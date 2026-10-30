#!/usr/bin/env python3
"""Fail-closed v0.1.2 to v0.1.3 comparison without search opt-in.

Only the version and the exact legacy filter label (with its manifest hash)
may change. Search-enabled output requires separate source/native qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path


OLD_LABEL = b'<label for="package-search">Search documentation</label>'
NEW_LABEL = b'<label for="package-search">Filter navigation links</label>'


def compare(baseline, candidate, *, official=False, default_router=False):
    def files(root):
        result = {}
        for path in root.rglob('*'):
            if path.is_symlink():raise ValueError('symlink publication member')
            if path.is_file():result[path.relative_to(root).as_posix()] = path.read_bytes()
        return result

    old, new = files(baseline), files(candidate)
    if old.keys() != new.keys():raise ValueError('publication file inventory changed')
    if {'api/gnatdoc-search-index.json', 'api/gnatdoc-search.css'}.intersection(new):
        raise ValueError('search opt-in requires separate qualification')
    changed = sorted(name for name in old if old[name] != new[name])
    manifest = 'api/presentation.json'
    index = 'api/index.html'
    expected = [manifest]
    fields = ['enhancer_version']
    a, b = json.loads(old[manifest]), json.loads(new[manifest])
    if a['enhancer_version'] != '0.1.2' or b['enhancer_version'] != '0.1.3':
        raise ValueError('unexpected baseline/candidate version')
    b['enhancer_version'] = a['enhancer_version']
    hash_changes = {}
    if OLD_LABEL in old.get(index, b''):
        if old[index].count(OLD_LABEL) != 1 or new[index] != old[index].replace(OLD_LABEL, NEW_LABEL):
            raise ValueError('unclassified navigation-filter label difference')
        hashes = [hashlib.sha256(content[index]).hexdigest() for content in (old, new)]
        if [data['output_sha256'].get(index) for data in (a, b)] != hashes:
            raise ValueError('navigation-filter manifest hash mismatch')
        b['output_sha256'][index] = a['output_sha256'][index]
        hash_changes[index] = dict(zip(('baseline', 'candidate'), hashes))
        expected.append(index)
        fields.append('output_sha256.api/index.html')
    if changed != sorted(expected) or a != b:
        raise ValueError('unclassified publication difference: '+repr(changed))
    return dict(files=len(old), changed_files=changed, permitted_manifest_fields=fields,
                changed_output_hashes=hash_changes,
                classification='version and intentional navigation-filter label' if hash_changes else 'version only',
                all_other_bytes_equal=True,
                baseline='official-v0.1.2' if official else 'independently-generated-v0.1.2')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--official', action='store_true')
    parser.add_argument('--default-router', action='store_true')
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.candidate, official=args.official,
                             default_router=args.default_router), indent=2))