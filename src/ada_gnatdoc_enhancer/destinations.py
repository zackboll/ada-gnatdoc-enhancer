"""Shared source-order declaration identities for navigation and authored links.

Ordinals come only from the public Ada inventory. Native sections supply only
observed filenames, anchors and complete profile evidence, never ordering.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .inventory import (Declaration, HEADER, direct_callables, packages, mask_ada,
                        visible_prefix, last_semicolon)
from .native_html import NativePage, Section
from .profiles import reconcile
from .util import require


@dataclass(frozen=True)
class Destination:
    package: str
    declaration: Declaration
    page: NativePage
    section: Section
    ordinal: int
    total: int

    @property
    def href(self):
        return self.page.path.name + '#' + self.section.anchor


def source_destinations(config, native, source=None):
    """Reconcile each supported declaration with exactly one distinct anchor.

    Preserve authored links' narrow flat-package constant support without
    expanding the general inventory's historical coverage counts.
    """
    source = packages(config) if source is None else source
    require(set(source) == set(native.pages), 'source/native destination package mismatch')
    result = {}
    for key, pkg in source.items():
        used = set()
        page = native.pages[key]
        require(page.package.lower() == key, 'swapped native destination package')
        callables = direct_callables(pkg)
        declarations = list(pkg.declarations)
        masked = mask_ada(pkg.source); header = HEADER.search(masked)
        public = visible_prefix(pkg.source, header.end())
        public_mask = mask_ada(public)
        if callables:
            for match in re.finditer(r'(?im)^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*constant\b', public_mask):
                end = last_semicolon(public_mask, match.start())
                declarations.append(Declaration('constant', match[1], public[match.start():end].strip(),
                    pkg.source.count('\n', 0, header.end() + match.start()) + 1))
        declarations.sort(key=lambda d: d.line)
        totals = Counter(d.name.lower() for d in declarations)
        counters = Counter()
        result[key] = []
        for decl in declarations:
            found = [s for s in page.sections if s.name.lower() == decl.name.lower() and
                     reconcile(decl.signature, s.code, callables) is not None]
            require(len(found) == 1,
                    f'API declaration lacks unique source identity: {pkg.name}.{decl.name} at {decl.line}')
            section = found[0]
            href = page.path.name + '#' + section.anchor
            require(href not in used, 'ambiguous source declarations share native destination')
            used.add(href)
            name = decl.name.lower(); counters[name] += 1
            result[key].append(Destination(pkg.name, decl, page, section, counters[name], totals[name]))
    return result