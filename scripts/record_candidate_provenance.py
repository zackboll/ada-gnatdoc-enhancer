#!/usr/bin/env python3
"""Bind independently authorized Git source to audited candidate archives.

Expected commit/tree are supplied by the release review or hosted event, never
read from the candidate archives. Output is a qualification artifact, not release
authorization. This file intentionally does not claim its own digest or commit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile

from check_distributions import audit, require


def record(args):
    def git(*words):
        return subprocess.check_output(['git', '-C', str(args.repository), *words])

    commit = args.expected_source_commit
    tree = args.expected_source_tree
    require(git('rev-parse', commit+'^{commit}').decode().strip() == commit,
            'source commit must be an exact independently authorized SHA')
    require(git('rev-parse', commit+'^{tree}').decode().strip() == tree,
            'authorized commit/tree mismatch')
    source = args.source.resolve()
    inventory = {}
    for entry in git('ls-tree', '-rz', commit).split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, kind, blob = header.decode().split()
        require(mode in ('100644', '100755') and kind == 'blob', 'nonregular source member')
        name = name.decode()
        expected = git('cat-file', 'blob', blob)
        require(not (source/name).is_symlink() and (source/name).read_bytes() == expected,
                'source bytes differ from authorized tree: '+name)
        inventory[name] = dict(git_blob=blob, sha256=hashlib.sha256(expected).hexdigest(),
                               bytes=len(expected))
    content = audit(source, args.wheel, args.sdist, args.rebuilt)
    archives = {}
    for label, path in [('wheel', args.wheel), ('sdist', args.sdist), ('rebuilt_wheel', args.rebuilt)]:
        if path.suffix == '.whl':
            with zipfile.ZipFile(path) as archive:
                members = {n: archive.read(n) for n in archive.namelist() if not n.endswith('/')}
        else:
            with tarfile.open(path) as archive:
                members = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
        archives[label] = dict(content['archives'][label], members={
            n: dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            for n, data in sorted(members.items())})
    return dict(schema_version=1, release_version='0.1.4', publication_authorized=False,
                expected_source_commit=commit, expected_source_tree=tree,
                source_files=inventory, archives=archives, distribution_content_audit=content,
                authorization='Expected source commit/tree supplied independently of archives',
                compression_byte_identity_required=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repository', 'source', 'wheel', 'sdist', 'rebuilt'):
        parser.add_argument('--'+key, type=Path, required=True)
    for key in ('expected-source-commit', 'expected-source-tree'):
        parser.add_argument('--'+key, required=True)
    print(json.dumps(record(parser.parse_args()), indent=2, sort_keys=True))