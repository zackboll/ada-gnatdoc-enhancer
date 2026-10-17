"""GNATdoc 26 native page discovery and public source reconciliation."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .errors import EnhancementError, UnsupportedStructure
from .inventory import Package, normalized
from .util import PAGE_NAME, require, regular

HEADING = re.compile(r'<h1>([^<]+)</h1>')
SECTION = re.compile(r'<h4 id=(?:"([a-f0-9]{64})"|([a-f0-9]{64}))>([^<]+)</h4>\s*<pre class=ada-code-snippet><code>(.*?)</code></pre>', re.S)
NATIVE_ITEM = re.compile(r'<a href=(?:"([a-f0-9]{64}\.html)"|([a-f0-9]{64}\.html)) target=document-content>([^<]+)</a>')


@dataclass(frozen=True)
class Section:
    anchor: str
    name: str
    code: str


@dataclass
class NativePage:
    path: Path
    package: str
    sections: list[Section]
    original: str


@dataclass
class NativeSite:
    api: Path
    index: str
    original_css: bytes
    pages: dict[str, NativePage]
    nav_entries: list[tuple[str, str]]


def snapshot(config: Config, site: Path) -> NativeSite:
    from .inventory import packages
    api = site / 'api'
    regular(api / 'index.html'); regular(api / 'gnatdoc.css')
    source = packages(config)
    records = {}
    for path in sorted(api.glob('*.html')):
        if path.name == 'index.html': continue
        require(PAGE_NAME.fullmatch(path.name) is not None, f"unknown native HTML filename: {path.name}")
        original = regular(path).read_text(encoding='utf-8')
        heading = HEADING.findall(original)
        require(len(heading) == 1, f"invalid native package h1: {path.name}")
        name = html.unescape(heading[0])
        key = name.lower()
        require(key in source and key not in records, f"unrecognized or duplicated native package: {name}")
        sections = [Section(m[1] or m[2], html.unescape(m[3]), html.unescape(m[4]))
                    for m in SECTION.finditer(original)]
        require(len({x.anchor for x in sections}) == len(sections), f"duplicate native declaration anchors: {name}")
        records[key] = NativePage(path, name, sections, original)
    require(set(records) == set(source), f"source/native package mismatch: {sorted(set(records) ^ set(source))}")
    index = regular(api / 'index.html').read_text(encoding='utf-8')
    # Parse native links; tagged-type entries may share the same page and carry
    # fragments, hence only compare the compilation-units list.
    nav_body = index.split('<h2 id=tagged-types>', 1)[0]
    nav_items = [(html.unescape(x[2]), x[0] or x[1]) for x in NATIVE_ITEM.findall(nav_body)]
    require(len(nav_items) == len(records), "incomplete native compilation-unit navigation")
    expected = {(p.package.lower(), p.path.name) for p in records.values()}
    require({(name.lower(), target) for name,target in nav_items} == expected,
            "native navigation package destinations mismatch")
    require(len({name.lower() for name,_ in nav_items}) == len(nav_items), "duplicate native navigation name")
    require('iframe name=document-content' in index, "missing GNATdoc document-content frame")
    # Validate supported original declaration profiles against the Ada source.
    # A same-named but different overload is never accepted as equivalent.
    for key, package in source.items():
        page=records[key]
        for decl in package.declarations:
            expected=normalized(decl.signature).removesuffix(' ;').strip()
            # GNATdoc 26 strips aspects; only a trailing top-level aspect is
            # excluded from presentation matching, not from source ownership.
            expected=re.split(r'\swith\s(?:pre|post|global|depends)\s',expected,maxsplit=1)[0]
            found=[s for s in page.sections if s.name.lower()==decl.name.lower() and
                   normalized(s.code).removesuffix(' ;').strip()==expected]
            require(len(found)==1,
                    f"native declaration profile unmatched or swapped: {package.name}.{decl.name} at {decl.line}")
    return NativeSite(api, index, (api / 'gnatdoc.css').read_bytes(), records, nav_items)


def verified_types(site: NativeSite, source: dict[str, Package]) -> dict[str, tuple[Path, str]]:
    """Source and GNATdoc must independently support each type destination."""
    result = {}
    for key, page in site.pages.items():
        pkg = source[key]
        for name, declaration in pkg.public_types.items():
            matches = [s for s in page.sections if s.name.lower() == name and
                       re.match(r'^\s*(?:type|subtype)\s+'+re.escape(name)+r'\b', s.code, re.I)]
            require(len(matches) == 1, f"type declaration lacks unique real GNATdoc anchor: {pkg.name}.{name}")
            result[f"{key}.{name}"] = (page.path, matches[0].anchor)
    return result
