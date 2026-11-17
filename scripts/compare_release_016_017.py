#!/usr/bin/env python3
"""Fail-closed official v0.1.6 → v0.1.7 source-view-disabled byte comparison."""
import argparse
import json
from pathlib import Path


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


def compare(baseline, candidate, *, config=None):
    old, new = files(baseline), files(candidate)
    require(old.keys() == new.keys(), 'publication file inventory changed')
    manifest = 'api/presentation.json'
    require(manifest in old, 'missing presentation manifest')
    a, b = json.loads(old[manifest]), json.loads(new[manifest])
    require(a.get('enhancer_version') == '0.1.6' and b.get('enhancer_version') == '0.1.7',
            'unexpected baseline/candidate version')
    token = b'"enhancer_version": "0.1.6"'
    require(old[manifest].count(token) == 1, 'missing/duplicate serialized release version')
    expected = dict(old)
    expected[manifest] = old[manifest].replace(token, b'"enhancer_version": "0.1.7"', 1)
    changed = sorted(name for name in old if old[name] != new[name])
    require(new == expected, 'unclassified publication difference: '+repr(changed))
    return dict(baseline='official-v0.1.6', candidate='preparation-v0.1.7', files=len(old),
                changed_files=changed, permitted_manifest_fields=['enhancer_version'],
                classification='version only', all_other_bytes_equal=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.candidate), indent=2))