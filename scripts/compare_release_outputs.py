#!/usr/bin/env python3
"""Classify complete v0.1.2 output against independently selected release inputs."""
import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_ROUTER = 'e32e0a9fcbccffbe94268ff933905e5616a52d4d89969c52e7d539acdb102522'
OFFICIAL_DEFAULT_ROUTER = 'b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd'


def compare(baseline, candidate, *, official=False, default_router=False):
    def files(root):
        result = {}
        for path in root.rglob('*'):
            if path.is_symlink():raise ValueError('symlink publication member')
            if path.is_file():result[path.relative_to(root).as_posix()] = path.read_bytes()
        return result

    old, new = files(baseline), files(candidate)
    if old.keys() != new.keys():raise ValueError('publication file inventory changed')
    changed = sorted(name for name in old if old[name] != new[name])
    manifest = 'api/presentation.json'
    router = 'api/gnatdoc-navigation.js'
    expected = [manifest]
    fields = ['enhancer_version']
    a, b = json.loads(old[manifest]), json.loads(new[manifest])
    if a['enhancer_version'] != '0.1.1' or b['enhancer_version'] != '0.1.2':
        raise ValueError('unexpected baseline/candidate version')
    b['enhancer_version'] = a['enhancer_version']
    if official and default_router:
        if hashlib.sha256(old[router]).hexdigest() != OFFICIAL_DEFAULT_ROUTER:
            raise ValueError('unapproved official default router')
        if hashlib.sha256(new[router]).hexdigest() != DEFAULT_ROUTER:
            raise ValueError('unapproved candidate default router')
        if a['output_sha256'][router] != hashlib.sha256(old[router]).hexdigest() or \
           b['output_sha256'][router] != DEFAULT_ROUTER:
            raise ValueError('router manifest hash mismatch')
        b['output_sha256'][router] = a['output_sha256'][router]
        expected.append(router)
        fields.append('output_sha256.api/gnatdoc-navigation.js')
    if changed != sorted(expected) or a != b:
        raise ValueError('unclassified publication difference: '+repr(changed))
    return dict(files=len(old), changed_files=changed, permitted_manifest_fields=fields,
                all_other_bytes_equal=True,
                baseline='official-v0.1.1' if official else 'merged-main-GNATDOC-019')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--official', action='store_true')
    parser.add_argument('--default-router', action='store_true')
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.candidate, official=args.official,
                             default_router=args.default_router), indent=2))