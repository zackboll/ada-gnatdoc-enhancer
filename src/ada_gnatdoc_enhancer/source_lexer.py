"""Canonical executable-ada-catalog-v1 display lexer.

Adapted from MEL Bridge docs/tools/ada_examples.py at
039bd4f05be969f0f224747728dfbae5305ee29b (Apache-2.0).
Tokenization is display-only, never compiler or execution evidence.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass

KEYWORDS = frozenset("""abort abs abstract accept access aliased all and array at
begin body case constant declare delay delta digits do else elsif end entry
exception exit for function generic goto if in interface is limited loop mod new
not null of or others out overriding package parallel pragma private procedure
protected raise range record rem renames requeue return reverse select separate
some subtype synchronized tagged task terminate then type until use when while
with xor""".split())
PATTERN = re.compile(
    r'(?P<space>\s+)|(?P<comment>--[^\r\n]*)|'
    r'(?P<string>"(?:""|[^"\r\n])*")|'
    r"(?P<character>'[^\r\n]')|(?P<attribute>'[A-Za-z][A-Za-z0-9_]*)|"
    r'(?P<number>[0-9](?:_?[0-9])*(?:#[0-9A-Fa-f](?:_?[0-9A-Fa-f])*'
    r'(?:\.[0-9A-Fa-f](?:_?[0-9A-Fa-f])*)?#|(?:\.[0-9](?:_?[0-9])*)?)'
    r'(?:[Ee][+-]?[0-9](?:_?[0-9])*)?)|'
    r'(?P<identifier>[^\W\d_](?:\w)*)|'
    r'(?P<operator>:=|=>|\.\.|\*\*|/=|<=|>=|<<|>>|<>|[&()*+,\-./:;<=>\[\]|\'])|'
    r'(?P<plain>.)', re.UNICODE)


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: int
    end: int


def tokenize(text):
    tokens = []
    cursor, previous = 0, None
    while cursor < len(text):
        match = PATTERN.match(text, cursor)
        kind = match.lastgroup
        # A tick after a name/expression is an attribute/qualification tick,
        # not the start of a character literal (e.g. Character'('A')).
        if kind == "character" and previous is not None and (
                previous.kind in {"identifier", "attribute", "number", "string", "character"}
                or previous.text in {")", "]"}):
            tokens.append(Token("operator", "'", cursor, cursor + 1))
            previous = tokens[-1]
            cursor += 1
            continue
        if kind == "identifier" and match[0].lower() in KEYWORDS:
            kind = "keyword"
        tokens.append(Token(kind, match[0], match.start(), match.end()))
        if kind not in {"space", "comment"}:
            previous = tokens[-1]
        cursor = match.end()
    if "".join(t.text for t in tokens) != text:
        raise ValueError("Ada lexer did not preserve source")
    return tokens


def chains(tokens, start, stop):
    """Maximal selected names; never resume midway through a selected chain."""
    i = start
    while i < stop:
        if tokens[i].kind != "identifier" or (i and tokens[i - 1].text == "."):
            i += 1
            continue
        end = i + 1
        while end + 1 < stop and tokens[end].text == "." and tokens[end + 1].kind == "identifier":
            end += 2
        yield i, end, "".join(t.text.lower() for t in tokens[i:end])
        i = end


def annotate(text, occurrences=()):
    """One canonical, balanced serialization; no generated metadata is trusted."""
    starts = {r["start"]: r for r in occurrences}
    ends = {r["end"]: r for r in occurrences}
    if len(starts) != len(occurrences) or len(ends) != len(occurrences):
        raise ValueError("duplicate example link span")
    output = []
    for token in tokenize(text):
        if token.start in starts:
            output.append('<a class="ada-reference" href="' + html.escape(starts[token.start]["href"], quote=True) + '">')
        escaped = html.escape(token.text)
        if token.kind not in {"space", "identifier", "plain"}:
            escaped = '<span class="ada-' + token.kind + '">' + escaped + '</span>'
        output.append(escaped)
        if token.end in ends:
            output.append('</a>')
    # Chromium otherwise drops the final source newline from Selection.toString.
    # This empty inline box contributes no text (including to accessible text).
    return "".join(output) + '<span class="ada-source-end" aria-hidden="true"></span>'
