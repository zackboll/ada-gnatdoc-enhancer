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
        closer=re.search(r'\bend\s+record\s*;',masked[start:],re.I)
        if closer is None:raise EnhancementError('unterminated record type')
        return start+closer.end()
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
    declarations: list[Declaration] = []
    for kind, pattern in (("type", TYPE), ("call", SUBPROGRAM)):
        for match in pattern.finditer(current):
            # Nested declarations not modeled: if before a top-level keyword we
            # see nested generic/package/record, the resolver must decline it.
            begin = match.start()
            end = last_semicolon(current, match.start())
            sig = contents[begin:end].strip()
            ident = match[2]
            actual_kind = match[1].lower() if kind == "type" else match[1].lower()
            line = source.count('\n', 0, header.end() + begin) + 1
            declarations.append(Declaration(actual_kind, ident, sig, line))
    declarations.sort(key=lambda x: x.line)
    type_symbols: dict[str, Declaration] = {}
    for decl in declarations:
        if decl.kind not in ("type", "subtype"): continue
        key = decl.name.lower()
        require(key not in type_symbols, f"duplicate public type identity: {name}.{decl.name}")
        type_symbols[key] = decl
    return Package(name, path, frozenset(imports), frozenset(uses), type_symbols, declarations, source)


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
