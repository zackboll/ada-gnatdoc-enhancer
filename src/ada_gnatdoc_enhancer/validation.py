"""Independent static-site, source, link and publication-surface validation."""
from __future__ import annotations

import html
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from .config import Config
from .errors import EnhancementError
from .util import PAGE_NAME, local_link, require

SCRIPT = 'api/gnatdoc-navigation.js'


class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.links=[];self.issues=[];self.scripts=[];self.iframes=0;self.package_entries=[]
        self.feed(text);self.close()

    def handle_starttag(self,tag,attrs):
        if tag in ('style','base','object','embed','applet','form','svg','math','video','audio','img'):
            self.issues.append(f"disallowed HTML element: {tag}")
        keys=dict(attrs)
        if len(keys)!=len(attrs):self.issues.append(f"duplicate HTML attribute: {tag}")
        if tag=='link' and (set(keys)!={'href','rel'} or keys.get('rel')!='stylesheet'):
            self.issues.append('unapproved stylesheet/resource link')
        for key,value in attrs:
            if key.lower().startswith('on') or key in ('style','srcdoc','http-equiv'):
                self.issues.append(f"executable attribute: {key}")
            if key in ('srcset','action','formaction','poster','data','background'):
                self.issues.append(f"unapproved URL attribute: {key}")
            if key=='id':self.ids.append(value)
            if key in ('src','href'):self.links.append(value)
        if tag=='script':
            if set(keys)!={'src','defer'} or keys.get('defer') is not None:
                self.issues.append('script with unapproved attributes')
            self.scripts.append(keys.get('src'))
        if tag=='iframe':
            self.iframes+=1
            if keys.get('name')!='document-content' or 'src' in keys or len(keys)!=1:
                self.issues.append('unapproved iframe')
        if 'data-package-entry' in keys:
            self.package_entries.append((keys['data-package-entry'],keys.get('href')))
    handle_startendtag=handle_starttag


def css_safe(content:bytes):
    text=content.decode('utf-8')
    value=re.sub(r'/\*.*?\*/','',text,flags=re.S)
    require('\\' not in value and not re.search(
        r'@import|url\s*\(|expression\s*\(|-moz-binding|behavior\s*:',value,re.I),
        'unapproved CSS resource, escaped import or execution expression')


def validate_files(site:Path,config:Config,expected:set[str], *, raw=False):
    """Reject unpublished extra content and independently validate local links."""
    require(site.is_dir() and not site.is_symlink(),'invalid/symlink site root')
    observed=set(); pages={}
    for path in site.rglob('*'):
        require(not path.is_symlink(),f"symlink published: {path}")
        if path.is_dir():continue
        require(path.is_file(),f"unexpected published node: {path}")
        relative=path.relative_to(site).as_posix()
        observed.add(relative)
        require(relative in expected,f"unapproved output file: {relative}")
        if path.suffix=='.css':css_safe(path.read_bytes())
        elif path.suffix=='.js':
            require(relative==SCRIPT,'unapproved JavaScript file')
            require('eval(' not in path.read_text() and 'new Function(' not in path.read_text(),
                    'prohibited dynamic JavaScript evaluation')
        elif path.suffix=='.html':
            text=path.read_text(encoding='utf-8')
            require(not re.search(r'/(?:home|tmp|Users)/|file:/{2}|[A-Z]:\\',text),
                    f"machine-local path leak: {relative}")
            require('{{' not in text and '}}' not in text, f"unresolved template in {relative}")
            page=Page(text)
            require(not page.issues and len(page.ids)==len(set(page.ids)),
                    f"unsafe HTML/duplicate IDs in {relative}: {page.issues}")
            if page.scripts:
                require(relative=='api/index.html' and page.scripts==['gnatdoc-navigation.js'],
                        f"unapproved script in {relative}")
            require(page.iframes == (1 if relative=='api/index.html' else 0),
                    f"unapproved/missing native iframe in {relative}")
            pages[path.resolve()]=page
    require(expected==observed,f"missing site files: {sorted(expected-observed)}")
    for path,page in pages.items():
        for link in page.links:
            target,fragment=local_link(path,site,link,external=config.allowed_hosts,
                                       exact_external_fragments=frozenset(config.externals.values()))
            if target is None:continue
            if fragment:
                require(target.resolve() in pages and fragment in pages[target.resolve()].ids,
                        f"broken fragment {link} from {path}")
    return {'files':len(observed),'html_pages':len(pages),'links':sum(len(x.links) for x in pages.values())}
