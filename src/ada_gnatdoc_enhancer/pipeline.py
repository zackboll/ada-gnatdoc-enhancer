"""Offline, deterministic, resumable GNATdoc 26 presentation pipeline.

Native HTML is captured before enhancement, so reruns reconstruct presentation
from the same observed original. Publication verification never treats an
output-side manifest as authority for Ada declarations or package identity.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from . import __version__
from .config import Config
from .errors import EnhancementError
from .guides import render as render_guides
from .inventory import packages
from .metadata import (check_native_input, guide_title, index_title, native_document,
                       package_title)
from .native_html import NativeSite, snapshot, verified_types
from .navigation import SCRIPT, enhance_index
from .syntax import transform_page
from .theme import METADATA, NATIVE_LINK, asset, themed, theme_asset, theme_identity
from .util import digest, require, site_root, sorted_json
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


def _head(config:Config,index:bool=False):
    """The approved head content of an enhanced API page, before document metadata."""
    return (NATIVE_LINK+(METADATA if config.theme else '')+
            (SCRIPT if index and config.navigation!='none' else ''))


def document_titles(config:Config,native:NativeSite):
    """Exact titles of generated pages, from verified package and guide identities."""
    titles={'api/'+p.path.name:package_title(p.package,config.project) for p in native.pages.values()}
    titles['api/index.html']=index_title(config.project)
    if config.guides=='markdown':
        from .guides import manifest
        titles.update({g['path']:guide_title(g['label'],config.project) for g in manifest(config)['guides']})
    return titles


def expected_output(config:Config,site:Path):
    """Produce expected published bytes without modifying the input site."""
    from .external_types import destinations
    config=replace(config,externals=destinations(config))
    native=snapshot(config,site)
    source=packages(config)
    from .adapters.mel import verify_renderer_exceptions
    exceptions=verify_renderer_exceptions(config,source,native)
    types=verified_types(native,source) if config.type_links else {}
    from .generic_instances import summaries
    instance_sections,instance_counts=summaries(config,source,native)
    from .instance_references import targets as reference_targets, metadata as reference_metadata
    references=reference_targets(config,source,native,instance_sections)
    values={}
    totals={'linked_types':0,'declaration_snippets':0,'public_packages':len(native.pages),
            'linked_local_types':0,'linked_external_types':0,
            'unrendered_renderer_exceptions':exceptions}
    totals.update(instance_counts)
    for name,page in native.pages.items():
        check_native_input(page.original,'api/'+page.path.name)
        require(source[name].name==page.package,
                f"native package heading differs from its Ada source name: {page.package}")
        text,counts=transform_page(page.original,source[name],source,native,types,config,references)
        for label,val in counts.items():
            totals['linked_types' if label=='links' else 'declaration_snippets']+=val
        from .syntax import TYPE_LINK
        import html
        external_count=sum(html.unescape(m[1]).startswith('https://') for m in TYPE_LINK.finditer(text))
        totals['linked_external_types']+=external_count
        totals['linked_local_types']+=counts['links']-external_count
        summary=instance_sections.get('api/'+page.path.name)
        if summary is not None:
            text=text.replace('<h2>Description</h2>',summary+'<h2>Description</h2>',1)
        path=page.path.relative_to(site).as_posix()
        values[path]=native_document(themed(text,config.theme),_head(config),
                                     package_title(page.package,config.project),path).encode()
    check_native_input(native.index,'api/index.html')
    index=themed(native.index,config.theme)
    index=enhance_index(native,index,config)
    if references:
        index=index.replace('<h2 id=compilation-units>',
                            reference_metadata(references)+'<h2 id=compilation-units>',1)
    values['api/index.html']=native_document(index,_head(config,True),index_title(config.project),
                                             'api/index.html').encode()
    if config.theme:values['api/gnatdoc-theme.css']=theme_asset(config)
    if config.navigation!='none':
        values['api/gnatdoc-navigation.js']=asset(
            'gnatdoc-instance-navigation.js' if config.instance_references else
            'gnatdoc-symbol-navigation.js' if config.symbol_bookmarks else 'gnatdoc-navigation.js')
    values.update(render_guides(config,native))
    return native,values,totals


def _expected_names(originals:dict,values:dict):
    return set(originals) | set(values) | {'api/gnatdoc.css', MANIFEST}


def _presentation(config:Config,site:Path,raw:dict,values:dict,counts:dict):
    source=packages(config)
    result = {'schema_version':1,'enhancer_version':__version__,
            'gnatdoc_version':config.gnatdoc,'project':config.project,
            'original_api_html':raw,
            'native_css_sha256':digest((site/'api/gnatdoc.css').read_bytes()),
            'source_sha256':canonical_fingerprints(source,config),
            'output_sha256':{path:digest(data) for path,data in sorted(values.items())},
            'counts':counts}
    identity = theme_identity(config)
    if identity is not None:
        result['theme_source'] = identity
    return result


def _generate(config:Config,site:Path):
    originals=_raw(site)
    native,values,counts=expected_output(config,site)
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
    return validate_files(site,config,_expected_names(originals,values),
                          titles=document_titles(config,native)),counts


def enhance(config:Config,site:Path,*,dry_run:bool=False):
    site=site_root(site)
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
    site=site_root(site)
    path=site/MANIFEST
    require(path.is_file() and not path.is_symlink(),'missing or symlink presentation manifest')
    data=json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(data,dict),'malformed presentation manifest: expected object')
    identity = theme_identity(config)
    require(set(data)=={'schema_version','enhancer_version','gnatdoc_version','project',
                        'original_api_html','native_css_sha256','source_sha256','output_sha256','counts'} |
                        ({'theme_source'} if identity is not None else set()),
            'unexpected presentation manifest fields')
    if identity is not None:
        require(data['theme_source'] == identity, 'custom theme source/configuration identity changed')
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
        native,values,counts=expected_output(config,raw)
        require(counts==data['counts'],'presentation counts mismatch')
        require({n:digest(d) for n,d in sorted(values.items())}==data['output_sha256'],
                'enhanced output does not match source/manifest')
        original_keys=set(originals)
        expected=_expected_names(originals,values)
        for name,content in values.items():
            target=site/name
            require(target.is_file() and not target.is_symlink() and target.read_bytes()==content,
                    f"published file differs from reconstructed output: {name}")
        result=validate_files(site,config,expected,titles=document_titles(config,native))
    return {'mode':'verified',**result,**counts}
