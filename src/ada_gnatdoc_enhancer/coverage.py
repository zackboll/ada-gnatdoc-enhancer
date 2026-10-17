"""Conservative source/rendered documentation evidence reporting.

Qualifies exactly package descriptions and native declaration coverage; richer
member-level contracts are delegated to consumer adapters until equivalent source
forms are qualified. Missing sections count as gaps, never as success.
"""
from __future__ import annotations

import re

from .errors import EnhancementError
from .inventory import Package
from .native_html import NativeSite
from .util import require


def report(source:dict[str,Package], native:NativeSite, *, comment_style='leading', renderer_exceptions=()):
    require(comment_style in ('leading','trailing'),"unsupported source comment style")
    units=[]
    for key,pkg in source.items():
        page=native.pages[key]
        for declaration in pkg.declarations:
            matches=[s for s in page.sections if s.name.lower()==declaration.name.lower()]
            # Overloads are included in inventory by source position, but a
            # same-named section is not enough to qualify overload identity.
            confirmed=next((s for s in matches if declaration.kind in ('type','subtype')
                            and re.match(r'^\s*'+declaration.kind+r'\s+',s.code,re.I)),None)
            if declaration.kind in ('type','subtype'):
                success=confirmed is not None
            elif declaration.kind in ('procedure','function'):
                success=any(re.match(r'^\s*'+declaration.kind+r'\s+',s.code,re.I) for s in matches)
            else: success=False
            units.append({'identity':pkg.name+'.'+declaration.name,
                          'kind':declaration.kind,'source':pkg.path.name,
                          'rendered':success})
    return {'schema_version':1,'level':'declaration inventory only — not full member/coverage parity',
            'elements':len(units),'rendered':sum(1 for u in units if u['rendered']),
            'unrendered':[u['identity'] for u in units if not u['rendered']],
            'comment_style':comment_style,
            'renderer_exceptions':list(renderer_exceptions)}
