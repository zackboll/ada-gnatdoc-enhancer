#!/usr/bin/env python3
"""Compare complete publications against official v0.1.7 or frozen merged main."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from compare_release_016_017 import files, require


MANIFEST = 'api/presentation.json'
CSS = 'api/gnatdoc-source.css'
OLD = b'"enhancer_version": "0.1.7"'
NEW = b'"enhancer_version": "0.1.8"'
STYLESHEETS = (
    '5b1716ddec6cb9afc3576a1628ba5e14002700575542c9afbe831d99a25a8260',
    '2e4eb69bd23e1ea97e3877383dc7e75d701429006c25581a0e16a75041823fdc',
)
TOKENS = re.compile(rb'<span class="ada-(?:keyword|comment|string|character|number|attribute|operator)">([^<]*)</span>')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest(data, version):
    def unique(pairs):
        result = dict(pairs)
        require(len(result) == len(pairs), 'duplicate presentation manifest field')
        return result

    value = json.loads(data, object_pairs_hook=unique)
    require(isinstance(value, dict) and value.get('enhancer_version') == version,
            'unexpected baseline/candidate version')
    return value


def replace_once(raw, old, new):
    require(raw.count(old) == 1, 'missing/duplicate serialized manifest identity')
    return raw.replace(old, new, 1)


def compare(baseline, candidate, *, authority, schema, highlighted=True):
    """Inputs must first be independently reconstructed and verified by each engine.

    The official schema-1 exception admits only exact de-highlighting, the pinned
    PR #37 source stylesheet, and their corresponding real byte hashes. Frozen
    main never takes this exception, even for source pages and their hashes.
    """
    require(authority in ('official', 'frozen') and schema in (0, 1, 2),
            'unknown compatibility authority or schema')
    require(authority != 'official' or schema != 2, 'official v0.1.7 does not support schema 2')
    old, new = files(baseline), files(candidate)
    require(old.keys() == new.keys(), 'publication file inventory changed')
    require(MANIFEST in old, 'missing presentation manifest')
    a, b = manifest(old[MANIFEST], '0.1.7'), manifest(new[MANIFEST], '0.1.8')
    for data in (a, b):
        source = data.get('source_view', {})
        require(source.get('schema_version', 0) == schema and (schema or not source),
                'unexpected source-view schema')
    expected = dict(old)
    raw = replace_once(old[MANIFEST], OLD, NEW)
    classified = []
    if authority == 'official' and schema == 1:
        pages = [entry['page'] for entry in a['source_view']['files']]
        require(len(pages) == len(set(pages)) and set(pages) ==
                {name for name in old if name.startswith('api/source/')},
                'incomplete specification page inventory')
        require(CSS in old and (sha(old[CSS]), sha(new[CSS])) == STYLESHEETS,
                'unclassified source stylesheet identity')
        for name in [CSS, *pages]:
            require(a['output_sha256'].get(name) == sha(old[name]) and
                    b['output_sha256'].get(name) == sha(new[name]), 'source output hash differs: '+name)
            if name != CSS:
                require(old[name] == (TOKENS.sub(rb'\1', new[name]) if highlighted else new[name]),
                        'source page changed beyond token spans: '+name)
            if old[name] != new[name]:
                # Replace only the exact serialized entry, retaining ordering,
                # indentation, and every byte outside this classified change.
                entry = json.dumps(name).encode() + b': "'
                raw = replace_once(raw, entry + sha(old[name]).encode() + b'"',
                                   entry + sha(new[name]).encode() + b'"')
                expected[name] = new[name]
                classified.append(name)
    expected[MANIFEST] = raw
    differences = sorted(name for name in old if new[name] != expected[name])
    require(not differences, 'unclassified publication difference: '+repr(differences))
    return dict(authority=authority, schema=schema, files=len(old),
                changed_files=sorted([MANIFEST, *classified]),
                classification='version and source highlighting' if classified else 'version only',
                all_other_bytes_equal=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('baseline', 'candidate'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--authority', choices=('official', 'frozen'), required=True)
    parser.add_argument('--schema', type=int, choices=(0, 1, 2), required=True)
    parser.add_argument('--plain', dest='highlighted', action='store_false')
    print(json.dumps(compare(**vars(parser.parse_args())), indent=2))