"""Fail-closed GNATdoc index navigation enhancements."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .config import Config
from .destinations import source_destinations
from .native_html import NativeSite
from .theme import asset
from .util import inside, require

CONTROL = ('<div id="package-navigation" hidden><label for="package-search">'
           'Filter navigation links</label><input id="package-search" type="search" '
           'autocomplete="off" spellcheck="false">'
           '<button id="package-clear" type="button">Clear</button>'
           '<p id="package-results" role="status" aria-live="polite"></p></div>')
SCRIPT='<script src="gnatdoc-navigation.js" defer></script>'


def operation_entries(config: Config, native: NativeSite):
    if config.navigation!='operations':return []
    require(config.category_file is not None,"operation navigation requires categories JSON")
    data=json.loads(inside(config.root,config.category_file).read_text(encoding='utf-8'))
    require(isinstance(data,dict) and data.get('version')==1,"unsupported category manifest version")
    if 'packages' in data:
        require(set(data)=={'version','packages'},"unexpected category manifest keys")
        require(isinstance(data['packages'],list) and data['packages'],"empty category packages")
        require(all(isinstance(x,dict) and set(x)=={'package','categories'} for x in data['packages']),
                "invalid category package structure")
        groups=[(x['package'],x['categories']) for x in data['packages']]
    else:
        require(set(data)=={'version','categories'},"unexpected category manifest keys")
        require(len(native.pages)==1,"multi-package categories must declare package identities")
        groups=[(next(iter(native.pages.values())).package,data['categories'])]
    identities=source_destinations(config,native)
    result=[]; seen_packages=set(); seen_categories=set(); used=set()
    for package,categories in groups:
        require(isinstance(package,str),"invalid category package")
        key=package.lower()
        require(key in identities, f"unknown categorized package: {package}")
        require(key not in seen_packages,"duplicate categorized package")
        seen_packages.add(key)
        require(isinstance(categories,list) and categories,"empty categories")
        available={d.declaration.name.lower() for d in identities[key]}
        assigned=set()
        for category in categories:
            require(isinstance(category,dict) and set(category)=={'id','title','declarations'},"unknown category keys")
            cid,title=category['id'],category['title']
            require(isinstance(cid,str) and re.fullmatch(r'[a-z][a-z0-9-]*',cid)!=None,"unsafe category slug")
            require(cid not in seen_categories,"duplicate category identity")
            seen_categories.add(cid)
            require(isinstance(title,str) and bool(title),"invalid category title")
            names=category['declarations']
            require(isinstance(names,list) and names,"empty category declarations")
            selected=set()
            for requested in names:
                require(isinstance(requested,str),"invalid category operation")
                name=requested.lower()
                require(name in available, f"unresolved operation: {package}.{requested}")
                require(name not in assigned,"duplicate operation category assignment")
                assigned.add(name); selected.add(name)
            resolved=[]
            # Consumer presentation order is alphabetical, then source ordinal;
            # neither category declaration lists nor native section order number overloads.
            for destination in sorted((d for d in identities[key] if d.declaration.name.lower() in selected),
                                      key=lambda d:(d.declaration.name.lower(),d.ordinal)):
                name=destination.declaration.name
                label=f"{name} ({destination.ordinal})" if destination.total>1 else name
                require(destination.href not in used,"duplicate operation destinations")
                used.add(destination.href)
                resolved.append((label,destination.href))
            result.append((package,cid,title,resolved))
        require(assigned==available,f"missing category assignments: {package}: {sorted(available-assigned)}")
        require({d.href for d in identities[key]}==
                {native.pages[key].path.name+'#'+s.anchor for s in native.pages[key].sections},
                f"incomplete source/native operation identities: {package}")
    require(seen_packages==set(identities),"missing categorized packages")
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
    from .symbols import metadata
    extra += metadata(config, native)
    value=original.replace('<h2 id=compilation-units>',CONTROL+extra+'<h2 id=compilation-units>',1)
    return value.replace('<body class=main>',SCRIPT+'<body class=main>',1)
