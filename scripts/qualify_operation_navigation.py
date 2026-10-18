#!/usr/bin/env python3
"""GNATDOC-008A offline requalification; never writes historical or consumer inputs.

Requires the original GNATDOC-002 acquisition, GNATDOC-007 historical workspace
and GNATDOC-008 exact-head workspace. No regeneration or weaker oracle is used.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from ada_gnatdoc_enhancer.authored import api_destinations
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.navigation import operation_entries
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, bind_pristine, preserve_native, identities
from ada_gnatdoc_enhancer.util import require, sorted_json

REPO = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--acquisition', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True,
                        help='GNATDOC-006 native-only workspaces (before authored configuration)')
    parser.add_argument('--baseline-source', type=Path, required=True,
                        help='Clean archive of f52dcfe; reconstruct baseline instead of trusting old mutable outputs')
    parser.add_argument('--imgproc-008', type=Path, required=True)
    parser.add_argument('--pristine-008', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.workspace.mkdir(parents=True, exist_ok=False)
    args.output.mkdir(parents=True, exist_ok=True)
    structural = {}
    for name in ('core', 'imgproc', 'geometry', 'mel'):
        subprocess.run([sys.executable, str(REPO/'scripts/qualify_authored.py'),
            '--name', name, '--sources', str(args.history/'exports'),
            '--acquisition', str(args.acquisition), '--previous', str(args.previous),
            '--workspace', str(args.workspace/name), '--reference', str(args.history/'reference'),
            '--output', str(args.workspace/'reports')], check=True)
        record = json.loads((args.workspace/f'reports/{name}-report.json').read_text())
        structural[name] = {k: record[k] for k in ('revision', 'publication', 'deterministic',
            'byte_idempotent', 'independent_reconstruction', 'native_preservation')}
        structural[name]['authored_guide_count'] = len(record['parity'])
        structural[name]['authored_byte_parity'] = all(e['byte_identical'] for e in record['parity'])
        new = args.workspace/name/'first/_site'
        baseline = args.workspace/'baseline'/name
        shutil.copytree(new.parent, baseline, ignore=shutil.ignore_patterns('_site'))
        shutil.copytree(args.acquisition/name/'pristine', baseline/'_site')
        environment = dict(os.environ, PYTHONPATH=str(args.baseline_source/'src'))
        subprocess.run([sys.executable, '-m', 'ada_gnatdoc_enhancer', 'enhance',
            '--source-root', str(baseline), '--config', 'qualification.toml', '--site', str(baseline/'_site')],
            cwd=args.baseline_source, env=environment, check=True, stdout=subprocess.DEVNULL)
        old = baseline/'_site'
        before, after = hashes(old), hashes(new)
        changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
        require(set(changed) <= {'api/index.html', 'api/presentation.json'}, 'unexplained historical output difference')
        structural[name]['changed_files'] = changed
    (args.output/'four-site.json').write_text(sorted_json(structural))

    workspace = args.workspace/'imgproc008'; workspace.mkdir()
    # Read-only oracle path: invoke the exact pinned consumer script unchanged.
    (workspace/'legacy').symlink_to(args.imgproc_008/'legacy', target_is_directory=True)
    reports = []
    original = args.imgproc_008/'first'
    config = load(original, 'qualification.toml')
    native = snapshot(config, args.pristine_008)
    api = api_destinations(config, native)
    proof = []
    for ds in source_destinations(config, native).values():
        for d in ds:
            identity = d.package.lower()+'.'+d.declaration.name.lower()+'/'+str(d.ordinal)
            require(api[identity] == '../api/'+d.href, 'authored/navigation identity mismatch')
            proof.append({'package': d.package, 'name': d.declaration.name,
                'source_line': d.declaration.line, 'source_profile': d.declaration.signature,
                'native_profile': d.section.code, 'ordinal': d.ordinal, 'overloads': d.total,
                'href': d.href, 'authored_identity': identity, 'authored_href': api[identity]})
    (args.output/'source-native-proof.json').write_text(sorted_json(proof))
    totals = Counter(p['name'] for p in proof if p['overloads'] > 1)
    (args.output/'overload-counts.json').write_text(sorted_json(dict(totals)))
    for copy in ('first', 'second'):
        root = workspace/copy
        shutil.copytree(original, root, ignore=shutil.ignore_patterns('_site'))
        shutil.copytree(args.pristine_008, root/'_site')
        c = load(root, 'qualification.toml')
        reports.append(enhance(c, root/'_site'))
        before = hashes(root/'_site'); verify(c, root/'_site'); enhance(c, root/'_site')
        require(before == hashes(root/'_site'), 'Imgproc not byte-idempotent')
        bind_pristine(args.pristine_008, root/'_site')
        preserve_native(identities(args.pristine_008), root/'_site')
    require(hashes(workspace/'first/_site') == hashes(workspace/'second/_site'), 'Imgproc not deterministic')
    script = args.imgproc_008/'source/scripts/compare_shared_gnatdoc_navigation.py'
    subprocess.run([sys.executable, str(script), '--workspace', str(workspace)], check=True)
    shutil.copyfile(workspace/'navigation-comparison.json', args.output/'navigation-after.json')
    # Use the existing independent native/link/guide comparison as well.
    sys.path.insert(0, str(script.parent))
    spec = importlib.util.spec_from_file_location('consumer_qualification', script.parent/'qualify_shared_gnatdoc_shadow.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    authored = json.loads((original/'docs/evidence/gnatdoc008/authored.json').read_text())
    comparison = module.compare(args.imgproc_008/'legacy/_site', workspace/'first/_site', args.pristine_008, authored)
    # Compare full authored identity maps with the historical qualified output.
    # The old output's guide bytes must not change; this independently covers
    # every guide link, not just anchor existence.
    old_hashes = hashes(original/'_site'); new_hashes = hashes(workspace/'first/_site')
    changed = sorted(p for p in old_hashes if old_hashes[p] != new_hashes.get(p))
    require(set(changed) <= {'api/index.html', 'api/presentation.json'}, 'unexplained GNATDOC-008 output difference')
    record = {'publication': reports[0], 'comparison': comparison, 'navigation_entries': len(proof),
              'incorrect_labels': 0, 'changed_files': changed, 'deterministic': True, 'byte_idempotent': True}
    (args.output/'imgproc008.json').write_text(sorted_json(record))
    # Original consumer ratchets, unchanged, against the newly produced site.
    for name, argv in (
        ('coverage', ['check_doc_coverage.py', '--fail-on-removed', 'docs/gnatdoc-coverage-baseline.txt', str(workspace/'first/_site')]),
        ('warnings', ['compare_gnatdoc_warnings.py', '--fail-on-removed', 'docs/gnatdoc-warning-baseline.txt', str(args.imgproc_008/'native-first.log')])):
        result = subprocess.run([sys.executable, str(script.parent/argv[0]), *argv[1:]],
                                cwd=args.imgproc_008/'source', text=True, capture_output=True)
        (args.output/(name+'.txt')).write_text(result.stdout+result.stderr)
        require(result.returncode == 0, name+' ratchet failed')
    print('GNATDOC-008A full historical and exact consumer qualification PASS')


if __name__ == '__main__': main()