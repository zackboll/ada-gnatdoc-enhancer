#!/usr/bin/env python3
"""Reconstruct 008B sites from hash-bound 008A native inputs, never mutate inputs.

The reviewed 008A workspaces retain immutable consumer/dependency contracts and
native HTML. Verification uses the current independent publication verifier.
"""
import argparse
import json
import shutil
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.navigation import operation_entries
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, bind_pristine, identities, preserve_native
from ada_gnatdoc_enhancer.util import require, sorted_json


def run(previous, workspace, output):
    workspace.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for name in ('core', 'imgproc', 'geometry', 'mel', 'imgproc008'):
        old = previous/name/'first'
        manifest = json.loads((old/'_site/api/presentation.json').read_text())
        pristine = workspace/name/'pristine'
        (pristine/'api').mkdir(parents=True)
        for path, text in manifest['original_api_html'].items():
            require(Path(path).parent == Path('api'), 'unexpected original path')
            (pristine/path).write_text(text)
        shutil.copyfile(old/'_site/api/gnatdoc.css', pristine/'api/gnatdoc.css')
        if name != 'imgproc008':
            spec = json.loads((Path(__file__).resolve().parents[1]/
                               f'docs/evidence/gnatdoc002/{name}-input.json').read_text())
            require(hashes(pristine) == spec['pristine_sha256'], 'historical native input mismatch')
            revision = spec['revision']
        else:
            require(hashes(pristine) == hashes(previous/name/'pristine-first'), 'Imgproc native input mismatch')
            revision = '9ce22ae5ab70008e1147475a9e6d7baef82f1df0'
        old_hashes = hashes(old/'_site')
        for copy in ('first', 'second'):
            root = workspace/name/copy
            # A pre-created exploratory browser workspace must not be reused.
            shutil.copytree(old, root, ignore=shutil.ignore_patterns('_site'))
            shutil.copytree(pristine, root/'_site')
            config = load(root, 'qualification.toml')
            report = enhance(config, root/'_site')
            before = hashes(root/'_site')
            verified = verify(config, root/'_site')
            enhance(config, root/'_site')
            require(before == hashes(root/'_site'), 'not byte-idempotent')
            bind_pristine(pristine, root/'_site')
            preservation = preserve_native(identities(pristine), root/'_site', config=config, pristine=pristine)
        require(hashes(workspace/name/'first/_site') == hashes(workspace/name/'second/_site'), 'not deterministic')
        changed = sorted(p for p in old_hashes if old_hashes[p] != before.get(p))
        require(set(changed) == {'api/gnatdoc-navigation.js', 'api/presentation.json'}, 'unexpected publication changes')
        native = snapshot(config, pristine)
        navigation = operation_entries(config, native)
        if navigation:
            destinations = source_destinations(config, native)
            expected = {(f'{d.declaration.name} ({d.ordinal})' if d.total > 1 else d.declaration.name, d.href)
                        for group in destinations.values() for d in group}
            actual = [entry for *_, entries in navigation for entry in entries]
            require(len(actual) == len(expected) and set(actual) == expected, 'source/native navigation mismatch')
        records[name] = {'revision': revision, 'publication': report, 'verification': verified,
                         'native_preservation': preservation, 'changed_files': changed,
                         'deterministic': True, 'byte_idempotent': True, 'independent_reconstruction': True,
                         'navigation_entries': sum(len(items) for *_, items in navigation),
                         'incorrect_labels': 0, 'missing_destinations': 0, 'duplicate_destinations': 0}
        (output/'four-site-regression.json').write_text(sorted_json(records))
        print(name, 'PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.previous, args.workspace, args.output)