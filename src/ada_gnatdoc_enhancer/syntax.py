"""Deterministic GNATdoc Ada lexical highlighting and source-backed type links.

Inspired by the Apache-2.0 OpenCV Core/Imgproc/Geometry enhancers. This module
keeps native source text, HTML entities, GNATdoc ids and hyperlink markup intact.
"""
from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path

from .config import Config
from .errors import EnhancementError
from .inventory import Package
from .native_html import NativeSite
from .util import IDENT, QNAME, require

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
TYPE_LINK = re.compile(r'<a class="type-reference" href="([^"<>]+)" data-type="([A-Za-z0-9_.]+)"(?: target="_top")?>([^<>]+)</a>')
SPAN = re.compile(r'<span class="ada-(?:keyword|number|string|character|attribute|comment|operator)">([^<]*)</span>')
CODE = re.compile(r'(<pre class=ada-code-snippet><code>)(.*?)(</code></pre>)', re.S)
SIMPLE_TYPE = re.compile(r'^'+QNAME+'$', re.I)
TYPE_MARK = re.compile(
    r'(?<![\w.])(?:return|of|\bis\s+(?:new|access|not\s+null\s+access)|:\s*(?:not\s+null\s+)?(?:aliased\s+)?(?:(?:in\s+out|in|out|access|constant)\s+)*)\s*('
    + QNAME + r')\b', re.I)
# A complete declaration snippet, not arbitrary "is Name" syntax. Attributes,
# null exclusions and other unsupported subtype indications remain unguessed.
SUBTYPE_BASE = re.compile(
    r'^\s*subtype\s+' + IDENT + r'\s+is\s+(' + QNAME +
    r')(?=\s*(?:;|\(|\brange\b))', re.I)
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


def external_visible(owner: str, pkg: Package) -> bool:
    """Narrow external guard, not a general Ada semantic resolver.

    Private/limited context clauses do not authorize a public type mark.
    Package aliases, instances, nested scopes and prefix declarations require
    semantics outside this adapter and therefore cannot grant external links.
    """
    return _external_profile(owner,pkg.source)


@lru_cache(maxsize=64)
def _external_profile(owner: str, source: str) -> bool:
    # Cache only immutable source text, never filesystem validation or evidence.
    from .inventory import HEADER, mask_ada, visible_prefix
    masked=mask_ada(source);header=HEADER.search(masked)
    if header is None or header[3].lower()!='is':return False
    context=masked[:header.start()]
    if re.search(r'\bgeneric\b',context,re.I):return False
    public=mask_ada(visible_prefix(source,header.end()))
    if re.search(r'\b(package|generic|task|protected|begin|declare)\b',public,re.I):return False
    prefix=owner.split('.')[0]
    if re.search(r'(?im)^\s*'+re.escape(prefix)+r'\s*(?:,|:)',public):return False
    restricted=set()
    for clause in re.finditer(r'(?im)^\s*(?:private\s+|limited\s+)+with\s+([^;]+);',context):
        restricted.update(n.strip().lower() for n in clause[1].split(','))
    return owner not in restricted


@lru_cache(maxsize=64)
def _current_package_prefix(key: str, selector: str, source: str) -> bool:
    """Prove a short current-package prefix in a deliberately flat subset.

    Inventory.declarations is not a scope table (notably it omits objects).
    Instead decline *every* bare use of the actual short identifier in the
    masked public region. This includes defining names in same-line and comma
    lists, enum literals, formals, components and discriminants, regardless of
    whether the inventory models them. It also deliberately rejects some safe
    nondefining uses; this is not a general Ada semantic front end.
    """
    from .inventory import HEADER, mask_ada
    masked=mask_ada(source);header=HEADER.search(masked)
    if (header is None or header[1] or header[2].lower()!=key or
            header[3].lower()!='is'):
        return False
    if re.search(r'\bgeneric\b',masked[:header.start()],re.I):return False
    public=masked[header.end():]
    # A partial view with aspects is outside this lexical subset: PRIVATE WITH
    # must not masquerade as the private-part boundary and conceal later names.
    if re.search(r'\bprivate\s+with\b',public,re.I):return False
    # Unlike a line-start-only boundary, this also sees same-line PRIVATE.
    # Public partial views end in "private;" and do not start the private part.
    boundary=re.search(r'\bprivate\b(?!\s*;)',public,re.I)
    if boundary is not None:public=public[:boundary.start()]
    else:
        closing=re.search(r'\bend\s+(?:'+QNAME+r'\s*)?;\s*$',public,re.I)
        if closing is None:return False
        public=public[:closing.start()]
    if re.search(r'\b(package|generic|task|protected|begin|declare|renames)\b',public,re.I):
        return False
    # Derived types can implicitly inherit enumeration literals/subprograms;
    # their defining names are not necessarily present in this source unit.
    if re.search(r'\bis\s+new\b',public,re.I):return False
    short=key.rsplit('.',1)[-1]
    for use in re.finditer(r'\b'+re.escape(short)+r'\b',public,re.I):
        before=public[:use.start()].rstrip()
        after=public[use.end():].lstrip()
        if not after.startswith('.') and not before.endswith('.'):
            return False
    return re.search(r'\b(?:type|subtype)\s+'+re.escape(selector)+r'\b',public,re.I) is not None


def resolve(name: str, pkg: Package, source: dict[str, Package],
            targets: dict[str, tuple[Path,str]], external: dict[str,str]) -> tuple[str, str] | None:
    """Conservative resolution: never choose a destination from name alone."""
    token=name.lower(); key=pkg.name.lower()
    if token in STANDARD or token in KEYWORDS: return None
    if '.' in token:
        owner=token.rsplit('.',1)[0]
        if token.count('.')==1 and owner==key.rsplit('.',1)[-1] and owner!=key:
            # Sole candidate: this source package, never a suffix search or an
            # external fallback. Existing full-owner resolution stays below.
            identity=key+'.'+token.split('.')[1]
            if (source.get(key) is pkg and token.split('.')[1] in pkg.public_types
                    and identity in targets and _current_package_prefix(key,token.split('.')[1],pkg.source)):
                return identity,'local'
            return None
        if owner!=key and not key.startswith(owner+'.') and owner not in pkg.imports:
            return None
        if token in targets: return token, 'local'
        exact=next((k for k in external if k.lower()==token),None)
        if exact is None:return None
        # A source-owned package never acquires imported or aliased type owners.
        if owner in source:return None
        # Decline qualified prefixes shadowed in the current public scope.
        prefix=token.split('.')[0]
        if any(d.name.lower()==prefix for d in pkg.declarations):return None
        if not external_visible(owner,pkg):return None
        return exact,'external'
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
    from .inventory import mask_ada
    masked=mask_ada(code)
    matches=list(TYPE_MARK.finditer(masked))
    base=SUBTYPE_BASE.match(masked)
    if base is not None:matches.append(base)
    for m in sorted(matches,key=lambda m:m.start(1)):
        word=m[1]
        if word.lower() not in KEYWORDS and word.lower() not in STANDARD:
            positions.append((m.start(1),m.end(1),word))
    return positions


def _current_type_context(text: str, start: int, end: int) -> bool:
    """Additional fail-closed context guard for newly eligible relative names."""
    from .inventory import mask_ada
    masked=mask_ada(text)
    if re.match(r"\s*'",masked[end:]):return False
    # A supported type mark precedes its own default/constraint. A later mark
    # inside an expression, aspect or default cannot acquire this new authority.
    segment=masked[:start].rsplit(';',1)[-1]
    if ':=' in segment or '=>' in segment or re.search(r'\bwith\b',segment,re.I):
        return False
    if re.search(r'\b(?:range|digits|delta)\b',segment,re.I):return False
    # A colon must directly follow a defining-name list. In particular reject
    # quantified expressions, even if an extractor recognizes their colon.
    colon=re.search(r'('+IDENT+r'(?:\s*,\s*'+IDENT+r')*)\s*:\s*'
                    r'(?:(?:not|null|aliased|in|out|access|constant)\s+)*$',segment,re.I)
    if colon is not None:
        prefix=segment[:colon.start()].rstrip()
        return not prefix or prefix.endswith('(') or re.search(r'\brecord$',prefix,re.I) is not None
    # The other existing contexts (return, array element, access/derived type,
    # ordinary subtype base) must remain declaration contexts, not expressions.
    return re.match(r'^\s*(?:type|subtype|function|procedure|overriding|not)\b',masked,re.I) is not None


def linked(raw: str, pkg: Package, source: dict[str, Package],
           native: NativeSite, targets: dict[str,tuple[Path,str]], config: Config,
           instance_targets=None):
    require('<' not in raw,"type linking requires raw GNATdoc snippets")
    text,starts,ends=escaped_offsets(raw)
    inserts=[]
    from .inventory import mask_ada
    base=SUBTYPE_BASE.match(mask_ada(text))
    for a,b,name in type_positions(text):
        target_attribute=''
        relative=(name.count('.')==1 and
                  name.split('.')[0].lower()==pkg.name.rsplit('.',1)[-1].lower() and
                  name.rsplit('.',1)[0].lower()!=pkg.name.lower())
        if relative and not _current_type_context(text,a,b):continue
        if base is not None and (a,b)==base.span(1):
            # Reuse the existing flat public-scope guard also for local bases.
            # A snippet alone must not newly authorize a nested/aliased scope.
            if not external_visible(pkg.name.lower(),pkg):continue
        target=resolve(name,pkg,source,targets,config.externals)
        if target is None:
            from .instance_references import resolve as instance_resolve
            explanation=instance_resolve(name,text,a,b,pkg,source,instance_targets)
            if explanation is None:continue
            identity,url=explanation.identity,explanation.href
        else:
            identity,kind=target
            if kind=='external':
                url=config.externals[identity]
                if config.external_type_target == '_top':target_attribute=' target="_top"'
            else:
                target_page,anchor=targets[identity]
                url=target_page.name+'#'+anchor
        src_a,src_b=starts[a],ends[b-1]
        encoded=raw[src_a:src_b]
        inserts.append((src_a,src_b,
                        f'<a class="type-reference" href="{html.escape(url,quote=True)}" '
                        f'data-type="{identity}"{target_attribute}>{encoded}</a>'))
    # Only accept nonoverlapping type-mark spans.
    used=set()
    for start,end,_ in inserts:
        require(not any(i in used for i in range(start,end)),"overlapping type positions")
        used.update(range(start,end))
    for a,b,markup in reversed(inserts):raw=raw[:a]+markup+raw[b:]
    require(plain(raw)==text,"type linker changed escaped original declaration")
    return raw,len(inserts)


def transform_page(original: str, pkg: Package, source: dict[str,Package],
                   native: NativeSite, targets, config:Config, instance_targets=None):
    counts={'links':0,'snippets':0}
    def render(m):
        raw=m[2];before=plain(raw)
        if config.type_links:
            raw,linked_count=linked(raw,pkg,source,native,targets,config,instance_targets)
            counts['links']+=linked_count
        if config.highlight:raw=highlighted(raw)
        require(plain(raw)==before,"snippet not text preserving")
        counts['snippets']+=1
        return m[1]+raw+m[3]
    return CODE.sub(render,original),counts
