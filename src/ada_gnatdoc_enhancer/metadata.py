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


def label(value, what: str) -> str:
    """A title component: one line of visible text, no controls or format characters."""
    require(isinstance(value, str) and bool(value) and value == value.strip() and
            len(value) <= MAX_TITLE and
            all(c == ' ' or unicodedata.category(c)[0] not in 'CZ' for c in value),
            f"untrusted {what} for an HTML document title: {value!r}")
    return value


def package_title(package: str, project: str) -> str:
    return label(package, 'package name') + SEPARATOR + label(project, 'project name')


def index_title(project: str) -> str:
    return API_INDEX + SEPARATOR + label(project, 'project name')


def guide_title(guide: str, project: str) -> str:
    return label(guide, 'guide label') + SEPARATOR + label(project, 'project name')


class Document(HTMLParser):
    """Independent document-metadata census; shares no strings with the generator."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.roots, self.langs, self.heads, self.bodies = 0, [], 0, 0
        self.titles, self.charsets, self.misplaced = [], [], []
        self.in_head, self._title = True, None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        keys = dict(attrs)
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
            if not self.in_head:
                self.misplaced.append('title')
            self._title = ''
        elif tag == 'meta' and 'charset' in keys:
            if not self.in_head:
                self.misplaced.append('charset')
            self.charsets.append(keys['charset'])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        if tag == 'title' and self._title is not None:
            self.titles.append(self._title)
            self._title = None

    def handle_data(self, data):
        if self._title is not None:
            self._title += data


def check_document(text: str, name: str, *, title: str | None = None,
                   generated: bool = False) -> str:
    """Require exactly one html root with a language, one nonempty head title and
    a UTF-8 charset. Generated pages also need an explicit head, lang="en" and
    their exact verified title. Returns the title text."""
    page = Document(text)
    require(page.roots == 1 and page.bodies <= 1, f"missing or duplicate document root: {name}")
    require(len(page.langs[0]) == 1 and BCP47.fullmatch(page.langs[0][0] or '') is not None,
            f"missing, duplicate or invalid document language: {name}")
    require(page.heads <= 1, f"duplicate document head: {name}")
    require(len(page.titles) == 1, f"missing or duplicate document title: {name}")
    require(len(page.charsets) == 1 and page.charsets[0].lower() == 'utf-8',
            f"missing, duplicate or non-UTF-8 charset declaration: {name}")
    require(not page.misplaced, f"document metadata outside the head: {name}")
    found = page.titles[0]
    require(bool(found.strip()) and found == found.strip() and '\n' not in found,
            f"empty or malformed document title: {name}")
    if generated:
        require(page.heads == 1 and page.langs[0] == [LANGUAGE],
                f"generated page lacks its head or lang=\"{LANGUAGE}\": {name}")
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
    require(page.roots == 1 and page.bodies == 1 and page.heads == 0 and not page.titles and
            not page.charsets and page.langs == [[]],
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
