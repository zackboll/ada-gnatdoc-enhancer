#!/usr/bin/env python3
"""Audit release archives against source; compare content, not compressed bytes."""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile
import tomllib
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def wheel_files(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'duplicate wheel members')
        for member in archive.infolist():
            parts = PurePosixPath(member.filename).parts
            require(parts and not PurePosixPath(member.filename).is_absolute()
                    and '..' not in parts, 'unsafe wheel path')
            mode = member.external_attr >> 16
            kind = stat.S_IFMT(mode)
            # Some ZIP writers omit Unix file-type bits. When present, accept
            # only regular files/directories, never symlinks or device entries.
            require(kind in (0, stat.S_IFREG, stat.S_IFDIR), 'nonregular wheel member')
            require(kind != stat.S_IFDIR or member.is_dir(), 'invalid wheel directory')
        return {name: archive.read(name) for name in names if not name.endswith('/')}


def audit(source, wheel, sdist, rebuilt):
    source = source.resolve()
    project = tomllib.loads((source/'pyproject.toml').read_text())['project']
    require(project['version'] == '0.1.0', 'wrong source version')
    original = wheel_files(wheel)
    second = wheel_files(rebuilt)
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        require(len({m.name for m in members}) == len(members), 'duplicate sdist members')
        packaged = {}
        for member in members:
            parts = PurePosixPath(member.name).parts
            require(parts and parts[0] == 'ada_gnatdoc_enhancer-0.1.0'
                    and '..' not in parts, 'unsafe sdist path')
            require(member.isdir() or member.isfile(), 'nonregular sdist member')
            if member.isfile():
                packaged['/'.join(parts[1:])] = archive.extractfile(member).read()
    expected = {p.relative_to(source/'src').as_posix(): p.read_bytes()
                for p in (source/'src/ada_gnatdoc_enhancer').rglob('*')
                if p.is_file() and p.suffix in {'.py', '.css', '.js'}}
    for label, content in [('wheel', original), ('rebuilt wheel', second)]:
        actual = {n: data for n, data in content.items() if n.startswith('ada_gnatdoc_enhancer/')}
        require(actual == expected, label+' modules/assets differ from source')
        metadata_names = [n for n in content if n.endswith('.dist-info/METADATA')]
        require(len(metadata_names) == 1, 'missing/duplicate metadata')
        metadata = BytesParser().parsebytes(content[metadata_names[0]])
        require(metadata['Version'] == '0.1.0', 'metadata version mismatch')
        require(metadata['Requires-Python'] == '>=3.11', 'Python support changed')
        require(metadata['License-Expression'] == 'Apache-2.0', 'missing SPDX license')
        require(metadata.get_all('License-File') == ['LICENSE'], 'missing license declaration')
        dependencies = metadata.get_all('Requires-Dist', [])
        require(sorted(dependencies) == ['markdown-it-py==3.0.0; extra == "guides"',
                                         'mdurl==0.1.2; extra == "guides"'],
                'unexpected dependency: '+repr(dependencies))
        require(metadata.get_all('Provides-Extra') == ['guides'], 'unexpected extras')
        prefix = metadata_names[0].removesuffix('METADATA')
        require(content[prefix+'licenses/LICENSE'] == (source/'LICENSE').read_bytes(),
                'license file changed')
        require(b'gnatdoc-enhancer = ada_gnatdoc_enhancer.cli:main' in
                content[prefix+'entry_points.txt'], 'missing CLI entry point')
        for name, data in content.items():
            require(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts,
                    'unsafe wheel path')
            require('/__pycache__/' not in name and not name.endswith(('.pyc', '.pyo')),
                    'generated wheel member')
            if '.dist-info/' in name:
                # METADATA's README body contains intentional /tmp usage examples,
                # not build-machine metadata. Inspect its RFC headers separately.
                metadata_bytes = data.split(b'\n\n', 1)[0] if name.endswith('/METADATA') else data
                require(b'/home/' not in metadata_bytes and b'/tmp/' not in metadata_bytes
                        and b'file:///' not in metadata_bytes,
                        'absolute workstation path in metadata: '+name)
    for name, data in expected.items():
        require(packaged.get('src/'+name) == data, 'sdist module/asset mismatch: '+name)
    required = ['pyproject.toml', 'README.md', 'LICENSE', 'MANIFEST.in',
                'CHANGELOG.md', 'docs/evidence/gnatdoc003/provenance.json',
                'docs/evidence/gnatdoc004/provenance.json']
    for directory in ('tests', 'scripts', 'examples'):
        required.extend(p.relative_to(source).as_posix() for p in (source/directory).rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    for name in required:
        require(packaged.get(name) == (source/name).read_bytes(), 'missing/changed sdist input: '+name)
    allowed_evidence = {'docs/evidence/gnatdoc003/provenance.json',
                        'docs/evidence/gnatdoc004/provenance.json'}
    require({n for n in packaged if n.startswith('docs/evidence/')} == allowed_evidence,
            'historical evidence unnecessarily bundled')
    for name in packaged:
        parts = PurePosixPath(name).parts
        require(not {'build', 'dist', '.venv', '.git', '__pycache__'}.intersection(parts)
                and not name.endswith(('.pyc', '.pyo')), 'generated sdist member: '+name)
    require(packaged['PKG-INFO'] == original['ada_gnatdoc_enhancer-0.1.0.dist-info/METADATA'],
            'sdist/wheel metadata differ')
    return {'version': '0.1.0', 'module_asset_sha256': {n: sha(d) for n, d in sorted(expected.items())},
            'source_wheel_sdist_rebuilt_module_assets_equal': True,
            'required_sdist_inputs': len(required), 'sdist_files': len(packaged),
            'wheel_files': len(original), 'runtime_dependencies': [],
            'optional_guides_dependencies': dependencies,
            'archives': {label: {'name': p.name, 'bytes': p.stat().st_size,
                                 'sha256': sha(p.read_bytes())}
                         for label, p in [('wheel', wheel), ('sdist', sdist), ('rebuilt_wheel', rebuilt)]},
            'compression_byte_identity_required': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'wheel', 'sdist', 'rebuilt'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source, args.wheel, args.sdist, args.rebuilt), indent=2, sort_keys=True))