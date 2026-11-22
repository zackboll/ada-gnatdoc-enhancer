#!/usr/bin/env python3
"""Rebuild retained release profiles with separate official, frozen and candidate engines."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess

from ada_gnatdoc_enhancer import __version__
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import require, sorted_json

from compare_release_017_018 import compare
import qualify_release_014_015 as profiles


FROZEN = '502bcae9c0194642394347ba7347c28c0af4b90a'
FROZEN_TREE = 'd950ad3b8413ad3a99975a308eaec06368303d0d'
OFFICIAL_WHEEL = '957c65797b03b5c6b3779e2a1918730a2e44749670e37535d2c8ff3e109f3ba4'
OFFICIAL_CHECK = f'''
import importlib.metadata as md, json
from ada_gnatdoc_enhancer import __file__ as module, __version__
from pathlib import Path
d = md.distribution('ada-gnatdoc-enhancer')
origin = json.loads(d.read_text('direct_url.json'))
if (__version__ != '0.1.7' or d.version != __version__ or
    Path(module).resolve() != Path(d.locate_file('ada_gnatdoc_enhancer/__init__.py')).resolve() or
    origin.get('archive_info', {{}}).get('hashes', {{}}).get('sha256') != {OFFICIAL_WHEEL!r}):
    raise ValueError('expected the installed independently acquired official v0.1.7 wheel')
'''


def check_frozen(path):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

    require(git('rev-parse', 'HEAD', 'HEAD^{tree}').splitlines() == [FROZEN, FROZEN_TREE],
            'wrong frozen merged-main authority')
    require(not git('status', '--porcelain', '--untracked-files=all'), 'dirty frozen merged main')


def run(repository, workspace, variant, frozen_source=None):
    if variant == 'baseline':
        exec(OFFICIAL_CHECK, {})
    elif variant == 'frozen':
        import ada_gnatdoc_enhancer as package
        require(frozen_source is not None, 'frozen source is required')
        check_frozen(frozen_source)
        require(__version__ == '0.1.7' and Path(package.__file__).resolve().is_relative_to(frozen_source/'src'),
                'not running the frozen merged-main implementation')
    else:
        require(__version__ == '0.1.8', 'wrong candidate version')
    # Reuse the retained profile definitions but not their historical comparator.
    profiles.compare = lambda old, new: compare(old, new, authority='official', schema=0)
    reports = profiles.run(repository, workspace, variant)
    for name, fixture, config_name, native, options in (
            ('mel-search', 'real-fixtures/search-mel', 'docs/gnatdoc-enhance.toml', 'pristine', {}),
            ('core-resize', 'real-fixtures/search-core', 'default.toml', 'pristine',
             dict(search=True, resizable_sidebar=True)),
            ('mel-source-blocks', 'source-block-fixtures/mel', 'docs/gnatdoc-authored-pilot.toml', 'native', {})):
        base = repository/'tests'/fixture
        folder = workspace/variant/name
        authority = folder/'authority'; site = folder/'site'
        shutil.copytree(base/'authority' if (base/'authority').is_dir() else base, authority)
        shutil.copytree(base/native, site)
        config = replace(load(authority, config_name), **options)
        require(not config.source_view, 'release profile unexpectedly enables source browsing')
        counts = enhance(config, site); verify(config, site)
        first = hashes(site); enhance(config, site)
        require(first == hashes(site), 'publication is not idempotent: '+name)
        reports[name] = dict(counts=counts, output_sha256=first)
    if variant == 'candidate':
        for name, result in reports.items():
            outputs = [n for n in ('site', 'enabled', 'none', 'symbol')
                       if (workspace/variant/name/n).is_dir()]
            result['comparison'] = {n: {
                authority: compare(workspace/other/name/n,
                                   workspace/variant/name/n, authority=authority, schema=0)
                for other, authority in (('baseline', 'official'), ('frozen', 'frozen'))} for n in outputs}
    (workspace/(variant+'.json')).write_text(sorted_json(reports))
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repository', 'workspace'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--variant', choices=('baseline', 'frozen', 'candidate'), required=True)
    parser.add_argument('--frozen-source', type=Path)
    args = parser.parse_args()
    run(args.repository.resolve(), args.workspace.resolve(), args.variant,
        args.frozen_source.resolve() if args.frozen_source else None)