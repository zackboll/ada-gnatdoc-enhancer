"""Reconstruct pinned external destinations; manifests are claims, not authority.

The reviewed acquisition and manifest hashes belong to consumer configuration.
Every use rechecks original source/native bytes and regenerates the inventory.
This module performs no implicit network access or Ada name-only inference.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from .util import QNAME, digest, inside, regular, require


def _pairs(items):
    result={}
    for key,value in items:
        require(key.lower() not in {k.lower() for k in result},
                'duplicate case-insensitive manifest key')
        result[key]=value
    return result


def read_json(path):
    try:
        data=json.loads(regular(path).read_text(encoding='utf-8'),object_pairs_hook=_pairs)
    except (UnicodeError,ValueError) as exc:
        from .errors import EnhancementError
        raise EnhancementError(f'malformed external evidence: {exc}') from exc
    require(isinstance(data,dict),'external evidence must be an object')
    return data


def inventory(spec, source, pristine):
    """Export only ordinary source-owned public type/subtype declarations.

    The whole site is reconciled first. Flat package ownership is required;
    instances and nested/generic scopes cannot introduce exported members.
    """
    from .config import load
    from .inventory import HEADER, mask_ada, packages, visible_prefix
    from .native_html import snapshot, verified_types
    from .profiles import reconcile
    from .qualification import check_snapshot, hashes, identities
    require(spec.get('schema_version')==1,'unsupported acquisition schema')
    require(isinstance(spec.get('revision'),str) and
            re.fullmatch('[a-f0-9]{40}',spec['revision']),'invalid dependency revision')
    require(spec.get('gnatdoc')=='GNATdoc 26.0.0 (20260415)','unqualified dependency GNATdoc')
    require(isinstance(spec.get('repository'),str) and
            re.fullmatch(r'https://github.com/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+',spec['repository']),
            'invalid dependency repository')
    check_snapshot(source,spec['source_sha256'])
    require(hashes(pristine)==spec['pristine_sha256'],'dependency native artifact changed')
    public=spec['public_sources']
    require(isinstance(public,list) and public and len(public)==len(set(public)),
            'invalid dependency public source list')
    with tempfile.TemporaryDirectory(prefix='gde-external-inventory-') as temp:
        root=Path(temp)
        for name in public:
            require(name in spec['source_sha256'],'unpinned public dependency source')
            target=inside(root/'qualification-public',name)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(regular(inside(source,name)),target)
        # Acquisition configuration may not import other manifests or grant URL
        # permissions. It only defines this dependency's public source profile.
        import tomllib
        raw=tomllib.loads(spec['configuration'])
        require(not raw.get('external_dependencies') and not raw.get('external_types'),
                'dependency acquisition cannot import type owners')
        require(raw.get('sources',{}).get('directories')==['qualification-public'] and
                raw.get('navigation',{}).get('mode','packages')=='packages' and
                not raw.get('guides') and not raw.get('security') and
                not raw.get('renderer_exceptions'),
                'unsupported dependency source profile')
        (root/'inventory.toml').write_text(spec['configuration'],encoding='utf-8')
        # Operation categories are consumer concerns, not type identity evidence.
        if raw.get('navigation',{}).get('categories'):
            raise ValueError('unsupported dependency navigation profile')
        config=load(root,'inventory.toml')
        pkgs=packages(config);native=snapshot(config,pristine)
        targets=verified_types(native,pkgs);independent=identities(pristine)
        types={};unsupported=[]
        for key,pkg in sorted(pkgs.items()):
            masked=mask_ada(pkg.source);header=HEADER.search(masked)
            flat=(header is not None and header[3].lower()=='is' and
                  not re.search(r'\bgeneric\b',masked[:header.start()],re.I) and
                  not re.search(r'\b(package|generic|task|protected|begin|declare)\b',
                                mask_ada(visible_prefix(pkg.source,header.end())),re.I))
            for name,decl in sorted(pkg.public_types.items()):
                identity=key+'.'+name
                if not flat:
                    unsupported.append(identity);continue
                page,anchor=targets[identity]
                sections=[s for s in native.pages[key].sections if s.anchor==anchor]
                require(len(sections)==1 and reconcile(decl.signature,sections[0].code) is not None,
                        'external source/native declaration identity mismatch')
                evidence=independent['api/'+page.name]
                require(evidence['ids'].count(anchor)==1 and
                        [anchor,decl.name] in evidence['declarations'] and
                        sections[0].code in evidence['signatures'],
                        'external destination lacks independent native identity')
                types[identity]={
                    'qualified_name':pkg.name+'.'+decl.name,'package':pkg.name,
                    'kind':decl.kind,'source_path':pkg.path.relative_to(root/'qualification-public').as_posix(),
                    'source_line':decl.line,'source_file_sha256':digest(pkg.path.read_bytes()),
                    'source_declaration_sha256':digest(decl.signature.encode()),
                    'page':page.name,'anchor':anchor,
                    'native_declaration_sha256':digest(sections[0].code.encode()),
                    'qualification':'dependency-anchor-verified'}
    return {'schema_version':1,'repository':spec['repository'],'revision':spec['revision'],
            'gnatdoc':spec['gnatdoc'],'source_sha256':spec['source_sha256'],
            'native_sha256':spec['pristine_sha256'],'types':types,'unsupported':unsupported,
            'qualification':{'source_native_reconciliation':'pass',
                'unique_public_type_anchors':'pass','published_url':'not verified',
                'scope':'native public API; generic-instance members not exported'}}


def base_url(value, hosts):
    require(isinstance(value,str) and not re.search(r'[\x00-\x20\\%?#]',value),
            'unsafe dependency base URL')
    uri=urlsplit(value)
    require(uri.scheme=='https' and uri.netloc in hosts and uri.hostname==uri.netloc and
            uri.path.endswith('/') and
            all(p not in ('.','..') for p in uri.path.split('/')) and
            '//' not in uri.path,'unapproved dependency base URL')
    return value


def destinations(config):
    """Revalidate on enhancement AND independent publication reconstruction."""
    result={k.lower():v for k,v in config.externals.items()}
    owners={};repositories=set()
    for dep in config.dependencies:
        manifest_path=regular(inside(config.root,dep['manifest']))
        spec_path=regular(inside(config.root,dep['acquisition']))
        require(digest(manifest_path.read_bytes())==dep['manifest_sha256'],
                'external manifest hash mismatch')
        require(digest(spec_path.read_bytes())==dep['acquisition_sha256'],
                'external acquisition hash mismatch')
        manifest=read_json(manifest_path);spec=read_json(spec_path)
        require(manifest.get('repository')==spec.get('repository')==dep['repository'] and
                manifest.get('revision')==spec.get('revision')==dep['revision'],
                'external dependency repository/revision mismatch')
        require(dep['repository'] not in repositories,'conflicting dependency manifests')
        repositories.add(dep['repository'])
        observed=inventory(spec,inside(config.root,dep['source']),inside(config.root,dep['site']))
        require(manifest==observed,'external manifest differs from source/native identity evidence')
        base=base_url(dep['base_url'],config.allowed_hosts)
        # A reserved, explicit simulation URL cannot be mistaken for production.
        # No deployment is asserted by offline artifact qualification.
        require(dep['publication']=='offline-test' and urlsplit(base).hostname.endswith('.invalid'),
                'production publication is not qualified; offline-test requires a reserved .invalid host')
        require(dep['revision'] in urlsplit(base).path.split('/'),
                'test publication mapping must contain the immutable dependency revision')
        for name in dep['types']:
            key=name.lower()
            require(re.fullmatch(QNAME,name) and '.' in name and key in observed['types'],
                    'external type is not uniquely source-owned')
            item=observed['types'][key];owner=item['package'].lower()
            require(key.rsplit('.',1)[0]==owner,'incorrect external package ownership')
            authority=(dep['repository'],dep['revision'])
            require(owner not in owners or owners[owner]==authority,
                    'conflicting external type owners')
            owners[owner]=authority
            require(key not in result,'conflicting external types or aliases')
            result[key]=base+item['page']+'#'+item['anchor']
    return result


def verify_published(base, manifest, hosts, fetch):
    """Separate explicit network audit. HTTP success alone never proves identity.

    fetch(url) returns (final_url, bytes). Redirect substitutions are rejected.
    Match ALL pristine native bytes, including index and CSS, not just an ID.
    This observation is not permission to treat a mutable host as stable.
    """
    base_url(base,hosts)
    require(manifest['revision'] in urlsplit(base).path.split('/'),
            'publication URL does not explicitly pin the revision')
    checked={}
    for name,sha in sorted(manifest['native_sha256'].items()):
        require(name.startswith('api/') and len(Path(name).parts)==2,
                'unsupported publication artifact path')
        url=base+name.removeprefix('api/')
        final,content=fetch(url)
        require(final==url and digest(content)==sha,
                'published content differs from pinned dependency artifact')
        checked[url]=sha
    return {'status':'published-bytes-verified','revision':manifest['revision'],
            'urls':checked,'version_stability':'requires deployment-owner guarantee'}