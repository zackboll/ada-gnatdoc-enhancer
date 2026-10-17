"""Pinned real-input qualification, separate from synthetic conformance.

The input specification is a reviewed acquisition record, not proof that an
arbitrary directory was produced by GNATdoc. Hashes bind it to that record.
No command here builds or modifies a consumer checkout, or uses the network.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path

from .config import load
from .inventory import packages
from .native_html import snapshot
from .pipeline import MANIFEST, enhance, verify
from .util import digest, inside, regular, require, site_root, sorted_json


def hashes(root):
    root=site_root(root)
    return {p.relative_to(root).as_posix():digest(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


def check_snapshot(root, expected, *, staged=False):
    require(isinstance(expected,dict) and expected,'empty pinned source inventory')
    for name,sha in expected.items():
        require(re.fullmatch('[a-f0-9]{64}',sha) is not None,'invalid SHA-256')
        path=inside(root,name)
        require(all(not p.is_symlink() for p in (path,*path.parents)),
                f'symlink input path: {name}')
        require(digest(regular(path).read_bytes())==sha,f'pinned source mismatch: {name}')
    # Build products may exist, but additional Ada inputs must not slip in.
    actual={p.relative_to(root).as_posix() for p in root.rglob('*')
            if p.suffix.lower() in ('.ads','.adb') and
            not (staged and p.is_relative_to(root/'qualification-public'))}
    require(actual=={n for n in expected if Path(n).suffix.lower() in ('.ads','.adb')},
            'unpinned Ada source inventory')


class Identities(HTMLParser):
    """Independent text/ID collector; deliberately does not use native regexes."""
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.headings=[];self.snippets=[];self.links=[]
        self.heading=None;self.code=None;self.text=[]
        self.feed(text);self.close()

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='h4':self.heading=[attrs.get('id'),'']
        if tag=='code':self.code=''
        if tag=='a' and 'href' in attrs:self.links.append(attrs['href'])

    def handle_data(self,data):
        self.text.append(data)
        if self.heading is not None:self.heading[1]+=data
        if self.code is not None:self.code+=data

    def handle_endtag(self,tag):
        if tag=='h4' and self.heading is not None:
            self.headings.append(self.heading);self.heading=None
        if tag=='code' and self.code is not None:
            self.snippets.append(self.code);self.code=None


def identities(site):
    result={}
    for path in sorted((site/'api').glob('*.html')):
        text=path.read_text(encoding='utf-8');page=Identities(text)
        title=re.findall(r'<h1>([^<]+)</h1>',text)
        result[path.relative_to(site).as_posix()]={
            'package':html.unescape(title[0]) if len(title)==1 else None,
            'ids':page.ids,'declarations':page.headings,'signatures':page.snippets,
            'visible_text_sha256':digest(''.join(page.text).encode()),
            'native_links':page.links}
    return result


def preserve_native(before,site):
    after=identities(site)
    require(set(before)==set(after),'native page inventory changed')
    for name,old in before.items():
        new=after[name]
        for key in ('package','declarations','signatures'):
            require(new[key]==old[key],f'native {key} changed: {name}')
        if name!='api/index.html':
            require(new['visible_text_sha256']==old['visible_text_sha256'],
                    f'native visible content changed: {name}')
        require(set(old['ids'])<=set(new['ids']),f'native anchor removed: {name}')
        require(set(old['native_links'])<=set(new['native_links']),f'native link removed: {name}')
    return {'pages':len(before),
            'packages':sum(p['package'] is not None for p in before.values()),
            'declarations':sum(len(p['declarations']) for p in before.values()),
            'signatures':sum(len(p['signatures']) for p in before.values()),
            'status':'preserved'}


def bind_pristine(pristine,site):
    """Do not let an output manifest redefine its own pristine authority."""
    manifest=json.loads((site/MANIFEST).read_text(encoding='utf-8'))
    raw={p.relative_to(pristine).as_posix():p.read_text(encoding='utf-8')
         for p in (pristine/'api').glob('*.html')}
    require(manifest['original_api_html']==raw,'captured native input differs from pristine authority')
    for path in pristine.rglob('*'):
        if not path.is_file() or path.suffix=='.html':continue
        require((site/path.relative_to(pristine)).read_bytes()==path.read_bytes(),
                'non-HTML pristine content changed')


def negative_checks(root,site):
    """Publication verification must reject four independent corruption classes."""
    config=load(root,'qualification.toml');results={}
    page=next(p for p in sorted((site/'api').glob('*.html')) if p.name!='index.html')
    native=identities(site)[page.relative_to(site).as_posix()]
    require(native['declarations'],'negative checks need a real native declaration')
    anchor=native['declarations'][0][0]
    source_path=next(iter(packages(config).values())).path
    mutations={
        'anchor':(page,page.read_bytes().replace(anchor.encode(),b'0'*64)),
        'link':(page,page.read_bytes()+b'<a href="missing.html#missing">invalid</a>'),
        'asset':(site/'api/gnatdoc-theme.css',b'/* altered asset */'),
        'source':(source_path,source_path.read_bytes()+b'\n-- identity mismatch\n'),
    }
    for label,(path,changed) in mutations.items():
        original=path.read_bytes()
        try:
            path.write_bytes(changed)
            try:verify(config,site)
            except (ValueError,OSError) as exc:
                results[label]={'rejected':True,'reason':str(exc)}
            else:raise ValueError(f'verifier accepted {label} tampering')
        finally:path.write_bytes(original)
    verify(config,site)
    return results


def run(spec_path:Path, source:Path, pristine:Path, workspace:Path):
    spec=json.loads(regular(spec_path).read_text(encoding='utf-8'))
    require(spec['schema_version']==1,'unsupported qualification specification')
    require(re.fullmatch('[a-f0-9]{40}',spec['revision']) is not None,
            'consumer revision must be an immutable Git SHA')
    require(spec['gnatdoc']=='GNATdoc 26.0.0 (20260415)','unqualified native generator')
    require(spec['evidence_level'] and spec['public_sources'],'missing acquisition scope/public sources')
    require(len(spec['public_sources'])==len(set(spec['public_sources'])),
            'duplicate public source paths')
    # Check lexical paths before resolve/copy. Never follow input symlinks.
    source=site_root(source);pristine=site_root(pristine)
    require(not workspace.exists() and not workspace.is_symlink(),'workspace must be new')
    require(all(not p.is_symlink() for p in workspace.parents),'symlink workspace ancestor')
    workspace=workspace.resolve()
    for original in (source,pristine):
        require(not workspace.is_relative_to(original) and not original.is_relative_to(workspace),
                'qualification workspace overlaps an input')
    check_snapshot(source,spec['source_sha256'])
    input_hashes=hashes(pristine)
    require(input_hashes==spec['pristine_sha256'],'pristine site hashes mismatch')
    require(not (pristine/MANIFEST).exists(),'enhanced site is not pristine input')
    require(all('gnatdoc-theme.css' not in p.read_text(encoding='utf-8')
                for p in pristine.rglob('*.html')),'postprocessed native input')
    native=identities(pristine)
    workspace.mkdir(parents=True)
    report={'schema_version':1,'repository':spec['repository'],'revision':spec['revision'],
            'evidence_level':spec['evidence_level'],'native_input':'verified against acquisition hashes',
            'source_sha256':spec['source_sha256'],'pristine_sha256':input_hashes,
            'native_inventory':native,'expected_packages':spec['public_packages'],
            'observed_packages':sorted(p['package'] for p in native.values() if p['package']),
            'checks':{name:'not executed' for name in ('source_inventory','dry_run',
                'enhancement','publication','native_integrity','idempotence',
                'negative_integrity','determinism')},'blockers':list(spec.get('blockers',[])),
            'browser':{'status':'not executed'},'full_site_compatibility':'incompatible'}
    states=[];phase='configuration'
    try:
        require(report['expected_packages']==report['observed_packages'],
                'acquisition public package inventory mismatch')
        for label in ('first','second'):
            root=workspace/label;root.mkdir()
            for name in spec['source_sha256']:
                target=inside(root,name);target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source/name,target)
            # Preserve original paths and bytes; stage only the explicitly
            # inventoried public units to avoid recursive internal resolution units.
            for name in spec['public_sources']:
                require(name in spec['source_sha256'],'public source is not pinned')
                target=root/'qualification-public'/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(root/name,target)
            (root/'qualification.toml').write_text(spec['configuration'],encoding='utf-8')
            site=root/'_site';shutil.copytree(pristine,site,symlinks=False)
            config=load(root,'qualification.toml')
            phase='inventory';source_packages=packages(config)
            report['checks']['source_inventory']={'packages':sorted(p.name for p in source_packages.values()),
                'declarations':sum(len(p.declarations) for p in source_packages.values()),
                'scope':'conservative scanner types/subtypes/calls, NOT full consumer coverage model',
                'profiles':{p.name:[{'name':d.name,'kind':d.kind,'line':d.line,
                                    'signature':d.signature} for d in p.declarations]
                            for p in source_packages.values()}}
            snapshot(config,site)
            phase='dry_run';report['checks']['dry_run']=enhance(config,site,dry_run=True)
            require(hashes(site)==input_hashes,'dry-run changed input bytes')
            phase='enhance';report['checks']['enhancement']=enhance(config,site)
            phase='verify';report['checks']['publication']=verify(config,site)
            bind_pristine(pristine,site)
            report['checks']['native_integrity']=preserve_native(native,site)
            require((site/'api/gnatdoc.css').read_bytes()==(pristine/'api/gnatdoc.css').read_bytes(),
                    'native stylesheet changed')
            state=hashes(site)
            phase='idempotence';enhance(config,site)
            require(state==hashes(site),'second enhancement changed bytes')
            report['checks']['idempotence']=True
            phase='negative_integrity'
            if label=='first':report['checks']['negative_integrity']=negative_checks(root,site)
            check_snapshot(root,spec['source_sha256'],staged=True)
            for name in spec['public_sources']:
                require(digest((root/'qualification-public'/name).read_bytes())==spec['source_sha256'][name],
                        f'staged public source changed: {name}')
            states.append(state)
        phase='determinism';require(states[0]==states[1],'identical pinned inputs differ')
        report['checks']['determinism']=True
        report['output_sha256']=states[0]
        # A successful structural run alone is not a full adoption certificate.
        report['structural_result']='pass'
        report['full_site_compatibility']='not fully qualified'
    except (ValueError,OSError,KeyError) as exc:
        report['structural_result']='fail'
        report['failure']={'phase':phase,'reason':str(exc)}
    finally:
        check_snapshot(source,spec['source_sha256'])
        require(hashes(pristine)==input_hashes,'original pristine input changed')
        report['original_inputs_preserved']=True
    (workspace/'report.json').write_text(sorted_json(report),encoding='utf-8')
    return report