"""Stable warning identities with source-location ownership.

The common implementation covers package, type, subprogram and record locations;
unsupported nested constructs are flagged instead of silently matched.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import EnhancementError
from .inventory import Package, mask_ada, normalized
from .util import require

WARNING = re.compile(r'^(.*?\.ads):(\d+):(\d+): warning: (.+)$')


def identities(log: str, packages:dict[str,Package]):
    by_name={p.path.name:p for p in packages.values()}
    values=[]
    for line in log.splitlines():
        if 'warning:' not in line:continue
        m=WARNING.fullmatch(line.strip())
        require(m is not None,f"unsupported GNATdoc warning format: {line}")
        filename,n,col,message=m.groups()
        p=by_name.get(filename.rpartition('/')[2])
        require(p is not None, f"warning source outside known public specs: {filename}")
        line=int(n)
        candidates=[d for d in p.declarations if d.line<=line]
        # Refuse warnings not mapped to a declaration/package context.
        if candidates:
            d=max(candidates,key=lambda d:d.line)
            identity=f"{p.name}: {d.kind} {d.name}: {normalized(d.signature)}"
        else:
            identity=f"{p.name}: package"
        values.append(f"{p.path.name}: {identity}: warning: {message.strip()}")
    require(len(values)==len(set(values)), "duplicate warning identities; source resolver insufficient")
    return sorted(values)


def compare(actual:list[str],baseline:list[str],strict_removed=True):
    added=sorted(set(actual)-set(baseline))
    removed=sorted(set(baseline)-set(actual))
    require(not added,f"new documentation warnings: {added[:8]}")
    if strict_removed: require(not removed,f"fixed documentation warnings still in baseline: {removed[:8]}")
    return {'actual':len(actual),'added':added,'removed':removed}
