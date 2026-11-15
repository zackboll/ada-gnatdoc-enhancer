"""Conservative source-owned public library-unit and declaration inventory.

A lexical scanner is NOT a complete Ada name resolver. Unsupported scopes must
remain unlinked rather than being guessed. GNATdoc-to-source declaration identity
is checked a second time against the actual rendered signature.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .errors import EnhancementError
from .util import IDENT, QNAME, require

HEADER = re.compile(r"(?im)^\s*(private\s+)?package\s+(" + QNAME + r")\s+(is\b|renames\b)")
SUBPROGRAM = re.compile(r"(?im)^\s*(?:overriding\s+|not\s+overriding\s+)?(function|procedure)\s+("+IDENT+r")\b")
TYPE = re.compile(r"(?im)^\s*(type|subtype)\s+(" + IDENT + r")\b")


def mask_ada(text: str, comments=True) -> str:
    """Mask quoted literals and comments while preserving offsets and newlines."""
    out = list(text)
    i = 0
    while i < len(text):
        if text[i:i+2] == '--':
            end = text.find('\n', i)
            if end < 0:
                end = len(text)
            if comments:
                for j in range(i, end): out[j] = ' '
            i = end
        elif text[i] == '"':
            start = i
            i += 1
            while i < len(text):
                if text[i] == '"':
                    if text[i:i+2] == '""': i += 2; continue
                    i += 1
                    break
                i += 1
            for j in range(start, i):
                if text[j] != '\n': out[j] = ' '
        elif text[i] == "'" and i+2 < len(text) and text[i+2] == "'":
            for j in range(i, i+3): out[j] = ' '
            i += 3
        else:
            i += 1
    return ''.join(out)


def normalized(text: str) -> str:
    """Stable Ada identity with string/character literal bytes preserved."""
    # Strip comments without losing literals or differences in actual values.
    result=[];i=0;quoted=False
    while i<len(text):
        c=text[i]
        if c=='"':
            result.append(c)
            if quoted and i+1<len(text) and text[i+1]=='"':
                result.append('"');i+=2;continue
            quoted=not quoted;i+=1;continue
        if not quoted and text[i:i+2]=='--':
            end=text.find('\n',i)
            if end<0:break
            result.append(' ');i=end;continue
        result.append(c);i+=1
    code=''.join(result)
    terms=re.findall(r'"(?:""|[^"])*"|\'[^\n]\'|[A-Za-z][A-Za-z0-9_]*|[0-9][A-Za-z0-9_#.]*(?:[Ee][+-]?[0-9]+)?|:=|=>|/=|<=|>=|\.\.|\S',code)
    return ' '.join(t if t.startswith(('"',"'")) else t.lower() for t in terms)


def last_semicolon(masked: str, start: int) -> int:
    # A top-level record type contains semicolons, so its declaration ends at
    # END RECORD rather than the first component's semicolon.
    beginning=masked[start:]
    record=re.search(r'\bis\s+(?:tagged\s+|limited\s+)*record\b',beginning,re.I)
    before_first=masked.find(';',start)
    if record and (before_first<0 or start+record.start()<before_first):
        closer=re.search(r'\bend\s+record\b',masked[start:],re.I)
        if closer is None:raise EnhancementError('unterminated record type')
        # A record may carry aspects after END RECORD. Scan only the suffix
        # for its terminating semicolon; component semicolons are not endings.
        return last_semicolon(masked, start+closer.end())
    depth=0
    for pos in range(start,len(masked)):
        c=masked[pos]
        if c=='(':depth+=1
        elif c==')':depth=max(0,depth-1)
        elif c==';' and depth==0:return pos+1
    raise EnhancementError('incomplete Ada declaration')


def visible_prefix(raw: str, start: int) -> str:
    text = raw[start:]
    masked = mask_ada(text)
    cut = re.search(r"(?im)^\s*private\s*$", masked)
    return text[:cut.start()] if cut else text


def public_declarations(raw: str) -> list[Declaration]:
    """Inventory direct visible declarations, never descendants of a scope.

    This is a declaration-boundary walker, not an Ada parser/name resolver.
    Literals/comments are masked with offsets intact. Nested specifications are
    walked only to establish their closing boundary; generic formals/templates
    and bodies are never promoted to the enclosing package. Unknown executable
    structure is rejected, not recovered by searching for a convenient END.
    Native profile reconciliation remains a separate, mandatory authority.
    """
    masked = mask_ada(raw)
    header = HEADER.search(masked)
    body_header = re.search(r'(?im)^\s*(?:package\s+body|separate\b)', masked)
    if body_header and (header is None or body_header.start() < header.start()):
        return []
    if header is None or header[3].lower() != 'is':
        return []
    if re.match(r'\s*new\b', masked[header.end():], re.I):
        return []
    lex = list(re.finditer(r'[A-Za-z][A-Za-z0-9_]*|:=|=>|<>|\S', masked))
    words = [m[0].lower() for m in lex]
    size = len(words)
    result = []
    historical_starts = {header.end() + m.end(): header.end() + m.start()
                         for pattern in (TYPE, SUBPROGRAM)
                         for m in pattern.finditer(masked[header.end():])}

    def need(condition):
        require(condition, 'unsupported or unbalanced Ada declaration scope')

    def statement(at):
        """End of one declaration, including record components and aspects."""
        parens = records = 0
        for i in range(at, size):
            word = words[i]
            if word == '(': parens += 1
            elif word == ')':
                parens -= 1; need(parens >= 0)
            elif not parens:
                if word == 'record' and (i == 0 or words[i-1] not in ('end', 'null')):
                    records += 1
                elif word == 'end' and words[i+1:i+2] == ['record']:
                    records -= 1; need(records >= 0)
                elif word == ';' and not records:
                    return i + 1
                elif word in ('begin', 'declare'):
                    need(False)
        need(False)

    def marker(at, end):
        depth = 0
        for i in range(at, end):
            if words[i] == '(': depth += 1
            elif words[i] == ')': depth -= 1
            elif not depth and words[i] in ('is', 'renames', ';'):
                return i
        need(False)

    def close(at, name):
        need(words[at:at+1] == ['end'])
        at += 1
        if words[at:at+1] != [';']:
            parts = name.lower().split('.')
            expected = [item for part in parts for item in (part, '.')][:-1]
            need(words[at:at+len(expected)] == expected)
            at += len(expected)
        need(words[at:at+1] == [';'])
        return at + 1

    def executable(at, name):
        # Only structured statements with unambiguous keyword closers. A bare
        # block, DECLARE expression, accept body, etc. fails closed for now.
        stack = []
        i = at
        while i < size:
            word = words[i]
            if word == 'end':
                if not stack:
                    return close(i, name)
                need(words[i+1:i+2] == [stack.pop()])
                i += 2
                continue
            if word in ('if', 'case', 'loop', 'select'):
                stack.append(word)
            elif word in ('begin', 'declare', 'accept'):
                need(False)
            i += 1
        need(False)

    def declaration(at, visible):
        start = at
        word = words[at]
        if word == 'generic':
            at += 1
            # WITH subprogram/package clauses belong to the formal part. Only
            # an unprefixed package/subprogram starts the generic template.
            while at < size and words[at] not in ('package', 'function', 'procedure'):
                at = statement(at)
            need(at < size)
            return declaration(at, False)
        if words[at:at+2] == ['not', 'overriding']: at += 2
        elif word == 'overriding': at += 1
        word = words[at]
        if word in ('package', 'task', 'protected', 'function', 'procedure'):
            kind = word
            if kind == 'function' and words[at+1:at+2] == ['(']:
                # Quoted operators are outside the identifier-only contract,
                # but cannot suppress unrelated direct declarations.
                return statement(start)
            at += 1
            body = words[at:at+1] == ['body']
            if words[at:at+1] in (['body'], ['type']): at += 1
            need(at < size)
            name = words[at]; at += 1
            while words[at:at+1] == ['.']:
                need(at+1 < size)
                name += '.' + words[at+1]; at += 2
            boundary = marker(at, size)
            value = words[boundary]
            if value == 'is' and words[boundary+1:boundary+2] not in (
                    ['new'], ['('], ['null'], ['abstract'], ['separate']):
                # A scope's members are never direct enclosing declarations.
                return region(boundary+1, name, False, body or kind in ('function', 'procedure'))
            end = statement(start)
            instance = value == 'is' and words[boundary+1:boundary+2] == ['new']
            if visible and kind in ('function', 'procedure') and not body and not instance:
                admit(start, end, kind, name)
            return end
        end = statement(start)
        if visible and word in ('type', 'subtype'):
            need(at+1 < size)
            admit(start, end, word, words[at+1])
        return end

    def admit(start, end, kind, name):
        begin = lex[start].start(); finish = lex[end-1].end()
        # Take spelling/signature verbatim from source, not the masked tokens.
        spelling = re.match(r'(?:not\s+overriding\s+|overriding\s+)?' + kind +
                            r'\s+(' + IDENT + r')', masked[begin:], re.I)
        need(spelling is not None)
        # Retain the historical source inventory's associated leading comments
        # and blank lines (and therefore existing search text/profile evidence).
        begin = historical_starts.get(begin + spelling.end(), begin)
        result.append(Declaration(kind, spelling[1], raw[begin:finish].strip(),
                                  raw.count('\n', 0, begin) + 1))

    def region(at, name, visible, body=False):
        while at < size:
            word = words[at]
            if word == 'end': return close(at, name)
            if word == 'private':
                if visible: return size
                visible = False; at += 1
            elif word == 'begin':
                need(body)
                return executable(at+1, name)
            else:
                at = declaration(at, visible)
        need(False)

    start = next((i for i, m in enumerate(lex) if m.start() >= header.end()), size)
    try:
        end = region(start, header[2], True)
        need(end == size)
    except EnhancementError:
        # No recovery guesses: even declarations collected before an ambiguous
        # boundary cannot authorize links from this unit.
        return []
    return result


@dataclass(frozen=True)
class Declaration:
    kind: str
    name: str
    signature: str
    line: int


@dataclass
class Package:
    name: str
    path: Path
    imports: frozenset[str]
    uses: frozenset[str]
    public_types: dict[str, Declaration]
    declarations: list[Declaration]
    source: str


def _one(path: Path) -> Package | None:
    source = path.read_text(encoding='utf-8')
    masked = mask_ada(source)
    header = HEADER.search(masked)
    body_header = re.search(r'(?im)^\s*(?:package\s+body|separate\b)', masked)
    if body_header and (header is None or body_header.start() < header.start()):
        return None
    if not header:
        # Ignored only for explicitly private library packages and Ada helper units.
        if re.search(r'(?im)^\s*(?:package\s+body|separate\b)', masked): return None
        raise EnhancementError(f"unsupported Ada library-unit header: {path}")
    if header[1]: return None
    name = header[2]
    context = masked[:header.start()]
    imports = set()
    for clause in re.finditer(r"(?ims)^\s*(?:private\s+|limited\s+)?with\s+([^;]+);", context):
        imports.update(v.strip().lower() for v in clause[1].split(','))
    contents = visible_prefix(source, header.end())
    current = mask_ada(contents)
    uses = set()
    for clause in re.finditer(r"(?im)^\s*use\s+(?!type\b)([^;]+);", current):
        uses.update(v.strip().lower() for v in clause[1].split(','))
    declarations = public_declarations(source)
    type_symbols: dict[str, Declaration] = {}
    for decl in declarations:
        if decl.kind not in ("type", "subtype"): continue
        key = decl.name.lower()
        require(key not in type_symbols, f"duplicate public type identity: {name}.{decl.name}")
        type_symbols[key] = decl
    return Package(name, path, frozenset(imports), frozenset(uses), type_symbols, declarations, source)


def direct_callables(package: Package) -> tuple[str, ...]:
    """Target evidence only in an ordinary, flat source-owned public package.

    The general inventory is not a scope resolver. Decline the new renaming
    projection entirely when nested/generic/executable scopes could interfere.
    """
    masked=mask_ada(package.source)
    header=HEADER.search(masked)
    if header is None or header[3].lower()!='is':return ()
    if re.search(r'\bgeneric\b',masked[:header.start()],re.I):return ()
    public=mask_ada(visible_prefix(package.source,header.end()))
    if re.search(r'\b(package|generic|task|protected|begin|declare)\b',public,re.I):return ()
    return tuple(d.signature for d in package.declarations if d.kind in ('procedure','function'))


def packages(config: Config) -> dict[str, Package]:
    results = {}
    for folder in config.sources:
        for path in sorted((config.root / folder).rglob('*.ads')):
            require(not path.is_symlink(), f"symlink Ada source: {path}")
            pkg = _one(path)
            if pkg is None: continue
            key = pkg.name.lower()
            require(key not in results, f"duplicate Ada public package: {pkg.name}")
            results[key] = pkg
    require(results, "no public Ada packages discovered")
    if config.expected_packages:
        expected = {p.lower() for p in config.expected_packages}
        require(expected == set(results), f"public package inventory mismatch: {sorted(expected ^ set(results))}")
    return results
