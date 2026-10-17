"""Deterministic GNATdoc Ada lexical highlighting and source-backed type links.

Inspired by the Apache-2.0 OpenCV Core/Imgproc/Geometry enhancers. This module
keeps native source text, HTML entities, GNATdoc ids and hyperlink markup intact.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from .config import Config
from .errors import EnhancementError
from .inventory import Package
from .native_html import NativeSite
from .util import QNAME, require

KEYWORDS = frozenset('''abort abs abstract accept access aliased all and array at begin body
case constant declare delay delta digits do else elsif end entry exception exit for
function generic goto if in interface is limited loop mod new not null of or
others out overriding package parallel pragma private procedure protected raise
range record rem renames requeue return reverse select separate some subtype
synchronized tagged task terminate then type until use when while with xor'''.split())
LEXEME = re.compile(
    r'(?P<comment>--[^\n]*)|(?P<string>"(?:[^"\n]|"")*")|'
    r"(?P<character>'[^\n]')|(?P<attribute>'[A-Za-z][A-Za-z0-9_]*)|"
    r'(?P<number>[0-9][0-9_]*\#[0-9A-Fa-f_]+(?:\.[0-9A-Fa-f_]+)?\#'
    r'(?:[Ee][+-]?[0-9][0-9_]*)?|[0-9][0-9_]*(?:\.(?!\.)[0-9][0-9_]*)?'
    r'(?:[Ee][+-]?[0-9][0-9_]*)?)|'
    r'(?P<identifier>[A-Za-z][A-Za-z0-9_]*)|'
    r'(?P<operator>:=|=>|\.\.|\*\*|/=|<=|>=|<>|[&+*/=<>:;,.()|\-])')
TYPE_LINK = re.compile(r'<a class="type-reference" href="([^"<>]+)" data-type="([A-Za-z0-9_.]+)">([^<>]+)</a>')
SPAN = re.compile(r'<span class="ada-(?:keyword|number|string|character|attribute|comment|operator)">([^<]*)</span>')
CODE = re.compile(r'(<pre class=ada-code-snippet><code>)(.*?)(</code></pre>)', re.S)
SIMPLE_TYPE = re.compile(r'^'+QNAME+'$', re.I)
TYPE_MARK = re.compile(
    r'(?<![\w.])(?:return|of|\bis\s+(?:new|access|not\s+null\s+access)|:\s*(?:not\s+null\s+)?(?:aliased\s+)?(?:(?:in\s+out|in|out|access|constant)\s+)*)\s*('
    + QNAME + r')\b', re.I)
STANDARD = frozenset('integer natural positive boolean float long_float long_long_float string wide_string duration character wide_character interfaces'.split())


def escaped_offsets(raw: str):
    text, starts, ends = [], [], []
    for m in re.finditer(r'&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z0-9]+);|.', raw, re.S):
        for char in html.unescape(m.group()):
            text.append(char); starts.append(m.start()); ends.append(m.end())
    return ''.join(text), starts, ends


def plain(raw: str):
    value = SPAN.sub(lambda m:m[1], raw)
    value = TYPE_LINK.sub(lambda m:m[3], value)
    require('<' not in value,
            "unsupported or nested HTML tags inside Ada declaration snippet")
    return html.unescape(value)


def highlighted(raw: str):
    original = plain(raw)
    def interval(piece):
        text,starts,ends = escaped_offsets(piece)
        adds=[]
        for match in LEXEME.finditer(text):
            kind=match.lastgroup
            if kind=='identifier':
                if match.group().lower() not in KEYWORDS: continue
                kind='keyword'
            a,b=starts[match.start()],ends[match.end()-1]
            adds.append((a,b,f'<span class="ada-{kind}">{piece[a:b]}</span>'))
        for a,b,s in reversed(adds): piece=piece[:a]+s+piece[b:]
        return piece
    results, pos = [], 0
    for match in TYPE_LINK.finditer(raw):
        results.extend((interval(raw[pos:match.start()]), match[0]));pos=match.end()
    results.append(interval(raw[pos:]))
    final=''.join(results)
    require(plain(final)==original, "highlighting changed visible declaration text")
    return final


def _local_shadow(pkg: Package, name: str) -> bool:
    return any(d.name.lower()==name and d.kind not in ('type','subtype')
               for d in pkg.declarations)


def resolve(name: str, pkg: Package, source: dict[str, Package],
            targets: dict[str, tuple[Path,str]], external: dict[str,str]) -> tuple[str, str] | None:
    """Conservative resolution: never choose a destination from name alone."""
    token=name.lower(); key=pkg.name.lower()
    if token in STANDARD or token in KEYWORDS: return None
    if '.' in token:
        owner=token.rsplit('.',1)[0]
        if owner!=key and not key.startswith(owner+'.') and owner not in pkg.imports:
            return None
        if token in targets: return token, 'local'
        exact=next((k for k in external if k.lower()==token),None)
        if exact: return exact,'external'
        return None
    # A local non-type declaration prevents guessing an ancestor type.
    if _local_shadow(pkg,token): return None
    p=key
    while p:
        fullname=p+'.'+token
        if fullname in targets: return fullname,'local'
        if p in source and _local_shadow(source[p],token): return None
        p=p.rpartition('.')[0]
    # Unqualified names imported via use are potentially ambiguous. Explicit
    # one-owner resolution is allowed only if exactly one imported type matches.
    matches=[p+'.'+token for p in pkg.uses if p+'.'+token in targets and p in pkg.imports]
    return (matches[0],'local') if len(matches)==1 else None


def type_positions(code: str):
    """Typed contexts only; do not link constraints, defaults or attributes."""
    positions=[]
    for m in TYPE_MARK.finditer(code):
        word=m[1]
        if word.lower() not in KEYWORDS and word.lower() not in STANDARD:
            positions.append((m.start(1),m.end(1),word))
    return positions


def linked(raw: str, pkg: Package, source: dict[str, Package],
           native: NativeSite, targets: dict[str,tuple[Path,str]], config: Config):
    require('<' not in raw,"type linking requires raw GNATdoc snippets")
    text,starts,ends=escaped_offsets(raw)
    inserts=[]
    for a,b,name in type_positions(text):
        target=resolve(name,pkg,source,targets,config.externals)
        if target is None:continue
        identity,kind=target
        if kind=='external': url=config.externals[identity]
        else:
            target_page,anchor=targets[identity]
            url=target_page.name+'#'+anchor
        src_a,src_b=starts[a],ends[b-1]
        encoded=raw[src_a:src_b]
        inserts.append((src_a,src_b,
                        f'<a class="type-reference" href="{html.escape(url,quote=True)}" '
                        f'data-type="{identity}">{encoded}</a>'))
    # Only accept nonoverlapping type-mark spans.
    used=set()
    for start,end,_ in inserts:
        require(not any(i in used for i in range(start,end)),"overlapping type positions")
        used.update(range(start,end))
    for a,b,markup in reversed(inserts):raw=raw[:a]+markup+raw[b:]
    require(plain(raw)==text,"type linker changed escaped original declaration")
    return raw,len(inserts)


def transform_page(original: str, pkg: Package, source: dict[str,Package],
                   native: NativeSite, targets, config:Config):
    counts={'links':0,'snippets':0}
    def render(m):
        raw=m[2];before=plain(raw)
        if config.type_links:
            raw,linked_count=linked(raw,pkg,source,native,targets,config)
            counts['links']+=linked_count
        if config.highlight:raw=highlighted(raw)
        require(plain(raw)==before,"snippet not text preserving")
        counts['snippets']+=1
        return m[1]+raw+m[3]
    return CODE.sub(render,original),counts
