#!/usr/bin/env python3
"""Offline GNATDOC-005 full-site qualification using independently acquired inputs.

Requires the original GNATDOC-002 acquisition AND both new dependency sites.
Does not run consumer postprocessing, deployment, or modify source checkouts.
Outputs must be new. Hosted CI uses reduced fixtures instead of this driver.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from acquire_real_sites import DEPENDENCIES
from record_real_site import record
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.external_types import destinations, inventory
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.pipeline import verify
from ada_gnatdoc_enhancer.qualification import hashes, run
from ada_gnatdoc_enhancer.syntax import TYPE_LINK, resolve, type_positions
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

REPOSITORY=Path(__file__).resolve().parents[1]


def write(path,data):
    path.write_text(sorted_json(data),encoding='utf-8')


def candidate_audit(root,pristine,manifest,candidates):
    config=load(root,'qualification.toml');source=packages(config)
    native=snapshot(config,pristine);local=verified_types(native,source)
    external=destinations(config);occurrences=[]
    for key,page in sorted(native.pages.items()):
        published=(root/'_site/api'/page.path.name).read_text()
        for section in page.sections:
            positions={(a,b) for a,b,_ in type_positions(section.code)}
            for name in sorted(candidates):
                for match in re.finditer(r'(?<![\w.])'+re.escape(name)+r'(?![\w.])',section.code,re.I):
                    target=manifest['types'].get(name.lower())
                    resolution=resolve(name,source[key],source,local,external)
                    if (match.start(),match.end()) not in positions:
                        status='unsupported';reason='outside supported typed contexts'
                    elif target is None:
                        status='unresolved';reason='no qualified source-owned dependency type'
                    elif resolution is None:
                        status='unresolved';reason='visibility or shadowing protection'
                    elif resolution[1]!='external':
                        status='unresolved';reason='local ownership takes precedence'
                    else:
                        status='linked';reason='qualified source/native anchor and supported visible type mark'
                    occurrences.append({'type':name,'package':page.package,'page':page.path.name,
                        'consumer_anchor':section.anchor,'signature_sha256':digest(section.code.encode()),
                        'offset':match.start(),'status':status,'reason':reason,
                        'destination':external.get(name.lower()) if status=='linked' else None,
                        'proof':target})
        # Count actual output independently of candidate classification.
        actual=sum(m[1].startswith('https://') for m in TYPE_LINK.finditer(published))
        require(actual==sum(x['status']=='linked' for x in occurrences if x['page']==page.path.name),
                'candidate audit and rendered external link count disagree')
    counts={k:sum(x['status']==k for x in occurrences)
            for k in ('linked','unresolved','ambiguous','unsupported')}
    return {'candidate_occurrences':len(occurrences),'eligible':counts['linked'],
            **counts,'occurrences':occurrences,
            'classification':'candidate spelling is never automatic linking credit'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquisition',required=True,type=Path)
    parser.add_argument('--dependencies',required=True,type=Path)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    require(not args.workspace.exists() and not args.output.exists(),'workspace/output must be new')
    args.workspace.mkdir(parents=True);args.output.mkdir(parents=True)
    bundle=args.workspace/'bundle';bundle.mkdir()
    manifests={};specs={}
    for name,(_,sha) in DEPENDENCIES.items():
        acquisition=args.dependencies/name
        spec=record('core',acquisition/'snapshot',acquisition/'pristine')
        spec['revision']=sha
        spec['blockers']=['Generic-instance members intentionally unsupported',
                          'Production publication unqualified']
        spec['acquisition']={'detached_commit':sha,'release':name.removeprefix('core-'),
            'commands_sha256':digest((args.dependencies/'commands.log').read_bytes()),
            'source_checkout':'isolated detached clone','native_generation':'no consumer postprocessing',
            'harness_sha256':{n:digest((acquisition/n).read_bytes())
                for n in ('docs_api.gpr','docs_internal.gpr') if (acquisition/n).exists()}}
        target=bundle/name;target.mkdir()
        shutil.copytree(acquisition/'snapshot',target/'source')
        shutil.copytree(acquisition/'pristine',target/'native')
        manifest=inventory(spec,target/'source',target/'native')
        require(manifest==inventory(spec,target/'source',target/'native'),'dependency inventory nondeterminism')
        for filename,data in (('input.json',spec),('types.json',manifest)):
            write(target/filename,data);write(args.output/(name+'-'+filename),data)
        manifests[name]=manifest;specs[name]=spec
        print(name,'anchors',len(manifest['types']),flush=True)
    historical=REPOSITORY/'docs/evidence/gnatdoc002'
    candidates=json.loads((historical/'external-references.json').read_text())
    mapping={};matrix={}
    for name in ('core','imgproc','geometry','mel'):
        original=historical/(name+'-input.json')
        spec=json.loads(original.read_text());dep=None
        if name in ('imgproc','geometry'):
            dep='core-'+('0.4.1' if name=='imgproc' else '0.5.0')
            sha=specs[dep]['revision'];prefix='qualification-dependencies/'+dep+'/'
            entry={'repository':specs[dep]['repository'],'revision':sha,
                'manifest':prefix+'types.json','manifest_sha256':digest((bundle/dep/'types.json').read_bytes()),
                'acquisition':prefix+'input.json','acquisition_sha256':digest((bundle/dep/'input.json').read_bytes()),
                'source':prefix+'source','site':prefix+'native',
                'base_url':'https://core.invalid/'+sha+'/api/','publication':'offline-test',
                'types':sorted(candidates[name]['references'])}
            spec['configuration']+='\n[security]\nexternal_hosts = ["core.invalid"]\n[[external_dependencies]]\n'
            spec['configuration']+='\n'.join(k+' = '+json.dumps(v) for k,v in entry.items())+'\n'
            mapping[name]={'consumer_revision':spec['revision'],**entry}
        spec['blockers']=['Published version-stable dependency deployment unavailable',
                          'Authored guides and consumer adoption outside scope']
        spec_path=args.output/(name+'-input.json');write(spec_path,spec)
        acquisition=args.acquisition/name;workspace=args.workspace/name
        report=run(spec_path,acquisition/'snapshot',acquisition/'pristine',workspace,
                   dependency_bundle=bundle if dep else None)
        require(report['structural_result']=='pass',str(report.get('failure')))
        # Independently rerun publication reconstruction and ratchet expected
        # local counts, not total type links including external destinations.
        config=load(workspace/'first','qualification.toml')
        publication=verify(config,workspace/'first/_site')
        expected={'core':2459,'imgproc':326,'geometry':171,'mel':1418}[name]
        require(publication['linked_local_types']==expected,'local type link regression')
        if dep:
            audit=candidate_audit(workspace/'first',acquisition/'pristine',
                                  manifests[dep],candidates[name]['references'])
            write(args.output/(name+'-references.json'),audit)
            require(audit['linked']==publication['linked_external_types'],'external count mismatch')
        # Compact structural evidence retains every check and full input/output
        # hash; original native inventory is already independently preserved.
        report['checks'].pop('source_inventory',None)
        report.pop('native_inventory',None)
        report['historical_input_spec_sha256']=digest(original.read_bytes())
        report['external_publication']='offline-test mapping; no public deployment verified'
        write(args.output/(name+'-report.json'),report)
        matrix[name]={'revision':spec['revision'],'structural_result':report['structural_result'],
            'packages':publication['public_packages'],'local_type_links':publication['linked_local_types'],
            'external_type_links':publication['linked_external_types'],
            'native_sections':report['checks']['native_integrity']['declarations'],
            'determinism':report['checks']['determinism'],'idempotence':report['checks']['idempotence']}
        print(name,matrix[name],flush=True)
    write(args.output/'consumer-dependencies.json',mapping)
    write(args.output/'compatibility-matrix.json',matrix)


if __name__=='__main__':main()