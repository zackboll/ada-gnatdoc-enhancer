"""Exact known GNATdoc 26 MEL package-renaming renderer omission.

The exception is a measured unrendered source declaration. It cannot provide
coverage credit and does not authorize arbitrary future renderer omissions.
"""
from __future__ import annotations

import re

from ..errors import EnhancementError
from ..inventory import mask_ada
from ..util import require

IDENTITY='AMS.MEL.IR.Health_Status.Metadata.Status'
PARENT='AMS.MEL.IR.Health_Status.Metadata'
TARGET='AMS.MEL.Status'


def verify_renderer_exceptions(config,source,native):
    if not config.renderer_exceptions:return 0
    require(config.gnatdoc=='26.0.0' and config.renderer_exceptions==(IDENTITY,),
            'unqualified MEL renderer exception')
    pkg=source.get(PARENT.lower())
    require(pkg is not None and PARENT.lower() in native.pages,
            'MEL renderer exception package is absent')
    # Only the exact package-renaming source declaration qualifies, not a
    # comments-only match or a private-part declaration.
    code=mask_ada(pkg.source)
    declaration=re.findall(r'(?im)^\s*package\s+Status\s+renames\s+AMS\.MEL\.Status\s*;',code)
    require(len(declaration)==1,'MEL renderer exception lacks exact source alias')
    candidates=[s for s in native.pages[PARENT.lower()].sections
                if s.name.lower()=='status' and re.match(r'(?i)\s*package\s+Status\s+renames',s.code)]
    require(not candidates,'renderer exception has become rendered; remove stale exception')
    return 1
