#!/usr/bin/env python3
"""Smoke-test an installed wheel outside the checkout, with explicit fixture input."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib.resources import files
from importlib.metadata import version
from pathlib import Path

import ada_gnatdoc_enhancer


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


def run(fixtures:Path):
    installed=Path(ada_gnatdoc_enhancer.__file__).resolve()
    require(installed.is_relative_to(Path(sys.prefix).resolve()),
            f'expected a wheel installed in this virtual environment, got {installed}')
    cli=Path(sys.executable).parent/'gnatdoc-enhancer'
    environment=os.environ.copy();environment.pop('PYTHONPATH',None)
    fixtures=fixtures.resolve()
    with tempfile.TemporaryDirectory(prefix='gnatdoc-installed-') as temp:
        cwd=Path(temp)

        def invoke(*args):
            result=subprocess.run([str(cli),*map(str,args)],cwd=cwd,env=environment,
                                  text=True,capture_output=True)
            require(result.returncode==0,f'{args}: {result.stderr}')
            return result.stdout

        require('enhance' in invoke('--help'),'missing CLI help')
        require(version('ada-gnatdoc-enhancer') == ada_gnatdoc_enhancer.__version__ == '0.1.3',
                'installed distribution/module version mismatch')
        require(invoke('--version').strip() == '0.1.3',
                'installed CLI version mismatch')
        conformance=json.loads(invoke('conformance','--fixtures',fixtures))
        require(set(conformance['profiles'])=={'core','imgproc','geometry','mel'},
                'incomplete installed conformance')
        root=cwd/'fixture';shutil.copytree(fixtures/'mel',root)
        alias=cwd/'alias';alias.symlink_to(root,target_is_directory=True)
        pristine=hashes(root)
        rejected=subprocess.run([str(cli),'enhance','--source-root',str(alias),
                                 '--config','project.toml','--site','_site'],
                                cwd=cwd,env=environment,text=True,capture_output=True)
        require(rejected.returncode==2 and 'symlink site path' in rejected.stderr
                and 'Traceback' not in rejected.stderr and not rejected.stdout,
                f'installed CLI failed to reject aliased site: {rejected.stderr}')
        require(pristine==hashes(root),'rejected installed invocation modified fixture')
        before={p:h for p,h in hashes(root).items() if not p.startswith('_site/')}
        arguments=('--source-root',root,'--config','project.toml','--site','_site')
        result=json.loads(invoke('enhance',*arguments))
        require(result['public_packages']==29,'wrong installed package inventory')
        output=root/'_site'
        require(json.loads((output/'api/presentation.json').read_text())['enhancer_version'] == '0.1.3',
                'installed presentation manifest version mismatch')
        for destination in ('api/gnatdoc-theme.css','api/gnatdoc-navigation.js',
                            'assets/gnatdoc-guides.css'):
            bundled=files('ada_gnatdoc_enhancer').joinpath('assets',Path(destination).name)
            require((output/destination).read_bytes()==bundled.read_bytes(),
                    f'missing or changed bundled asset: {destination}')
        index=(output/'api/index.html').read_text(encoding='utf-8')
        require('id="package-search"' in index,'missing search controls')
        package_pages=[p.read_text(encoding='utf-8') for p in output.glob('api/[0-9a-f]*.html')]
        require(any('class="ada-keyword"' in p for p in package_pages),'no Ada highlighting')
        require(any('class="type-reference"' in p for p in package_pages),'no type links')
        first=hashes(output)
        invoke('enhance',*arguments)
        require(first==hashes(output),'installed enhancement is not byte-idempotent')
        verified=json.loads(invoke('verify',*arguments))
        require(verified['html_pages']==37,'wrong installed HTML inventory')
        require(before=={p:h for p,h in hashes(root).items() if not p.startswith('_site/')},
                'installed enhancement changed files outside the output directory')
    return {'installed_module':str(installed),'version':version('ada-gnatdoc-enhancer'),
            'help':'passed','assets':3,
            'symlink_source_root_rejection':'passed',
            'enhancement':'passed','idempotence':'passed','verification':verified,
            'conformance':conformance}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures',required=True,type=Path)
    print(json.dumps(run(parser.parse_args().fixtures),sort_keys=True,indent=2))