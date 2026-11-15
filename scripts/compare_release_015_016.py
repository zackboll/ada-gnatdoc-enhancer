#!/usr/bin/env python3
"""Fail-closed official v0.1.5 → v0.1.6 publication comparison.

Unaffected profiles permit only the exact serialized release-version field.
Search changes require source/native reconstruction, not an output-side digest
or a caller-supplied declaration allowlist. Schema-3 has a separate portal oracle.
"""
import argparse
import html
import json
from pathlib import Path
import re

from ada_gnatdoc_enhancer.pipeline import verify
from ada_gnatdoc_enhancer.util import digest, sorted_json

MANIFEST = 'api/presentation.json'
INDEX = 'api/gnatdoc-search-index.json'
SHELL = 'api/index.html'
AUTHORITY = re.compile(r'<div id="documentation-search-authority" hidden data-schema="1" '
                       r'data-sha256="[0-9a-f]{64}" data-count="[0-9]+">.*?</div>')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def files(root):
    require(root.is_dir() and not root.is_symlink(), 'invalid publication root')
    result = {}
    for path in root.rglob('*'):
        require(not path.is_symlink() and (path.is_dir() or path.is_file()),
                'nonregular publication member')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def authority(records, payload):
    links = []
    for record in records:
        target = ' target="document-content"' if record['kind'] != 'guide' else ''
        links.append('<a href="' + html.escape(record['href'], quote=True) + '"' + target +
                     ' data-search-name="' + html.escape(record['name'], quote=True) +
                     '" data-search-kind="' + record['kind'] + '"></a>')
    return ('<div id="documentation-search-authority" hidden data-schema="1" data-sha256="' +
            digest(payload) + '" data-count="' + str(len(records)) + '">' + ''.join(links) + '</div>')


def compare(baseline, candidate, *, config=None):
    old, new = files(baseline), files(candidate)
    require(old.keys() == new.keys(), 'publication file inventory changed')
    require(MANIFEST in old, 'missing presentation manifest')
    a, b = json.loads(old[MANIFEST]), json.loads(new[MANIFEST])
    require(a.get('enhancer_version') == '0.1.5' and b.get('enhancer_version') == '0.1.6',
            'unexpected baseline/candidate version')
    require(old[MANIFEST].count(b'"enhancer_version": "0.1.5"') == 1,
            'missing/duplicate serialized release version')
    expected_manifest = old[MANIFEST].replace(b'"enhancer_version": "0.1.5"',
                                             b'"enhancer_version": "0.1.6"', 1)
    expected = dict(old, **{MANIFEST: expected_manifest})
    additions = []
    old_records = []
    if INDEX in old and old[INDEX] != new[INDEX]:
        require(config is not None and config.search,
                'search delta requires source/native reconstruction')
        # Reconstruct every candidate output from the supplied source/config and
        # the native snapshot embedded in the publication, authenticating native
        # signatures/anchors. This rejects forged records even after rehashing.
        verify(config, candidate)
        left, right = json.loads(old[INDEX]), json.loads(new[INDEX])
        require(left.keys() == right.keys() == {'schema_version', 'records'} and
                left['schema_version'] == right['schema_version'] == 1, 'index schema changed')
        old_records, records = left['records'], right['records']
        before = {r['href']: r for r in old_records}
        after = {r['href']: r for r in records}
        require(len(before) == len(old_records) and len(after) == len(records),
                'duplicate declaration destination')
        require(all(after.get(href) == record for href, record in before.items()),
                'existing record changed or removed')
        require([r for r in records if r['href'] in before] == old_records,
                'existing record order changed')
        additions = [r for r in records if r['href'] not in before]
        require(additions and all(r['kind'] in ('symbol', 'operation') for r in additions),
                'only newly eligible declarations may be added')
        require(records == sorted(records, key=lambda r: (r['name'].lower(), r['kind'])),
                'noncanonical record order')
        require(old[INDEX] == sorted_json(left).encode() and new[INDEX] == sorted_json(right).encode(),
                'index serialization changed')
        old_shell = old[SHELL].decode()
        matches = list(AUTHORITY.finditer(old_shell))
        require(len(matches) == 1 and matches[0][0] == authority(old_records, old[INDEX]),
                'baseline search shell authority differs')
        expected[SHELL] = (old_shell[:matches[0].start()] + authority(records, new[INDEX]) +
                           old_shell[matches[0].end():]).encode()
        expected[INDEX] = new[INDEX]
        for name in (INDEX, SHELL):
            require(a['output_sha256'].get(name) == digest(old[name]), 'baseline output hash differs')
            before_hash, after_hash = digest(old[name]), digest(expected[name])
            token = ('"' + name + '": "' + before_hash + '"').encode()
            require(expected_manifest.count(token) == 1, 'missing/duplicate manifest output hash')
            expected_manifest = expected_manifest.replace(
                token, ('"' + name + '": "' + after_hash + '"').encode(), 1)
        expected[MANIFEST] = expected_manifest
    changed = sorted(name for name in old if old[name] != new[name])
    require(new == expected, 'unclassified publication difference: ' + repr(changed))
    return dict(baseline='official-v0.1.5', candidate='preparation-v0.1.6', files=len(old),
                changed_files=changed, preserved_records=len(old_records),
                added_declarations=len(additions), added_records=additions,
                classification='source/native-supported search additions' if additions else 'version only',
                all_other_bytes_equal=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('baseline', 'candidate'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--config')
    args = parser.parse_args()
    config = None
    if args.source_root is not None:
        from ada_gnatdoc_enhancer.config import load
        config = load(args.source_root, args.config)
    print(json.dumps(compare(args.baseline, args.candidate, config=config), indent=2))