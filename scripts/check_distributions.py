#!/usr/bin/env python3
"""Audit release archives against source; compare content, not compressed bytes."""
from __future__ import annotations

import argparse
import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile
import tomllib
import zipfile

VERSION = '0.1.8'
STEM = 'ada_gnatdoc_enhancer-' + VERSION


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_parts(name, kind):
    parts = name.removesuffix('/').split('/')
    require(all(p and p not in ('.', '..') and '\\' not in p and ':' not in p and
                all(ord(c) >= 32 and ord(c) != 127 for c in p) for p in parts),
            'unsafe '+kind+' path')
    return parts


def wheel_files(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len({n.removesuffix('/') for n in names}), 'duplicate wheel members')
        for member in archive.infolist():
            archive_parts(member.orig_filename, 'wheel')
            mode = member.external_attr >> 16
            kind = stat.S_IFMT(mode)
            # Some ZIP writers omit Unix file-type bits. When present, accept
            # only regular files/directories, never symlinks or device entries.
            require(kind in (0, stat.S_IFREG, stat.S_IFDIR), 'nonregular wheel member')
            require(kind != stat.S_IFDIR or member.is_dir(), 'invalid wheel directory')
        return {name: archive.read(name) for name in names if not name.endswith('/')}


def sdist_files(path):
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        require(len({m.name.removesuffix('/') for m in members}) == len(members), 'duplicate sdist members')
        regular = {m.name for m in members if m.isfile()}
        packaged = {}
        for member in members:
            parts = archive_parts(member.name, 'sdist')
            require(parts[0] == STEM and (member.isdir() or len(parts) > 1), 'unsafe sdist path')
            require(not any('/'.join(parts[:i]) in regular for i in range(1, len(parts))),
                    'sdist file used as directory')
            require(member.isdir() or member.isfile(), 'nonregular sdist member')
            if member.isfile():
                packaged['/'.join(parts[1:])] = archive.extractfile(member).read()
        return packaged


def extract_sdist(path, destination):
    # Extract only validated regular files into a new directory. Do not restore
    # archive ownership, permissions, links or platform-specific metadata.
    packaged = sdist_files(path)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in packaged.items():
        target = destination/STEM/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def verify_record(content, prefix):
    record = prefix+'RECORD'
    rows = list(csv.reader(io.StringIO(content[record].decode('utf-8'))))
    require(all(len(row) == 3 for row in rows), 'malformed wheel RECORD')
    require(len(rows) == len({row[0] for row in rows}), 'duplicate wheel RECORD entries')
    require({row[0] for row in rows} == set(content), 'incomplete wheel RECORD')
    for name, digest, size in rows:
        if name == record:
            require(digest == size == '', 'wheel RECORD must not hash itself')
            continue
        expected = base64.urlsafe_b64encode(hashlib.sha256(content[name]).digest()).rstrip(b'=').decode()
        require(digest == 'sha256='+expected and size == str(len(content[name])),
                'wheel RECORD hash/size mismatch: '+name)


def audit(source, wheel, sdist, rebuilt):
    source = source.resolve()
    project = tomllib.loads((source/'pyproject.toml').read_text())['project']
    require(project['version'] == VERSION, 'wrong source version')
    require(wheel.name == rebuilt.name == STEM+'-py3-none-any.whl',
            'wrong wheel filename')
    require(sdist.name == STEM+'.tar.gz', 'wrong sdist filename')
    original = wheel_files(wheel)
    second = wheel_files(rebuilt)
    packaged = sdist_files(sdist)
    expected = {p.relative_to(source/'src').as_posix(): p.read_bytes()
                for p in (source/'src/ada_gnatdoc_enhancer').rglob('*')
                if p.is_file() and p.suffix in {'.py', '.css', '.js'}}
    for label, content in [('wheel', original), ('rebuilt wheel', second)]:
        actual = {n: data for n, data in content.items() if n.startswith('ada_gnatdoc_enhancer/')}
        require(actual == expected, label+' modules/assets differ from source')
        metadata_names = [n for n in content if n.endswith('.dist-info/METADATA')]
        require(len(metadata_names) == 1, 'missing/duplicate metadata')
        metadata = BytesParser().parsebytes(content[metadata_names[0]])
        require(metadata['Name'] == 'ada-gnatdoc-enhancer', 'metadata name mismatch')
        require(metadata.get_all('Version') == [VERSION], 'metadata version mismatch')
        require(metadata['Requires-Python'] == '>=3.11', 'Python support changed')
        require(metadata['License-Expression'] == 'Apache-2.0', 'missing SPDX license')
        require(metadata.get_all('License-File') == ['LICENSE'], 'missing license declaration')
        dependencies = metadata.get_all('Requires-Dist', [])
        require(sorted(dependencies) == ['markdown-it-py==3.0.0; extra == "guides"',
                                         'mdurl==0.1.2; extra == "guides"'],
                'unexpected dependency: '+repr(dependencies))
        require(metadata.get_all('Provides-Extra') == ['guides'], 'unexpected extras')
        prefix = metadata_names[0].removesuffix('METADATA')
        require(prefix == STEM+'.dist-info/', 'wrong dist-info identity')
        require(set(content) == set(expected) | {prefix+n for n in (
            'METADATA', 'WHEEL', 'RECORD', 'entry_points.txt', 'top_level.txt', 'licenses/LICENSE')},
            'unexpected/missing wheel members')
        verify_record(content, prefix)
        require(b'Tag: py3-none-any\n' in content[prefix+'WHEEL']
                and b'Root-Is-Purelib: true\n' in content[prefix+'WHEEL'], 'wrong wheel compatibility')
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
                'CHANGELOG.md', 'CONTRIBUTING.md', 'Makefile', '.gitattributes', '.gitignore',
                'docs/evidence/gnatdoc003/provenance.json',
                'docs/evidence/gnatdoc004/provenance.json']
    for directory in ('tests', 'scripts', 'examples'):
        required.extend(p.relative_to(source).as_posix() for p in (source/directory).rglob('*')
                        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    required.extend(p.relative_to(source).as_posix() for p in (source/'docs').rglob('*.md')
                    if 'evidence' not in p.relative_to(source/'docs').parts)
    required.extend(p.relative_to(source).as_posix() for p in (source/'.github/workflows').glob('*.yml'))
    for name in required:
        require(packaged.get(name) == (source/name).read_bytes(), 'missing/changed sdist input: '+name)
    allowed_evidence = {'docs/evidence/gnatdoc003/provenance.json',
                        'docs/evidence/gnatdoc004/provenance.json'}
    require({n for n in packaged if n.startswith('docs/evidence/')} == allowed_evidence,
            'historical evidence unnecessarily bundled')
    generated = {'PKG-INFO', 'setup.cfg'} | {'src/ada_gnatdoc_enhancer.egg-info/'+n for n in (
        'PKG-INFO', 'SOURCES.txt', 'dependency_links.txt', 'entry_points.txt', 'requires.txt', 'top_level.txt')}
    require(set(packaged) == set(required) | {'src/'+n for n in expected} | generated,
            'unexpected/missing sdist members')
    for name in packaged:
        parts = PurePosixPath(name).parts
        require(not {'build', 'dist', '.venv', '.git', '__pycache__'}.intersection(parts)
                and not name.endswith(('.pyc', '.pyo')), 'generated sdist member: '+name)
    require(packaged['PKG-INFO'] == original[STEM+'.dist-info/METADATA'],
            'sdist/wheel metadata differ')
    require(packaged['src/ada_gnatdoc_enhancer.egg-info/PKG-INFO'] == packaged['PKG-INFO'],
            'sdist egg-info metadata differ')
    require(original == second, 'canonical and independently rebuilt wheel contents differ')
    return {'version': VERSION, 'module_asset_sha256': {n: sha(d) for n, d in sorted(expected.items())},
             'wheel_and_rebuilt_decompressed_contents_equal': True,
            'wheel_record_hashes_and_sizes_verified': True,
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
    parser.add_argument('--sdist', type=Path, required=True)
    for key in ('source', 'wheel', 'rebuilt', 'extract-to'):
        parser.add_argument('--'+key, type=Path)
    args = parser.parse_args()
    if args.extract_to:
        extract_sdist(args.sdist, args.extract_to)
    elif all((args.source, args.wheel, args.rebuilt)):
        print(json.dumps(audit(args.source, args.wheel, args.sdist, args.rebuilt), indent=2, sort_keys=True))
    else:
        parser.error('supply --extract-to or --source, --wheel and --rebuilt')