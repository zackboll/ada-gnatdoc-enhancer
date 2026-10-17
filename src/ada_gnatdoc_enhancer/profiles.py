"""Narrow, lexical source/native projections for GNATdoc 26.0.0.

These are presentation equivalences, not Ada semantic equivalences. Hidden
source text is never evidence of native rendering. See the compatibility doc.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .errors import EnhancementError
from .inventory import mask_ada, normalized

TOKEN = re.compile(
    r'(?P<space>\s+)|(?P<comment>--[^\n]*)|'
    r'(?P<string>"(?:[^"\n]|"")*")|(?P<character>\'[^\n]\')|'
    r'[A-Za-z][A-Za-z0-9_]*|'
    r'[0-9][0-9_]*(?:\#[0-9A-Fa-f_.]+\#|\.(?!\.)[0-9_]+)?(?:[Ee][+-]?[0-9_]+)?|'
    r':=|=>|\.\.|\*\*|/=|<=|>=|<>|[&+*/=<>:;,.()|\-\']|…')
IDENTIFIER = re.compile(r'[a-z](?:[a-z0-9]|_[a-z0-9])*\Z')
# Reserved words cannot stand in for a name or enumeration literal.
RESERVED = frozenset('''abort abs abstract accept access aliased all and array at begin body
case constant declare delay delta digits do else elsif end entry exception exit for
function generic goto if in interface is limited loop mod new not null of or others
out overriding package parallel pragma private procedure protected raise range record
rem renames requeue return reverse select separate some subtype synchronized tagged
task terminate then type until use when while with xor'''.split())


def tokens(text: str) -> tuple[str, ...]:
    result=[];pos=0;depth=0
    while pos<len(text):
        match=TOKEN.match(text,pos)
        if match is None:
            raise EnhancementError('unsupported declaration-profile lexical syntax')
        pos=match.end()
        if match.lastgroup in ('space','comment'):continue
        token=match[0]
        if match.lastgroup not in ('string','character'):token=token.lower()
        if token=='(':depth+=1
        elif token==')':
            depth-=1
            if depth<0:raise EnhancementError('unbalanced declaration-profile parentheses')
        result.append(token)
    if depth:raise EnhancementError('unbalanced declaration-profile parentheses')
    return tuple(result)


def identifier(token):
    return IDENTIFIER.fullmatch(token) is not None and token not in RESERVED


def closing(items, start):
    depth=0
    for i in range(start,len(items)):
        if items[i]=='(':depth+=1
        elif items[i]==')':
            depth-=1
            if depth==0:return i
    raise EnhancementError('unbalanced declaration-profile parentheses')


def type_mark(items):
    return bool(items) and all(identifier(t) if i%2==0 else t=='.'
                               for i,t in enumerate(items)) and len(items)%2==1


def parameters(items):
    """Named formals, optional modes, qualified type marks and complete defaults."""
    groups=[];start=0;depth=0
    for i,t in enumerate(items):
        if t=='(':depth+=1
        elif t==')':depth-=1
        elif t==';' and depth==0:groups.append(items[start:i]);start=i+1
    groups.append(items[start:])
    for group in groups:
        if ':' not in group:return False
        colon=group.index(':');names=group[:colon]
        if not names or len(names)%2!=1 or not all(
                identifier(t) if i%2==0 else t==',' for i,t in enumerate(names)):return False
        rest=group[colon+1:]
        for mode in (('in','out'),('in',),('out',)):
            if rest[:len(mode)]==mode:rest=rest[len(mode):];break
        if ':=' in rest:
            at=rest.index(':=');default=rest[at+1:];rest=rest[:at]
            if not default or any(t in (';',':=','declare','begin','end','…') for t in default):return False
        if not type_mark(rest):return False
    return True


def expression_profile(items):
    """Return the entire callable profile only for a supported expression body."""
    at=0
    if items[:2]==('not','overriding'):at=2
    elif items[:1]==('overriding',):at=1
    if items[at:at+1]!=('function',):return None
    at+=1
    if at>=len(items) or not identifier(items[at]):return None
    at+=1
    if items[at:at+1]==('(',):
        end=closing(items,at)
        if not parameters(items[at+1:end]):return None
        at=end+1
    if items[at:at+1]!=('return',):return None
    at+=1;return_start=at
    while at<len(items) and items[at]!='is':at+=1
    if not type_mark(items[return_start:at]) or items[at:at+2]!=('is','('):return None
    end=closing(items,at+1)
    body=items[at+2:end]
    # Deliberately exclude declarative expressions and aspect-bearing bodies.
    # Semicolons in quoted tokens are harmless; free semicolons are not.
    if not body or any(t in (';','declare','begin','end','function','procedure','is','…') for t in body):return None
    if items[end+1:]!=(';',):return None
    return items[:at]


def enumeration(items, *, abbreviated=False):
    if len(items)<7 or items[0]!='type' or not identifier(items[1]) or items[2:4]!=('is','('):return None
    if items[-2:]!=(')',';'):return None
    members=items[4:-2]
    if not members or len(members)%2!=1:return None
    literals=[]
    for i,t in enumerate(members):
        if i%2:
            if t!=',':return None
        elif identifier(t) or (len(t)==3 and t[0]==t[-1]=="'") or (abbreviated and t=='…'):
            literals.append(t)
        else:return None
    if len(set(literals))!=len(literals):return None
    return tuple(literals)


def callable_profile(items):
    """Consume a complete, simple callable spec; return its suffix boundary."""
    if len(items)<2 or items[0] not in ('procedure','function') or not identifier(items[1]):return None
    at=2
    if items[at:at+1]==('(',):
        end=closing(items,at)
        if not parameters(items[at+1:end]):return None
        at=end+1
    if items[0]=='function':
        if items[at:at+1]!=('return',):return None
        start=at+1;at=start
        while at<len(items) and (identifier(items[at]) or items[at]=='.'):at+=1
        if not type_mark(items[start:at]):return None
    return at


def renaming_profile(items, declarations):
    """Only a unique direct, non-renaming target in a verified flat package.

    Reject even distinguishable overloads and renaming chains for now. This also
    excludes cycles, cross-package names, generic and operator renamings.
    """
    at=callable_profile(items)
    if at is None or len(items)!=at+3 or items[at]!='renames' or items[-1]!=';':return None
    target=items[at+1]
    if not identifier(target) or target==items[1]:return None
    candidates=[]
    for declaration in declarations:
        owned=tokens(declaration)
        if len(owned)>1 and owned[1]==target:candidates.append(owned)
    if len(candidates)!=1:return None
    owned=candidates[0];end=callable_profile(owned)
    if end is None or owned[end:]!=(';',):return None
    # Only the defining name may differ; every other profile token must agree.
    if owned[:1]+owned[2:end]!=items[:1]+items[2:at]:return None
    return items[:at],target


def record_convention_profile(items):
    """Simple component-only records; exactly one established Convention aspect."""
    if len(items)<12 or items[:1]!=('type',) or not identifier(items[1]):return None
    if items[2:4]!=('is','record'):return None
    suffix=('end','record','with','convention','=>','c',';')
    if items[-7:]!=suffix:return None
    components=items[4:-7]
    if not components or components[-1]!=';':return None
    names=set();start=0
    for at,token in enumerate(components):
        if token!=';':continue
        group=components[start:at];start=at+1
        if ':' not in group:return None
        colon=group.index(':');fields=group[:colon]
        if not fields or len(fields)%2!=1 or not all(
                identifier(t) if i%2==0 else t==',' for i,t in enumerate(fields)):return None
        if not type_mark(group[colon+1:]):return None
        for name in fields[::2]:
            if name in names:return None
            names.add(name)
    return items[:-5]+(';',)


@dataclass(frozen=True)
class Projection:
    rule: str
    hidden_literals: int = 0
    omitted_source_tokens: tuple[str, ...] = ()
    target_name: str | None = None


@lru_cache(maxsize=8192)
def reconcile(source: str, native: str, declarations: tuple[str, ...] = ()) -> Projection | None:
    """Exact identity stays the default. No arbitrary prefixes or wildcards."""
    expected=normalized(source).removesuffix(' ;').strip()
    # Preserve the existing supported aspect omissions, but ONLY at top level.
    # Strings/default expressions containing WITH PRE are not aspect clauses.
    masked=mask_ada(source)
    depth=0;cut=None
    for match in re.finditer(r'\(|\)|\bwith\s+(?:pre|post|global|depends)\b',masked,re.I):
        if match[0]=='(':depth+=1
        elif match[0]==')':depth-=1
        elif depth==0:cut=match.start();break
    if cut is not None:expected=normalized(source[:cut]).strip()
    if normalized(native).removesuffix(' ;').strip()==expected:return Projection('exact')
    try:
        owned=tokens(source);rendered=tokens(native)
    except EnhancementError:
        return None
    try:
        renaming=renaming_profile(owned,declarations)
    except EnhancementError:
        renaming=None
    if renaming is not None and rendered==renaming[0]:
        return Projection('subprogram-renaming-profile',omitted_source_tokens=('renames',renaming[1],';'),
                          target_name=renaming[1])
    record=record_convention_profile(owned)
    if record is not None and rendered==record:
        return Projection('record-convention-aspect',omitted_source_tokens=('with','convention','=>','c'))
    profile=expression_profile(owned)
    if profile is not None and rendered==profile:return Projection('expression-function-profile')
    literals=enumeration(owned)
    if literals is not None and '…' in rendered:
        visible=enumeration(rendered,abbreviated=True)
        if (len(literals)>10 and visible==literals[:8]+('…',)+literals[-1:]
                and owned[:4]==rendered[:4]):
            return Projection('enumeration-first-eight-last',len(literals)-9)
    return None