"""Fail-closed GNATdoc index navigation enhancements."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .config import Config
from .native_html import NativeSite
from .theme import asset
from .util import inside, require

CONTROL = ('<div id="package-navigation" hidden><label for="package-search">'
           'Search documentation</label><input id="package-search" type="search" '
           'autocomplete="off" spellcheck="false">'
           '<button id="package-clear" type="button">Clear</button>'
           '<p id="package-results" role="status" aria-live="polite"></p></div>')
SCRIPT='<script src="gnatdoc-navigation.js" defer></script>'


def operation_entries(config: Config, native: NativeSite):
    if config.navigation!='operations':return []
    require(config.category_file is not None,"operation navigation requires categories JSON")
    data=json.loads(inside(config.root,config.category_file).read_text(encoding='utf-8'))
    require(data.get('version')==1,"unsupported category manifest version")
    if 'packages' in data:
        require(set(data)=={'version','packages'},"unexpected category manifest keys")
        groups=[(x['package'],x['categories']) for x in data['packages']]
    else:
        require(set(data)=={'version','categories'},"unexpected category manifest keys")
        require(len(native.pages)==1,"multi-package categories must declare package identities")
        groups=[(next(iter(native.pages.values())).package,data['categories'])]
    result=[]
    for package,categories in groups:
        page=native.pages.get(package.lower())
        require(page is not None, f"unknown categorized package: {package}")
        for category in categories:
            require(set(category)=={'id','title','declarations'},"unknown category keys")
            cid,title=category['id'],category['title']
            require(re.fullmatch(r'[a-z][a-z0-9-]*',cid)!=None,"unsafe category slug")
            require(isinstance(title,str) and bool(title),"invalid category title")
            resolved=[]
            for requested in category['declarations']:
                matches=[s for s in page.sections if s.name.lower()==requested.lower()]
                require(matches, f"unresolved operation: {package}.{requested}")
                # An overloaded operation becomes one clickable item per actual
                # native declaration; native anchors are never invented.
                for section in matches:
                    resolved.append((f"{section.name} ({len(resolved)+1})" if len(matches)>1 else section.name,
                                     page.path.name+'#'+section.anchor))
            require(len(set(target for _,target in resolved))==len(resolved),
                    "duplicate operation destinations in category")
            result.append((package,cid,title,resolved))
    return result


def enhance_index(native:NativeSite, original:str, config:Config) -> str:
    if config.navigation=='none':return original
    require(original.count('<h2 id=compilation-units>')==1,
            'unqualified GNATdoc navigation heading')
    require(original.count('<body class=main>')==1,'unqualified GNATdoc browser shell')
    require('gnatdoc-navigation.js' not in original and 'id="package-navigation"' not in original,
            'native navigation already modified')
    extra=''
    entries=operation_entries(config,native)
    if entries:
        blocks=[]
        for package,cid,title,dests in entries:
            items=''.join('<li><a href="'+html.escape(url,quote=True)+'" target=document-content>'+
                          html.escape(label)+'</a></li>' for label,url in dests)
            blocks.append('<section class="operation-group" data-category="'+cid+'"><h3>'+html.escape(title)+
                          '</h3><ul>'+items+'</ul></section>')
        extra='<div id="operation-navigation"><h2>Browse operations</h2>'+''.join(blocks)+'</div>'
    value=original.replace('<h2 id=compilation-units>',CONTROL+extra+'<h2 id=compilation-units>',1)
    return value.replace('<body class=main>',SCRIPT+'<body class=main>',1)
