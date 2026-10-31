"""Static example presentation; lexical evidence is deliberately not Ada semantics.

Destinations are reconstructed from public source and complete native profiles.
No manifest, HTML attribute, example annotation or URL can grant a destination.
The resolver declines all overloads and prefixed object calls. Local declarations
conservatively suppress a name throughout the fence (including before its scope).
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from .destinations import source_destinations
from .inventory import mask_ada, packages
from .syntax import LEXEME, external_visible, highlighted
from .util import IDENT, QNAME, require

STYLESHEET = 'assets/gnatdoc-examples.css'
NAME = re.compile(r'\b' + IDENT + r'(?:\s*\.\s*' + IDENT + r')*\b')


class Resolver:
    def __init__(self, config, native):
        self.symbols = {}
        source = packages(config)
        self.owners = set(source)
        for owner, destinations in source_destinations(config, native, source).items():
            for destination in destinations:
                key = owner + '.' + destination.declaration.name.lower()
                self.symbols.setdefault(key, []).append(destination)
        self.supported = {owner for owner, pkg in source.items() if external_visible(owner, pkg)}

    def positions(self, text):
        masked = mask_ada(text)
        for token in LEXEME.finditer(text):
            if token.lastgroup == 'attribute':
                masked = masked[:token.start()] + ' ' * len(token[0]) + masked[token.end():]
        # A whole-example deny set deliberately over-approximates local scope.
        shadows = set()
        for match in re.finditer(r'\b(' + IDENT + r'(?:\s*,\s*' + IDENT + r')*)\s*:(?!=)', masked):
            shadows.update(re.findall(IDENT, match[1].lower()))
        for match in re.finditer(r'\b(?:procedure|function|type|subtype|package|entry|task|protected)\s+(?:body\s+|type\s+)?(' + IDENT + r')', masked, re.I):
            shadows.add(match[1].lower())
        for match in re.finditer(r'\bfor\s+(' + IDENT + r')\s+(?:in|of)\b', masked, re.I):
            shadows.add(match[1].lower())
        for match in re.finditer(r'\bis\s*\(([^()]*)\)', masked, re.I):
            shadows.update(re.findall(IDENT, match[1].lower()))
        uses = set()
        use_positions = {}
        for match in re.finditer(r'\buse\s+(' + QNAME + r'(?:\s*,\s*' + QNAME + r')*)\s*;', masked, re.I):
            for value in match[1].split(','):
                owner = value.strip().lower(); uses.add(owner)
                use_positions.setdefault(owner, match.end())
        for match in NAME.finditer(masked):
            spelling = text[match.start():match.end()]
            # Masked literals/comments cannot become part of a selected name.
            if not NAME.fullmatch(spelling):
                continue
            name = re.sub(r'\s+', '', spelling).lower()
            if name.split('.')[0] in shadows:
                continue
            before, after = masked[:match.start()], masked[match.end():]
            if '.' in name:
                candidates = self.symbols.get(name, [])
            else:
                # Multiple use-visible namespaces (including inherited and
                # enum declarations outside the inventory) need Ada semantics.
                if len(uses) != 1 or not uses <= self.owners:
                    continue
                use_end = use_positions[next(iter(uses))]
                if use_end > match.start() or re.search(r'\bend\b', masked[use_end:match.start()], re.I):
                    continue
                # Implicit inherited declarations and generic/package scopes
                # are not represented by the flat example symbol inventory.
                if re.search(r'\b(?:generic|package|new)\b|\buse\s+(?:all\s+)?type\b', masked, re.I):
                    continue
                candidates = [d for key, group in self.symbols.items() for d in group
                              if key.rpartition('.')[0] in uses and key.rpartition('.')[2] == name]
            if len(candidates) != 1:
                continue
            destination = candidates[0]
            if destination.package.lower() not in self.supported or destination.total != 1:
                continue
            if destination.declaration.kind in ('type', 'subtype'):
                # Only supported type-mark contexts, never declaration names,
                # record selectors, named arguments or arbitrary expressions.
                if not re.search(r'(?:\breturn|\bof|\bnew|\bis|:\s*(?:(?:constant|aliased|in|out|not|null|access)\s+)*)\s*$', before, re.I):
                    continue
            elif destination.declaration.kind not in ('function', 'procedure') or not re.match(r'\s*\(', after):
                continue
            yield match.start(), match.end(), destination.href


def code(text, resolver=None, *, landing=False):
    """Escape once and reuse the declaration lexer; retain every source character."""
    positions = list(resolver.positions(text)) if resolver else []
    parts, end = [], 0
    for start, stop, destination in positions:
        parts.append(highlighted(html.escape(text[end:start], quote=False)))
        prefix = 'api/' if landing else '../api/'
        parts.append('<a class="ada-api-reference" href="' + html.escape(prefix + destination, quote=True) + '">' +
                     highlighted(html.escape(text[start:stop], quote=False)) + '</a>')
        end = stop
    parts.append(highlighted(html.escape(text[end:], quote=False)))
    if text.endswith('\n'):
        # Chromium otherwise omits the final LF from native selection/clipboard
        # in preformatted blocks. An empty line box preserves it without adding
        # a single character to textContent or introducing executable behavior.
        parts.append('<span class="ada-example-end"></span>')
    return ''.join(parts)


def landing(home, text, resolver=None):
    """Replace exactly one plain pre's contents, not arbitrary consumer markup.

    HTMLParser supplies decoded text and original source offsets. Nested tags,
    attributes and repeated matches are rejected, not interpreted as directives.
    The existing source contract omits only final LF characters for the homepage.
    """
    expected = text.rstrip('\n')

    class Blocks(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.lines = [0]
            self.lines.extend(m.end() for m in re.finditer('\n', home))
            self.active = None
            self.matches = []

        def source_offset(self):
            line, col = self.getpos()
            return self.lines[line - 1] + col

        def handle_starttag(self, tag, attrs):
            if self.active is not None:
                self.active['unsafe'] = True
            if tag == 'pre':
                require(self.active is None, 'nested landing example pre')
                self.active = dict(start=self.source_offset(), content=self.source_offset() + len(self.get_starttag_text()),
                                   parts=[], unsafe=bool(attrs))

        def handle_startendtag(self, tag, attrs):
            if self.active is not None:
                self.active['unsafe'] = True

        def handle_data(self, value):
            if self.active is not None:
                self.active['parts'].append(value)

        def handle_comment(self, value):
            if self.active is not None:
                self.active['unsafe'] = True

        handle_decl = handle_comment
        handle_pi = handle_comment
        unknown_decl = handle_comment

        def handle_endtag(self, tag):
            if self.active is not None:
                if tag != 'pre':
                    self.active['unsafe'] = True
                    return
                block = self.active; self.active = None
                if ''.join(block['parts']) == expected:
                    require(not block['unsafe'], 'unexpected landing example tags/attributes')
                    self.matches.append((block['start'], block['content'], self.source_offset()))

    parser = Blocks(); parser.feed(home); parser.close()
    require(parser.active is None and len(parser.matches) == 1,
            'landing example requires exactly one authoritative plain pre')
    start, _, end = parser.matches[0]
    return home[:start] + '<pre class="ada-example" tabindex="0">' + code(expected, resolver, landing=True) + home[end:]


def stylesheet_link(page, *, landing=False):
    # Authentic consumer homepages legally omit the head element/end tag.
    marker = '</head>' if '</head>' in page else '<body>'
    require(page.count(marker) == 1, 'missing/ambiguous example stylesheet head')
    prefix = '' if landing else '../'
    return page.replace(marker, f'<link rel="stylesheet" href="{prefix}{STYLESHEET}">' + marker)