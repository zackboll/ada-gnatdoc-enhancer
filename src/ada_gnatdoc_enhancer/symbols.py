"""Opt-in public bookmarks; source owns identities, native input owns anchors.

This deliberately does not widen the type-link resolver or its historical
inventory. Unsupported nested scopes cannot gain bookmark authority merely by
having similarly named native output. Public private *views* (e.g. Mat) are
public; declarations after the private boundary and generic formals are not.
"""
from __future__ import annotations

import html
import re

from .destinations import source_destinations
from .inventory import HEADER, mask_ada, packages, visible_prefix
from .util import PAGE_NAME, QNAME, require


def public_symbols(config, native):
    if not config.symbol_bookmarks:
        return []
    require(config.navigation == 'packages' and config.category_file is None,
            'symbol bookmarks require uncategorized package navigation')
    source = packages(config)
    default = config.default_package
    require(isinstance(default, str) and default.lower() in source and
            default.lower() in native.pages and
            'internal' not in default.lower().split('.'),
            'default package lacks public source/native authority')
    require(native.pages[default.lower()].package == source[default.lower()].name,
            'default package spelling differs from source')
    destinations = source_destinations(config, native, source)
    result = []; identities = set(); targets = set()
    for key, package in sorted(source.items()):
        if 'internal' in key.split('.'):
            continue
        header = HEADER.search(mask_ada(package.source))
        require(header is not None, 'missing symbol owner header')
        public = mask_ada(visible_prefix(package.source, header.end()))
        # The historical scanner's line boundary is not a scope proof: Ada
        # permits PRIVATE on the same line. Public partial views end private;
        # and must not be confused with the private-part boundary.
        if re.search(r'\bprivate\s+with\b', public, re.I):
            continue
        boundary = re.search(r'\bprivate\b(?!\s*;)', public, re.I)
        if boundary is not None:
            public = public[:boundary.start()]
        # Library generic formals precede the header; declarations in the
        # public part of a generic template are genuine public declarations.
        if header[3].lower() != 'is' or re.search(
                r'\b(package|generic|task|protected|begin|declare)\b', public, re.I):
            continue
        for destination in destinations[key]:
            declaration = destination.declaration
            if declaration.kind not in ('type', 'subtype'):
                continue
            # Bind the defining declaration to the admitted public prefix,
            # rather than inheriting the broader historical lexical scanner.
            if not re.search(r'\b' + declaration.kind + r'\s+' +
                             re.escape(declaration.name) + r'\b', public, re.I):
                continue
            identity = package.name + '.' + declaration.name
            require(re.fullmatch(QNAME, identity) is not None and
                    native.pages[key].package == package.name,
                    'invalid public symbol owner or spelling')
            require(PAGE_NAME.fullmatch(destination.page.path.name) is not None and
                    re.fullmatch('[a-f0-9]{64}', destination.section.anchor) is not None,
                    'unsafe observed symbol destination')
            require(identity.lower() not in identities and destination.href not in targets,
                    'duplicate public symbol identity or destination')
            identities.add(identity.lower()); targets.add(destination.href)
            result.append((identity, destination))
    require(result, 'empty public symbol inventory')
    return result


def metadata(config, native):
    symbols = public_symbols(config, native)
    if not symbols:
        return ''
    default = native.pages[config.default_package.lower()].package
    links = ''.join('<a href="' + html.escape(d.href, quote=True) +
                    '" data-symbol="' + html.escape(name, quote=True) + '"></a>'
                    for name, d in symbols)
    return ('<div id="type-navigation" hidden data-default-package="' +
            html.escape(default, quote=True) + '">' + links + '</div>')