"""Offline, deterministic, resumable GNATdoc 26 presentation pipeline.

Native HTML is captured before enhancement, so reruns reconstruct presentation
from the same observed original. Publication verification never treats an
output-side manifest as authority for Ada declarations or package identity.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from . import __version__
from .config import Config
from .errors import EnhancementError
from .guides import render as render_guides
from .inventory import packages
from .native_html import NativeSite, snapshot, verified_types
from .navigation import enhance_index
from .syntax import transform_page
from .theme import asset, themed
from .util import digest, require, sorted_json
from .validation import validate_files

MANIFEST = 'api/presentation.json'


def canonical_fingerprints(source,config):
    return {p.path.relative_to(config.root).as_posix():digest(p.path.read_bytes())
            for p in source.values()}


def _raw(site:Path):
    api=site/'api';files={}
    for path in sorted(api.glob('*.html')):
        files[path.relative_to(site).as_posix()]=path.read_text(encoding='utf-8')
    require('api/index.html' in files,'missing native API index')
    return files


def expected_output(config:Config,site:Path):
    """Produce expected published bytes without modifying the input site."""
    native=snapshot(config,site)
    source=packages(config)
    from .adapters.mel import verify_renderer_exceptions
    exceptions=verify_renderer_exceptions(config,source,native)
    types=verified_types(native,source) if config.type_links else {}
    values={}
    totals={'linked_types':0,'declaration_snippets':0,'public_packages':len(native.pages),
            'unrendered_renderer_exceptions':exceptions}
    for name,page in native.pages.items():
        text,counts=transform_page(page.original,source[name],source,native,types,config)
        for label,val in counts.items():
            totals['linked_types' if label=='links' else 'declaration_snippets']+=val
        values[page.path.relative_to(site).as_posix()]=themed(text,config.theme).encode()
    index=themed(native.index,config.theme)
    index=enhance_index(native,index,config)
    values['api/index.html']=index.encode()
    if config.theme:values['api/gnatdoc-theme.css']=asset('gnatdoc-theme.css')
    if config.navigation!='none':values['api/gnatdoc-navigation.js']=asset('gnatdoc-navigation.js')
    values.update(render_guides(config,native))
    return native,values,totals


def _expected_names(originals:dict,values:dict):
    return set(originals) | set(values) | {'api/gnatdoc.css', MANIFEST}


def _presentation(config:Config,site:Path,raw:dict,values:dict,counts:dict):
    source=packages(config)
    return {'schema_version':1,'enhancer_version':__version__,
            'gnatdoc_version':config.gnatdoc,'project':config.project,
            'original_api_html':raw,
            'native_css_sha256':digest((site/'api/gnatdoc.css').read_bytes()),
            'source_sha256':canonical_fingerprints(source,config),
            'output_sha256':{path:digest(data) for path,data in sorted(values.items())},
            'counts':counts}


def _generate(config:Config,site:Path):
    originals=_raw(site)
    _,values,counts=expected_output(config,site)
    manifest=_presentation(config,site,originals,values,counts)
    values[MANIFEST]=sorted_json(manifest).encode()
    for name,content in values.items():
        target=site/name
        require(not target.is_symlink(), f"symlink enhancement destination: {name}")
        if target.exists():
            require(name in originals and target.is_file() and
                    target.read_text(encoding='utf-8') == originals[name],
                    f"unexpected existing enhancement destination: {name}")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    # Validate complete exact inventory, including every GNATdoc native page.
    return validate_files(site,config,_expected_names(originals,values)),counts


def enhance(config:Config,site:Path,*,dry_run:bool=False):
    site=site.resolve()
    require(site.is_dir() and not site.is_symlink(),'missing/symlink input site')
    if (site/MANIFEST).exists():return verify(config,site)
    # Work on a copy first: semantic/security validation errors cannot leave a
    # partially enhanced caller-owned output tree.
    with tempfile.TemporaryDirectory(prefix='gnatdoc-enhancer-') as temp:
        staging=Path(temp)/'site'
        shutil.copytree(site,staging,symlinks=True)
        stats,counts=_generate(config,staging)
        if not dry_run:
            # Original GNATdoc HTML may be replaced, but no native CSS bytes or
            # unknown file is removed. This doesn't delete caller directories.
            for path in sorted(staging.rglob('*')):
                if path.is_dir():continue
                rel=path.relative_to(staging)
                target=site/rel
                if not target.exists() or target.read_bytes()!=path.read_bytes():
                    target.parent.mkdir(parents=True,exist_ok=True)
                    require(not target.is_symlink(),f"symlink publication destination: {target}")
                    target.write_bytes(path.read_bytes())
    return {'mode':'dry-run' if dry_run else 'enhanced',**stats,**counts}


def verify(config:Config,site:Path):
    site=site.resolve()
    require(site.is_dir() and not site.is_symlink(),'invalid site root')
    path=site/MANIFEST
    require(path.is_file() and not path.is_symlink(),'missing or symlink presentation manifest')
    data=json.loads(path.read_text(encoding='utf-8'))
    require(set(data)=={'schema_version','enhancer_version','gnatdoc_version','project',
                        'original_api_html','native_css_sha256','source_sha256','output_sha256','counts'},
            'unexpected presentation manifest fields')
    require(data['schema_version']==1 and data['gnatdoc_version']==config.gnatdoc
            and data['project']==config.project and data['enhancer_version']==__version__,
            'presentation schema/tool/project mismatch')
    require(data['source_sha256']==canonical_fingerprints(packages(config),config),
            'source differs from qualified presentation manifest')
    require(digest((site/'api/gnatdoc.css').read_bytes())==data['native_css_sha256'],
            'native GNATdoc stylesheet has changed')
    originals=data['original_api_html']
    require(isinstance(originals,dict),'malformed original HTML manifest')
    with tempfile.TemporaryDirectory(prefix='gnatdoc-verify-') as temp:
        raw=Path(temp)/'site';(raw/'api').mkdir(parents=True)
        (raw/'api/gnatdoc.css').write_bytes((site/'api/gnatdoc.css').read_bytes())
        for name,value in originals.items():
            require(isinstance(name,str) and name.startswith('api/') and isinstance(value,str),
                    'unsupported original HTML payload')
            from .util import inside
            p=inside(raw,name)
            require(not p.exists(),"duplicate native source path")
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(value,encoding='utf-8')
        _,values,counts=expected_output(config,raw)
        require(counts==data['counts'],'presentation counts mismatch')
        require({n:digest(d) for n,d in sorted(values.items())}==data['output_sha256'],
                'enhanced output does not match source/manifest')
        original_keys=set(originals)
        expected=_expected_names(originals,values)
        for name,content in values.items():
            target=site/name
            require(target.is_file() and not target.is_symlink() and target.read_bytes()==content,
                    f"published file differs from reconstructed output: {name}")
        result=validate_files(site,config,expected)
    return {'mode':'verified',**result,**counts}
