"""Version-one opt-in search: source identities, observed native destinations.

The output index is a cache, not authority. Verification reconstructs every
byte from inputs. The browser checks its digest and resolves each record through
the separately generated destination allowlist before exposing any result.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from .destinations import source_destinations
from .inventory import HEADER, mask_ada, packages, visible_prefix
from .theme import asset
from .util import digest, require, sorted_json

MAX_RECORDS = 20000
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 64000
INDEX = 'api/gnatdoc-search-index.json'
STYLE = '<link rel="stylesheet" href="gnatdoc-search.css">'


class Text(HTMLParser):
    """Only visible authored content, not resources, navigation, or metadata."""
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.parts = []; self.main_parts = []; self.in_main = False; self.excluded = 0
        self.feed(value); self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'main': self.in_main = True
        if tag in ('head', 'script', 'style', 'nav', 'footer'):
            self.excluded += 1

    def handle_endtag(self, tag):
        if tag == 'main': self.in_main = False
        if tag in ('head', 'script', 'style', 'nav', 'footer'):
            self.excluded -= 1

    def handle_data(self, data):
        if not self.excluded:
            self.parts.append(data)
            if self.in_main: self.main_parts.append(data)


def flat_public(package):
    """Decline unsupported scopes, same-line private parts, and generic formals.

    Public private views are admitted; their completions are not. Generic
    templates' public members are real declarations; instantiated members with
    no native anchors are deliberately not invented.
    """
    header = HEADER.search(mask_ada(package.source))
    public = mask_ada(visible_prefix(package.source, header.end()))
    if re.search(r'\bprivate\s+with\b', public, re.I):
        return ''
    boundary = re.search(r'\bprivate\b(?!\s*;)', public, re.I)
    if boundary:
        public = public[:boundary.start()]
    if header[3].lower() != 'is' or re.search(
            r'\b(package|generic|task|protected|begin|declare)\b', public, re.I):
        return ''
    return public


def records(config, native, guides):
    if config.ada_example_highlighting or config.ada_landing_example_highlighting:
        # Token spans split HTMLParser data events. Index the original authored
        # rendering so presentation cannot insert spaces into identifiers or
        # otherwise change the established search corpus/authority hash.
        from dataclasses import replace
        from .guides import render
        guides = render(replace(config, ada_example_highlighting=False,
                                ada_example_api_links=False,
                                ada_landing_example_highlighting=False), native)
    source = packages(config)
    destinations = source_destinations(config, native, source)
    result = []
    for key, package in sorted(source.items()):
        if 'internal' in key.split('.'):
            continue
        page = native.pages[key]
        result.append(dict(kind='package', name=package.name, label=package.name,
                           href=page.path.name, text=''))
        public = flat_public(package)
        for d in destinations[key]:
            decl = d.declaration
            if decl.kind not in ('type', 'subtype', 'function', 'procedure'):
                continue
            # Match the whole signature inside the proven public prefix. This
            # binds overloads too, rather than checking a same-named declaration.
            signature = mask_ada(decl.signature).strip()
            if not signature or signature not in public:
                continue
            name = package.name + '.' + decl.name
            label = name + (f' (overload {d.ordinal}/{d.total})' if d.total > 1 else '')
            code = ' '.join(re.sub(r'(?m)^\s*--[^\n]*', '', decl.signature).split())
            description = ' '.join(decl.signature.split())
            result.append(dict(kind='symbol' if decl.kind in ('type', 'subtype') else 'operation',
                               name=name, label=label, href=d.href,
                               text=(code + ' ' + description)[:MAX_TEXT]))
    if config.guides != 'none':
        if config.guides.startswith('authored-'):
            from .authored import manifest
            data = manifest(config, native)
        else:
            from .guides import manifest
            data = manifest(config)
        for guide in data['guides']:
            path = guide['path']
            require(path in guides and re.fullmatch(r'guides/[a-z][a-z0-9-]*\.html', path),
                    'search guide lacks approved rendered destination')
            parser = Text(guides[path].decode())
            text = ' '.join(' '.join(parser.main_parts or parser.parts).split())
            require(len(text) <= MAX_TEXT, 'search guide exceeds bounded text contract')
            result.append(dict(kind='guide', name=guide['label'], label=guide['label'],
                               href='../' + path, text=text))
    result.sort(key=lambda r: (r['name'].lower(), r['kind']))
    require(len(result) <= MAX_RECORDS, 'search record limit exceeded')
    require(len({r['href'] for r in result}) == len(result), 'duplicate search destination')
    return result


def enhance(config, native, index, guides):
    data = records(config, native, guides)
    payload = sorted_json(dict(schema_version=1, records=data)).encode()
    require(len(payload) <= MAX_BYTES, 'search index byte limit exceeded')
    links = []
    for r in data:
        # API links join precisely the existing router's allowlist. Guides never
        # have an iframe target and cannot acquire API routing authority.
        target = ' target="document-content"' if r['kind'] != 'guide' else ''
        links.append('<a href="' + html.escape(r['href'], quote=True) + '"' + target +
                     ' data-search-name="' + html.escape(r['name'], quote=True) +
                     '" data-search-kind="' + r['kind'] + '"></a>')
    authority = ('<div id="documentation-search-authority" hidden data-schema="1" data-sha256="' +
                 digest(payload) + '" data-count="' + str(len(data)) + '">' + ''.join(links) + '</div>')
    index = index.replace('Filter navigation links</label>', 'Search documentation</label>', 1)
    index = index.replace('<h2 id=compilation-units>', authority +
                          '<ul id="documentation-search-results" aria-label="Search results" hidden></ul>' +
                          '<h2 id=compilation-units>', 1)
    from .navigation import SCRIPT
    index = index.replace(SCRIPT, SCRIPT + STYLE, 1)
    return index, {INDEX: payload, 'api/gnatdoc-search.css': asset('gnatdoc-search.css')}


def runtime(router):
    """A single shared implementation composed with any of the three routers.

    Leave legacy assets byte-identical. The opt-in adapter supplies only the
    existing router's approved states, canonical URL builder and activation.
    """
    text = router.decode()
    beginning = '  function filter() {'
    ending = "  window.addEventListener('popstate',restore);"
    require(text.count(beginning) == 1 and text.count(ending) == 1,
            'unqualified search/router composition points')
    start = text.index(beginning)
    end = text.index(ending, start)
    text = text[:start] + '''  const filter = window.gnatdocDocumentationSearch({approved, canonicalUrl, activate});
''' + text[end:]
    return asset('gnatdoc-search.js') + b'\n' + text.encode()