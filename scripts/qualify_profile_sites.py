#!/usr/bin/env python3
"""Requalify GNATDOC-002 acquisitions without rebuilding/modifying consumers.

Inputs are checked against historical source/native inventories by run().
Output is GNATDOC-003 evidence, never an overwrite of GNATDOC-002 evidence.
The audit visits every scanner declaration even when qualification fails early.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import SECTION
from ada_gnatdoc_enhancer.profiles import reconcile
from ada_gnatdoc_enhancer.qualification import run
from ada_gnatdoc_enhancer.util import digest, sorted_json

REPOSITORY=Path(__file__).resolve().parents[1]


def audit(workspace, pristine):
    config=load(workspace/'first','qualification.toml')
    accepted=[];unsupported=[]
    for pkg in packages(config).values():
        # Observed page identity, not a generated hashed destination.
        pages=[p for p in (pristine/'api').glob('*.html')
               if '<h1>'+pkg.name+'</h1>' in p.read_text(encoding='utf-8')]
        if len(pages)!=1:raise ValueError('audit requires unique observed package page')
        page=pages[0]
        sections=[(m[3],html.unescape(m[4]),m[1] or m[2])
                  for m in SECTION.finditer(page.read_text(encoding='utf-8'))]
        for decl in pkg.declarations:
            candidates=[s for s in sections if s[0].lower()==decl.name.lower()]
            found=[(s,reconcile(decl.signature,s[1])) for s in candidates
                   if reconcile(decl.signature,s[1]) is not None]
            identity={'package':pkg.name,'name':decl.name,'line':decl.line,
                      'source_path':pkg.path.relative_to(config.root/'qualification-public').as_posix(),
                      'source_file_sha256':digest(pkg.path.read_bytes()),
                      'source_declaration_sha256':digest(decl.signature.encode()),
                      'page':page.name}
            if len(found)!=1:
                unsupported.append({**identity,'phase':'inventory',
                    'source_signature':decl.signature,'native_signatures':[s[1] for s in candidates],
                    'reason':'no unique supported source/native presentation equivalence'})
            elif found[0][1].rule!='exact':
                section,projection=found[0]
                accepted.append({**identity,'anchor':section[2],
                    'native_signature_sha256':digest(section[1].encode()),
                    'rule':projection.rule,'hidden_literals':projection.hidden_literals,
                    'omitted_text_ownership':'source only; not visibly rendered by GNATdoc'})
    return {'accepted_projections':accepted,'unsupported':unsupported,
            'scope':'all scanner types/subtypes/named calls; not full consumer coverage'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquisition',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.workspace.exists() or args.output.exists():
        parser.error('workspace and evidence output must be new')
    args.output.mkdir(parents=True)
    for name in ('core','imgproc','geometry','mel'):
        spec=REPOSITORY/'docs/evidence/gnatdoc002'/f'{name}-input.json'
        acquisition=args.acquisition/name
        workspace=args.workspace/name
        report=run(spec,acquisition/'snapshot',acquisition/'pristine',workspace)
        report['historical_input_spec_sha256']=digest(spec.read_bytes())
        report['task']='GNATDOC-003'
        report['blocker_interpretation']='blockers copied from historical acquisition are BEFORE results; consult profile audit for current matching'
        (args.output/f'{name}-report.json').write_text(sorted_json(report))
        result=audit(workspace,acquisition/'pristine')
        (args.output/f'{name}-profiles.json').write_text(sorted_json(result))
        print(name,report['structural_result'],report.get('failure'),flush=True)


if __name__=='__main__':main()