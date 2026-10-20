"""Qualified GNATdoc 26 theme metadata and immutable bundled CSS."""
from __future__ import annotations

from importlib.resources import files

from .errors import EnhancementError
from .util import require

NATIVE_LINK = '<link rel=stylesheet href=gnatdoc.css>'
METADATA = ('<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<link rel="stylesheet" href="gnatdoc-theme.css">')


def themed(original: str, enabled: bool=True) -> str:
    if not enabled:return original
    require(original.count(NATIVE_LINK)==1, "unknown GNATdoc stylesheet insertion point")
    require('gnatdoc-theme.css' not in original and '<meta name="viewport"' not in original,
            "unexpected preexisting theme/viewport")
    return original.replace(NATIVE_LINK,NATIVE_LINK+METADATA,1)


def asset(name: str) -> bytes:
    require(name in {'gnatdoc-theme.css','gnatdoc-guides.css','gnatdoc-navigation.js',
                     'gnatdoc-symbol-navigation.js','gnatdoc-instance-navigation.js'},
            "unapproved bundled asset")
    return files('ada_gnatdoc_enhancer').joinpath('assets',name).read_bytes()
