#!/usr/bin/env python3
"""Fail-closed v0.1.3 to v0.1.4 feature-off publication comparison.

Search is allowed, but its inventory and bytes must be identical. No router,
label, CSS, guide, native page or checksum exception is permitted.
"""
import argparse
import json
from pathlib import Path


def compare(baseline, candidate):
    def files(root):
        if root.is_symlink() or not root.is_dir():
            raise ValueError('invalid publication root')
        result = {}
        for path in root.rglob('*'):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError('nonregular publication member')
            if path.is_file():
                result[path.relative_to(root).as_posix()] = path.read_bytes()
        return result

    old, new = files(baseline), files(candidate)
    if old.keys() != new.keys():
        raise ValueError('publication file inventory changed')
    manifest = 'api/presentation.json'
    if manifest not in old:
        raise ValueError('missing presentation manifest')
    a, b = json.loads(old[manifest]), json.loads(new[manifest])
    if a.get('enhancer_version') != '0.1.3' or b.get('enhancer_version') != '0.1.4':
        raise ValueError('unexpected baseline/candidate version')
    b['enhancer_version'] = a['enhancer_version']
    changed = sorted(name for name in old if old[name] != new[name])
    # Compare the actual serialized bytes as well as the decoded object. Even
    # whitespace/ordering changes outside the authorized version are rejected.
    expected = old[manifest].replace(b'"enhancer_version": "0.1.3"',
                                     b'"enhancer_version": "0.1.4"', 1)
    if a != b or changed != [manifest] or new[manifest] != expected:
        raise ValueError('unclassified publication difference: '+repr(changed))
    return dict(baseline='official-v0.1.3', candidate='preparation-v0.1.4',
                files=len(old), changed_files=changed,
                permitted_manifest_fields=['enhancer_version'],
                classification='version only', all_other_bytes_equal=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.candidate), indent=2))