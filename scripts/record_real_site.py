#!/usr/bin/env python3
"""Bind a native acquisition to a reviewed qualification specification.

Run only against the snapshot exported by acquire_real_sites.py, never a
post-build source directory. Output remains an acquisition attestation to review.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from acquire_real_sites import PINS
from ada_gnatdoc_enhancer.qualification import hashes, identities
from ada_gnatdoc_enhancer.util import sorted_json


BLOCKERS={
    'core':['25 Vector/Matrix generic-instance summaries are unsupported.',
            'Native expression-function profiles differ from full source declarations.'],
    'imgproc':['GNATdoc abbreviated Color_Conversion enumeration is unsupported.',
               'External Core 0.4.1 anchors have not been independently qualified.',
               'Compiled authored guides are not qualified by this API-only profile.'],
    'geometry':['External Core 0.5.0 anchors have not been independently qualified.',
                'Compiled authored guides are not qualified by this API-only profile.'],
    'mel':['GNATdoc abbreviated Cannot_Comply enumeration is unsupported.',
           'Health Status Metadata.Status renaming remains one unrendered omission, not credit.',
           'MEL authored portal/guides and approved source-integrity guard remain consumer-owned.'],
}


def record(profile,snapshot,site):
    repo,sha=PINS[profile]
    native=identities(site)
    public=[]
    directory='ada/src' if profile=='mel' else 'src'
    for path in sorted((snapshot/directory).glob('*.ads')):
        # Only library-header classification; do not hide a declaration-scanner
        # failure by using the enhancer to select its own qualifying inputs.
        from ada_gnatdoc_enhancer.inventory import mask_ada
        header=re.search(r'(?im)^\s*(private\s+)?package\s+([\w.]+)\s+is\b',
                         mask_ada(path.read_text(encoding='utf-8')))
        if not header:raise ValueError(f'unsupported library header: {path}')
        if not header[1]:public.append(path.relative_to(snapshot).as_posix())
    source_hashes={n:h for n,h in hashes(snapshot).items()
                   if Path(n).suffix in ('.ads','.adb','.gpr','.toml') or
                   (n.startswith('docs/') and Path(n).suffix in ('.md','.html','.json')) or
                   n in ('docs/api-categories.json','docs/gnatdoc-warning-baseline.txt',
                         'docs/gnatdoc-coverage-baseline.txt','docs/gnatdoc-renderer-exceptions.json')}
    names=sorted(p['package'] for p in native.values() if p['package'])
    config='schema_version = 1\nproject = '+json.dumps(repo)+'\n'
    if profile=='mel':
        config+='renderer_exceptions = ["AMS.MEL.IR.Health_Status.Metadata.Status"]\n'
    config+='[gnatdoc]\nversion = "26.0.0"\n[sources]\n'
    config+='directories = ["qualification-public"]\npackages = '+json.dumps(names)+'\n'
    config+='comment_style = "'+('trailing' if profile=='mel' else 'leading')+'"\n'
    config+='[navigation]\nmode = "'+('operations' if profile in ('imgproc','geometry') else 'packages')+'"\n'
    if profile in ('imgproc','geometry'):config+='categories = "docs/api-categories.json"\n'
    return {'schema_version':1,'repository':'https://github.com/zackboll/'+repo,
            'revision':sha,'gnatdoc':'GNATdoc 26.0.0 (20260415)',
            'compiler':'GNAT 16.1.0','gprbuild':'GPRBUILD 26.0.0 (2026-04-15); Alire release 26.0.1',
            'evidence_level':'full native API site; authored consumer portal not included',
            'source_sha256':source_hashes,'pristine_sha256':hashes(site),
            'public_sources':public,'public_packages':names,
            'configuration':config,'blockers':BLOCKERS[profile]}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=PINS,required=True)
    p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--site',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(sorted_json(record(a.profile,a.snapshot,a.site)),encoding='utf-8')