"""Offline HTML portal or strict Markdown guides with verified API links."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .config import Config
from .native_html import NativeSite
from .theme import asset
from .util import inside, regular, require

TOKEN = re.compile(r'\{\{(package:[A-Za-z0-9_.]+|navigation|package-directory)\}\}')


def manifest(config:Config):
    require(config.guide_manifest,"missing guide manifest")
    data=json.loads(regular(inside(config.root,config.guide_manifest)).read_text(encoding='utf-8'))
    require(set(data)=={'schema_version','home','stylesheet','guides'} and data['schema_version']==1,
            "unknown guide manifest structure")
    require(data['home']=='index.html' and data['stylesheet']=='assets/gnatdoc-guides.css',
            "unsupported guide landing/style paths; use owned output paths")
    require(isinstance(data['guides'],list) and data['guides'],"guides must be a nonempty array")
    names=set()
    for g in data['guides']:
        require(set(g) in ({'id','label','path'},{'id','label','path','example'}),
                "unknown guide entry")
        require(re.fullmatch(r'[a-z][a-z0-9-]*',g['id']) is not None,"unsafe guide identity")
        require(isinstance(g['label'],str) and bool(g['label']),"invalid guide label")
        require(g['path']==f'guides/{g["id"]}.html',"guide path not canonical")
        require(g['id'] not in names,"duplicate guide")
        names.add(g['id'])
    return data


def _package_url(name: str, page: str, native:NativeSite):
    p=native.pages.get(name.lower())
    require(p is not None, f"unknown package link: {name}")
    return ('../' if page.startswith('guides/') else '')+'api/'+p.path.name


def navigation(data:dict,page:str):
    prefix='../' if page.startswith('guides/') else ''
    a=[f'<a href="{prefix}index.html">Home</a>',f'<a href="{prefix}api/index.html">API Reference</a>']
    for g in data['guides']:
        a.append('<a href="'+prefix+g['path']+'">'+html.escape(g['label'])+'</a>')
    return '<nav aria-label="Documentation"><p>'+' · '.join(a)+'</p></nav>'


def directory(page:str,native:NativeSite):
    groups={}
    for pkg in sorted(native.pages.values(),key=lambda p:p.package.lower()):
        name=pkg.package
        if name.lower().startswith('ams.mel.ir.'):group='IR'
        elif name.lower().startswith('ams.mel.rf.'):group='RF'
        elif name.lower().startswith('ams'):group='Shared/Core'
        else:group=name.split('.')[0]
        groups.setdefault(group,[]).append(name)
    blocks=[]
    for group, names in groups.items():
        entries=[]
        for name in names:
            url=_package_url(name,page,native)
            entries.append('<li><a data-package-entry="'+name+'" href="'+url+'">'+name+'</a></li>')
        blocks.append('<h3>'+html.escape(group)+'</h3><ul>'+''.join(entries)+'</ul>')
    return '<section class="package-directory" aria-label="Public packages">'+''.join(blocks)+'</section>'


def _replace(text:str,page:str,data:dict,native:NativeSite):
    def one(m):
        token=m[1]
        if token=='navigation': return navigation(data,page)
        if token=='package-directory':return directory(page,native)
        name=token.partition(':')[2]
        return '<a href="'+_package_url(name,page,native)+'">'+html.escape(name)+'</a>'
    result=TOKEN.sub(one,text)
    require('{{' not in result and '}}' not in result,"unknown/unresolved guide substitution")
    return result


def _markdown(source:str,page:str,data:dict,native:NativeSite, config:Config, example:str | None):
    try:
        from importlib.metadata import version
        from markdown_it import MarkdownIt
    except ImportError as exc:
        raise ValueError('Markdown guides require pip install ada-gnatdoc-enhancer[guides]') from exc
    require(version('markdown-it-py')=='3.0.0' and version('mdurl')=='0.1.2',
            'Markdown guide renderer requires pinned markdown-it-py 3.0.0 / mdurl 0.1.2')
    parser=MarkdownIt('commonmark', {'html': False}).enable('table')
    parser.validateLink=lambda value:True
    tokens=parser.parse(source)
    h1=0;examples=[];seen=set()
    for i,tok in enumerate(tokens):
        require(tok.type not in ('html_block','html_inline','image'),"guide contains forbidden HTML/image")
        if tok.type=='heading_open':
            if tok.tag=='h1':h1+=1
        if tok.type=='fence':
            kind=tok.info.strip()
            require(kind in ('ada','sh','shell','text',''),"unsupported fenced code language")
            if kind=='ada':examples.append(tok.content.strip('\n'))
        for child in tok.children or []:
            require(child.type not in ('html_inline','image'),"unsafe inline markup")
            if child.type=='link_open':
                href=child.attrGet('href')
                if href.startswith('api:'):
                    target=href[4:]
                    match=re.fullmatch(r'([A-Za-z0-9_.]+)(?:/([1-9][0-9]*))?',target)
                    require(match is not None,"invalid api: target")
                    identity,n=match.group(1),match.group(2)
                    if identity.lower() in native.pages:
                        require(n is None,"no overload index on a package")
                        child.attrSet('href',_package_url(identity,page,native))
                    else:
                        parent,_,member=identity.rpartition('.')
                        p=native.pages.get(parent.lower())
                        require(p is not None,"api: declaration needs qualified package")
                        found=[s for s in p.sections if s.name.lower()==member.lower()]
                        require(found and (n is not None or len(found)==1),
                                "unresolved or ambiguous api: declaration link")
                        index=int(n)-1 if n else 0
                        require(index < len(found),"api: overload index out of range")
                        child.attrSet('href',_package_url(parent,page,native)+'#'+found[index].anchor)
                else:
                    # Final site validator independently checks local and allowlisted HTTPS.
                    require(not href.startswith(('javascript:','data:','file:')),
                            "unapproved Markdown link scheme")
    require(h1==1 and tokens and tokens[0].type=='heading_open' and tokens[0].tag=='h1',
            "guide must start with exactly one H1")
    if example:
        code=regular(inside(config.root,example)).read_text(encoding='utf-8').strip('\n')
        require(len(examples)==1 and examples[0]==code,
                "Ada code fence differs from its authoritative example source")
    else:
        require(not examples,"Ada code fences require an explicitly recorded example source")
    inner=parser.renderer.render(tokens,parser.options,{})
    inner=inner.replace('<table>','<div class="table-scroll"><table>').replace('</table>','</table></div>')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<link rel="stylesheet" href="../assets/gnatdoc-guides.css"></head><body>'
            '<a class="skip" href="#main">Skip to content</a><header>'+navigation(data,page)+
            '</header><main id="main">'+inner+'</main></body></html>\n')


def render(config:Config,native:NativeSite) -> dict[str,bytes]:
    if config.guides=='none':return {}
    if config.guides.startswith('authored-'):
        from .authored import render as authored_render
        return authored_render(config,native)
    data=manifest(config)
    written={}
    home=regular(inside(config.root,'docs/index.html')).read_text(encoding='utf-8')
    written['index.html']=_replace(home,'index.html',data,native).encode()
    for g in data['guides']:
        path=g['path']
        if config.guides=='html':
            source=regular(inside(config.root,'docs/'+path)).read_text(encoding='utf-8')
            html_text=_replace(source,path,data,native)
        else:
            source=regular(inside(config.root,'docs/'+path[:-5]+'.md')).read_text(encoding='utf-8')
            html_text=_markdown(source,path,data,native,config,g.get('example'))
        written[path]=html_text.encode()
    written['assets/gnatdoc-guides.css']=asset('gnatdoc-guides.css')
    return written
