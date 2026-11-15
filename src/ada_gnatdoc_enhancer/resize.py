"""Opt-in shell presentation only; no routing or declaration authority."""
from .theme import asset
from .util import require

HEAD = ('<link rel="stylesheet" href="gnatdoc-resize.css">'
        '<script src="gnatdoc-resize.js" defer></script>')
DIVIDER = ('<div id="navigation-resize" role="separator" aria-orientation="vertical" '
           'aria-label="Navigation width" aria-controls="resizable-navigation" '
           'tabindex="0" hidden></div>')


def enhance(config, index):
    if not config.resizable_sidebar:
        return index, {}
    require(config.theme, 'resizable sidebar requires theme = true')
    require(index.count('<div class=side-navigation>') == 1 and
            index.count('<div class=document-content>') == 1 and
            'navigation-resize' not in index and 'gnatdoc-resize' not in index,
            'unqualified resize shell')
    index = index.replace('<div class=side-navigation>',
                          '<div class=side-navigation id="resizable-navigation">', 1)
    index = index.replace('<div class=document-content>', DIVIDER+'<div class=document-content>', 1)
    # native_document validates the complete approved head before canonicalizing it.
    index = index.replace('<body class=main>', HEAD+'<body class=main>', 1)
    return index, {'api/'+name: asset(name) for name in ('gnatdoc-resize.css', 'gnatdoc-resize.js')}