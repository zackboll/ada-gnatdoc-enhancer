"""Source-verified HTML document metadata: title, language and charset.

GNATdoc 26.0.0 (20260415) writes each API page as exactly

    <!DOCTYPE html>\\n<html class=main>\\n<link rel=stylesheet href=gnatdoc.css><body class=main|content>...

with no <head>, <title>, character-encoding declaration or lang attribute.
The repository's synthetic conformance pages use the same element sequence
without the two line breaks and the html class. Any other layout, and any
preexisting document metadata, is rejected rather than reformatted.

The enhancement is one bounded insertion: lang="en" on the existing html start
tag (its native attributes are kept) and an explicit head that wraps the head
content the pipeline already approved (native stylesheet, optional theme and
viewport, optional navigation script) behind a UTF-8 charset declaration and a
title. The body, sections, anchors and code are not touched. Titles come only
from verified identities: a package page from its native h1 reconciled with the
Ada source package name, the API index and Markdown guides from the validated
project configuration and source-owned guide manifest; never from an output
filename, URL, fragment or page hash.

Author-provided pages (portal homes, HTML guides, authored portals) keep their
own metadata. They must carry it, and it is validated, never invented.
"""
from __future__ import annotations

import html
import re
import unicodedata
from html.parser import HTMLParser

from .theme import NATIVE_LINK
from .util import require

LANGUAGE = 'en'
CHARSET = '<meta charset="utf-8">'
SEPARATOR = ' — '
API_INDEX = 'API Reference'
NATIVE_PROLOGUE = re.compile(r'(<!DOCTYPE html>\n?<html(?: class=main)?)(>\n?)')
NATIVE_BODY = re.compile(r'<body class=(?:main|content)>')
BCP47 = re.compile(r'[a-z]{2,3}(?:-[A-Za-z0-9]{1,8})*')
HEAD_TAGS = frozenset({'html', 'head', 'meta', 'title', 'link', 'script', 'style', 'base',
                       'noscript', 'template'})
MAX_TITLE = 300
MAX_DOCUMENT_TITLE = 2 * MAX_TITLE + len(SEPARATOR)
VIEWPORT = {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}


def safe_title(value: str, what: str) -> str:
    """Validate decoded title text without normalizing or rewriting author content."""
    require(bool(value) and value == value.strip() and len(value) <= MAX_DOCUMENT_TITLE and
            all(c == ' ' or unicodedata.category(c)[0] not in 'CZ' for c in value),
            f"empty or malformed document title; unsafe document title: {what}")
    return value


def label(value, what: str) -> str:
    """A title component: one line of visible text, no controls or format characters."""
    require(isinstance(value, str) and bool(value) and value == value.strip() and
            len(value) <= MAX_TITLE and
            all(c == ' ' or unicodedata.category(c)[0] not in 'CZ' for c in value),
            f"untrusted {what} for an HTML document title: {value!r}")
    return value


def package_title(package: str, project: str) -> str:
    return safe_title(label(package, 'package name') + SEPARATOR + label(project, 'project name'), 'package')


def index_title(project: str) -> str:
    return safe_title(API_INDEX + SEPARATOR + label(project, 'project name'), 'index')


def guide_title(guide: str, project: str) -> str:
    return safe_title(label(guide, 'guide label') + SEPARATOR + label(project, 'project name'), 'guide')


def serialized_title(text: str, start: int, name: str) -> tuple[str, str, int]:
    """Check a title's original serialization, independently of RCDATA callbacks.

    The caller supplies the parser-observed opening offset, not a document-wide
    regex search (which could mistake comments or escaped examples for titles).
    Only an attribute-free opening, text/entities and a plain closing tag are
    supported. Literal '<' must begin that closure; escaped angle brackets are
    text. Decode numeric references explicitly so HTMLParser/html.unescape
    cannot silently discard or replace prohibited controls before validation.
    """
    opening = re.match(r'<title[\t\n\f\r ]*>', text[start:], re.I)
    require(opening is not None, f"malformed serialized document title opening: {name}")
    content_start = start + opening.end()
    closing = text.find('<', content_start)
    require(closing >= 0 and re.match(r'</title[\t\n\f\r ]*>', text[closing:], re.I) is not None,
            f"literal markup or unfinished serialized document title: {name}")
    raw = text[content_start:closing]

    def decode(match):
        entity = match[0]
        if entity.startswith('&#'):
            number = entity[2:].rstrip(';')
            try:
                return chr(int(number[1:], 16) if number.lower().startswith('x') else int(number))
            except (ValueError, OverflowError):
                require(False, f"unsafe document title character reference: {name}")
        return html.unescape(entity)

    decoded = re.sub(r'&#(?:[xX][0-9a-fA-F]+|[0-9]+);?|&[A-Za-z][A-Za-z0-9]*;?', decode, raw)
    return raw, safe_title(decoded, name), closing


class Document(HTMLParser):
    """Independent document-metadata census; shares no strings with the generator."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=False)
        self.roots, self.langs, self.heads, self.bodies = 0, [], 0, 0
        self.titles, self.charsets, self.misplaced = [], [], []
        self.in_head, self._title = True, None
        self.title_openings, self.title_closures = 0, 0
        self.head_closures, self.issues, self.metas = 0, [], []
        self._explicit_head, self._implicit_metadata = False, False
        self._root_closed = False
        self._serialized = text
        self._line_offsets = [0] + [m.end() for m in re.finditer('\n', text)]
        self.serialized_titles, self._title_closing = [], None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        keys = dict(attrs)
        if self._root_closed:
            self.issues.append('element after document root closure')
        if self._title is not None:
            self.issues.append('markup nested inside title')
        if tag == 'head':
            if not self.in_head or self.heads or self._implicit_metadata or self.roots != 1:
                self.issues.append('malformed head ordering')
            self._explicit_head = True
        if tag == 'html' and (self.heads or self._implicit_metadata):
            self.issues.append('malformed root ordering')
        if tag not in HEAD_TAGS and self._explicit_head:
            self.issues.append('unclosed head before body content')
        if tag not in HEAD_TAGS:
            self.in_head = False
        if tag == 'html':
            self.roots += 1
            self.langs.append([v for k, v in attrs if k == 'lang'])
        elif tag == 'head':
            self.heads += 1
        elif tag == 'body':
            self.bodies += 1
        elif tag == 'title':
            line, column = self.getpos()
            _, decoded, self._title_closing = serialized_title(
                self._serialized, self._line_offsets[line - 1] + column, 'HTML document')
            self.serialized_titles.append(decoded)
            self.title_openings += 1
            if not self.in_head:
                self.misplaced.append('title')
            if attrs:
                self.issues.append('unapproved title attributes')
            self._title = ''
        elif tag == 'meta':
            self.metas.append(attrs)
            if not self.in_head:
                self.misplaced.append('metadata')
            if 'charset' in keys:
                self.charsets.append(keys['charset'])
        if tag in ('title', 'meta', 'link') and not self.heads:
            self._implicit_metadata = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in ('html', 'head', 'title', 'body'):
            self.issues.append('self-closing document element')

    def handle_endtag(self, tag):
        if tag == 'html':
            self._root_closed = True
            self.in_head = False
        if tag == 'head':
            self.head_closures += 1
            if not self._explicit_head or not self.in_head:
                self.issues.append('unmatched head closure')
            self._explicit_head = False
            self.in_head = False
        if tag == 'title':
            self.title_closures += 1
            line, column = self.getpos()
            if self._title_closing != self._line_offsets[line - 1] + column:
                self.issues.append('serialized title closure differs from parser boundary')
            self._title_closing = None
            if self._title is None:
                self.issues.append('unmatched title closure')
            else:
                self.titles.append(self._title)
                self._title = None
        elif self._title is not None:
            self.issues.append('unfinished title before closing markup')

    def handle_data(self, data):
        if self._title is not None:
            self._title += data
        elif self.in_head and data.strip():
            if self._explicit_head:
                self.issues.append('body text inside explicit head')
            self.in_head = False

    def handle_entityref(self, name):
        self.handle_data(html.unescape('&' + name + ';'))

    def handle_charref(self, name):
        try:
            value = chr(int(name[1:], 16) if name.lower().startswith('x') else int(name))
        except (ValueError, OverflowError):
            self.issues.append('invalid character reference')
            return
        self.handle_data(value)

    def handle_comment(self, data):
        if self._title is not None:
            self.issues.append('comment markup inside title')


def check_document(text: str, name: str, *, title: str | None = None,
                   generated: bool = False, viewport: bool | None = None) -> str:
    """Require exactly one html root with a language, one nonempty head title and
    a UTF-8 charset. Generated pages also need an explicit head, lang="en" and
    their exact verified title. Returns the title text."""
    page = Document(text)
    require(page.roots == 1 and page.bodies <= 1, f"missing or duplicate document root: {name}")
    require(len(page.langs[0]) == 1 and BCP47.fullmatch(page.langs[0][0] or '') is not None,
            f"missing, duplicate or invalid document language: {name}")
    require(page.heads <= 1, f"duplicate document head: {name}")
    require(page.title_openings == page.title_closures == len(page.titles) == 1 and page._title is None,
            f"missing or duplicate document title, nested or unfinished title: {name}")
    require(page.titles == page.serialized_titles,
            f"serialized document title differs from decoded parser title: {name}")
    require(not page.issues and page.heads == page.head_closures,
            f"malformed document title/head structure: {name}: {page.issues}")
    require(len(page.charsets) == 1 and isinstance(page.charsets[0], str) and
            page.charsets[0].lower() == 'utf-8',
            f"missing, duplicate or non-UTF-8 charset declaration: {name}")
    require(not page.misplaced, f"document metadata outside the head: {name}")
    found = page.titles[0]
    safe_title(found, name)
    if generated:
        require(page.heads == 1 and page.langs[0] == [LANGUAGE],
                f"generated page lacks its head or lang=\"{LANGUAGE}\": {name}")
        # All generated metadata is independently inventoried, not just charset.
        metas = [dict(attrs) for attrs in page.metas]
        require(all(len(dict(attrs)) == len(attrs) for attrs in page.metas),
                f"duplicate generated metadata attributes: {name}")
        charset = [m for m in metas if set(m) == {'charset'} and
                   isinstance(m['charset'], str) and m['charset'].lower() == 'utf-8']
        viewports = [m for m in metas if m == VIEWPORT]
        require(len(charset) == 1 and len(metas) == 1 + len(viewports) and len(viewports) <= 1 and
                (viewport is None or len(viewports) == int(viewport)),
                f"unapproved generated metadata inventory: {name}")
    if title is not None:
        require(found == title, f"document title does not match its verified identity: {name}")
    return found


def check_native_input(original: str, name: str) -> None:
    """The original GNATdoc page must have the qualified layout and no metadata."""
    prologue = NATIVE_PROLOGUE.match(original)
    require(prologue is not None and original[prologue.end():].startswith(NATIVE_LINK) and
            NATIVE_BODY.match(original, prologue.end() + len(NATIVE_LINK)) is not None,
            f"unsupported native GNATdoc document layout: {name}")
    page = Document(original)
    require(page.roots == 1 and page.bodies == 1 and page.heads == 0 and not page.title_openings and
            not page.title_closures and not page.metas and not page.issues and page.langs == [[]],
            f"native GNATdoc page already has document metadata or a duplicate root: {name}")


def native_document(text: str, head: str, title: str, name: str) -> str:
    """Add lang, an explicit head, the charset and the title to an enhanced page.

    ``head`` is the exact head content the pipeline approved for this page."""
    prologue = NATIVE_PROLOGUE.match(text)
    require(prologue is not None and text[prologue.end():].startswith(head) and
            NATIVE_BODY.match(text, prologue.end() + len(head)) is not None,
            f"unexpected enhanced document head: {name}")
    rest = text[prologue.end() + len(head):]
    return (prologue[1] + ' lang="' + LANGUAGE + '"' + prologue[2] + '<head>' + CHARSET +
            '<title>' + html.escape(title) + '</title>' + head + '</head>' + rest)


def strip_native_document(text: str, title: str, name: str) -> str:
    """Exactly remove the authorized metadata, leaving the pre-metadata page."""
    opening = '<head>' + CHARSET + '<title>' + html.escape(title) + '</title>'
    prologue = NATIVE_PROLOGUE.match(text.replace(' lang="' + LANGUAGE + '">', '>', 1))
    require(prologue is not None and text.count(' lang="' + LANGUAGE + '"') == 1 and
            text.count(opening) == 1 and text.count('<head>') == 1 and text.count('</head>') == 1,
            f"native document metadata is missing, duplicated or not authorized: {name}")
    value = text.replace(' lang="' + LANGUAGE + '">', '>', 1)
    require(value[prologue.end():].startswith(opening), f"misplaced native document head: {name}")
    value = value.replace(opening, '', 1)
    body = NATIVE_BODY.search(value)
    require(body is not None and value[:body.start()].endswith('</head>'),
            f"misplaced native document head end: {name}")
    value = value[:body.start() - len('</head>')] + value[body.start():]
    page = Document(value)
    require(page.heads == 0 and not page.titles and not page.charsets and page.langs == [[]],
            f"unauthorized document metadata remains after removal: {name}")
    return value
