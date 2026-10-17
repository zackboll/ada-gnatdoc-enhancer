#!/usr/bin/env python3
"""GNATDOC-006 offline qualification; original GNATDOC-002/005 inputs required.

Only isolated copies are written. Historical evidence and consumers are read-only.
The upstream reference is actually executed, not inferred from renderer arithmetic.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.generic_instances import ANCHOR, CLASS, ELEMENTS, MEMBERS, discover, summaries
from ada_gnatdoc_enhancer.inventory import packages, normalized
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.pipeline import verify
from ada_gnatdoc_enhancer.qualification import check_snapshot, hashes, run
from ada_gnatdoc_enhancer.util import digest, require, sorted_json
from ada_gnatdoc_enhancer.validation import Page

REPOSITORY = Path(__file__).resolve().parents[1]
PIN = 'c5545eee815431568495c6c76af83df56cf5c3dd'


def write(path, data):
    path.write_text(sorted_json(data), encoding='utf-8')


def baseline():
    reviewed = json.loads((REPOSITORY/'docs/evidence/gnatdoc002/core-instances.json').read_text())
    require(len(reviewed) == 25, 'reviewed baseline count changed')
    return {v['package'].lower(): {k: v[k] for k in ('package', 'template', 'element_type', 'dimensions')} |
            {'element_owner': ELEMENTS[v['element_type']][0]} for v in reviewed}


def core_record(root, pristine):
    """Re-parse real sources and observed pages BEFORE creating qualification."""
    config = load(root, 'qualification.toml')
    source = packages(config); native = snapshot(config, pristine)
    instances, _ = discover(source, baseline())
    return {'schema_version': 1, 'instances': instances,
            'source_sha256': {p.path.relative_to(root).as_posix(): digest(p.path.read_bytes())
                              for p in source.values()},
            'native_sha256': hashes(pristine)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquisition', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True, help='GNATDOC-005 qualification workspace')
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.workspace.exists() and not args.output.exists(), 'outputs must be new')
    args.workspace.mkdir(parents=True); args.output.mkdir(parents=True)
    historical = REPOSITORY/'docs/evidence/gnatdoc002'
    spec = json.loads((historical/'core-input.json').read_text())
    require(spec['revision'] == PIN, 'wrong Core source pin')
    acquisition = args.acquisition/'core'
    check_snapshot(acquisition/'snapshot', spec['source_sha256'])
    require(hashes(acquisition/'pristine') == spec['pristine_sha256'], 'original pristine hash mismatch')
    # Use the previously staged public set only after reconciling it to the
    # original acquisition; no filename-based vector inventory is permitted.
    root = args.previous/'core/first'
    config = load(root, 'qualification.toml'); source = packages(config)
    for p in source.values():
        original = p.path.relative_to(root/'qualification-public').as_posix()
        require(digest(p.path.read_bytes()) == spec['source_sha256'][original], 'staged source mismatch')
    record = core_record(root, acquisition/'pristine')
    record_path = args.output/'core-generic-qualification.json'; write(record_path, record)
    isolated = args.workspace/'core-source'
    shutil.copytree(acquisition/'snapshot', isolated)
    shutil.copyfile(record_path, isolated/'generic-qualification.json')
    spec['source_sha256']['generic-qualification.json'] = digest(record_path.read_bytes())
    spec['configuration'] += ('\n[generic_instances]\nqualification = "generic-qualification.json"\nsha256 = "' +
                              digest(record_path.read_bytes()) + '"\n')
    spec['blockers'] = ['Production consumer adoption and publication outside scope']
    spec_path = args.output/'core-input.json'; write(spec_path, spec)
    matrix = {}
    for name in ('core', 'imgproc', 'geometry', 'mel'):
        current = spec_path
        if name != 'core':
            # GNATDOC-005 input specifications retain historical dependency IDs.
            current = REPOSITORY/'docs/evidence/gnatdoc005'/(name+'-input.json')
        report = run(current, isolated if name == 'core' else args.acquisition/name/'snapshot',
                     args.acquisition/name/'pristine', args.workspace/name,
                     dependency_bundle=args.previous/'bundle' if name in ('imgproc', 'geometry') else None)
        require(report['structural_result'] == 'pass', str(report.get('failure')))
        cfg = load(args.workspace/name/'first', 'qualification.toml')
        publication = verify(cfg, args.workspace/name/'first/_site')
        for field, value in {'public_packages': {'core':195,'imgproc':1,'geometry':2,'mel':29}[name],
                             'linked_local_types': {'core':2459,'imgproc':326,'geometry':171,'mel':1418}[name],
                             'linked_external_types': {'core':0,'imgproc':549,'geometry':95,'mel':0}[name]}.items():
            require(publication[field] == value, f'{name} {field} regression')
        require(report['checks']['native_integrity']['declarations'] ==
                {'core':1268,'imgproc':314,'geometry':130,'mel':1237}[name], 'native declaration regression')
        report['checks'].pop('source_inventory', None); report.pop('native_inventory', None)
        write(args.output/(name+'-report.json'), report)
        matrix[name] = {'revision':report['revision'], 'structural_result':'pass',
                        'publication':publication, 'native_integrity':report['checks']['native_integrity'],
                        'determinism':report['checks']['determinism'], 'idempotence':report['checks']['idempotence']}
        print(name, publication, flush=True)
    write(args.output/'compatibility-matrix.json', matrix)
    cfg = load(args.workspace/'core/first', 'qualification.toml')
    source = packages(cfg); native = snapshot(cfg, acquisition/'pristine')
    sections, counts = summaries(cfg, source, native); targets = verified_types(native, source)
    reviewed = json.loads((historical/'core-instances.json').read_text())
    inventory = []; discrepancies = []
    for key, item in sorted(record['instances'].items()):
        page = native.pages[key]; package = source[key]; name = 'api/'+page.path.name
        original = next(v for v in reviewed if v['package'].lower() == key)
        source_name = package.path.relative_to(cfg.root/'qualification-public').as_posix()
        if original['source'] != package.path.name or original['source_sha256'] != digest(package.path.read_bytes()):
            discrepancies.append({'package':item['package'], 'historical_source':original['source'],
                                   'verified_source':source_name, 'classification':'historical source attribution error'})
        require(original['native_path'] == name, 'historical native destination mismatch')
        parsed = Page(sections[name])
        actual = (args.workspace/'core/first/_site'/name).read_text()
        require(actual.count(sections[name]) == 1 and Page(sections[name]).links == parsed.links,
                'rendered summary differs')
        # Validate every actual link using the independently observed native IDs.
        pages = {p.path.name: Page(p.original) for p in native.pages.values()}
        for link in parsed.links:
            filename, _, fragment = link.partition('#')
            require(filename in pages and (not fragment or fragment in pages[filename].ids), 'bad summary target')
        inventory.append({**item, 'source':source_name,'source_sha256':digest(package.path.read_bytes()),
                          'native_path':name,'native_sha256':digest(page.original.encode()),
                          'existing_anchors':Page(page.original).ids, 'native_member_declarations':len(page.sections),
                          'presentation_anchor':ANCHOR,'summary_sha256':digest(sections[name].encode()),
                          'hyperlinks':parsed.links})
    require(sum(len(v['hyperlinks']) for v in inventory) == 102, 'observed hyperlink total mismatch')
    write(args.output/'instance-inventory.json', inventory)
    # Full-site instance-specific tamper rejection, not merely reduced tests.
    tampering = []
    published = args.workspace/'core/first/_site'
    for item in inventory:
        path = published/item['native_path']; original = path.read_bytes()
        section = sections[item['native_path']]
        changes = {
            'missing_summary': original.replace(section.encode(), b'', 1),
            'duplicate_summary': original + section.encode(),
            'changed_argument': original.replace(b'<td>'+str(item['dimensions'][0]).encode()+b'</td>',
                                                  b'<td>99</td>', 1),
            'missing_member_link': re.sub(rb'<a href="[^\"]+">(?:Vector|Matrix)</a>',
                                            b'Array', original, count=1),
            'swapped_existing_member_target': original.replace(item['hyperlinks'][1].encode(),
                                                               item['hyperlinks'][-1].encode(), 1),
        }
        for label, changed in changes.items():
            require(original != changed, 'ineffective full-site mutation')
            try:
                path.write_bytes(changed)
                try: verify(cfg, published)
                except ValueError as exc:
                    tampering.append({'package':item['package'],'mutation':label,'rejected':True,'reason':str(exc)})
                else: raise ValueError('accepted generic full-site tampering: '+label)
            finally: path.write_bytes(original)
    verify(cfg, published)
    write(args.output/'full-site-summary-tampering.json', tampering)
    write(args.output/'historical-inventory-discrepancies.json', discrepancies)
    write(args.output/'anchor-map.json', {k:{'page':v[0].name,'anchor':v[1],
          'source_declaration':source[k.rpartition('.')[0]].public_types[k.rpartition('.')[2]].signature,
          'source_declaration_sha256':digest(normalized(source[k.rpartition('.')[0]].public_types[k.rpartition('.')[2]].signature).encode()),
          'native_declaration_sha256':digest(next(s.code for s in native.pages[k.rpartition('.')[0]].sections if s.anchor==v[1]).encode())}
          for k,v in targets.items()
          if k in {t+'.'+m.lower() for t in MEMBERS for m in MEMBERS[t]} |
          {o+'.'+e.lower() for e,(o,_) in ELEMENTS.items()}})
    write(args.output/'template-fingerprints.json', {k:{'source_sha256':digest(source[k].path.read_bytes()),
          'normalized_declaration_sha256':digest(normalized(source[k].source).encode()),
          'members':{m:{'declaration':d,'normalized_declaration_sha256':digest(normalized(d).encode())}
                     for m,d in MEMBERS[k].items()}} for k in MEMBERS})
    # Execute original pinned reference, including its own integrity check.
    upstream = args.workspace/'upstream'; shutil.copytree(acquisition/'pristine', upstream)
    script = acquisition/'snapshot/scripts/enhance_gnatdoc_instances.py'
    commands = []; logs = []
    for suffix in ([], ['--check']):
        command = [sys.executable,str(script),str(upstream/'api'),'--sources',str(acquisition/'snapshot/src'),*suffix]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        commands.append(command); logs.append(result.stdout)
    parity = []
    for item in inventory:
        text = (upstream/item['native_path']).read_text()
        match = re.search(r'<section class="generic-instance-summary".*?</section>', text, re.S)
        require(match and text.count(CLASS) == 1, 'upstream summary coverage mismatch')
        old = Page(match[0]); new = Page(sections[item['native_path']])
        require(sorted(old.links) == sorted(new.links), 'upstream hyperlink parity failed')
        # Exact remaining prose/table parity is stronger than a loose keyword
        # assertion: only the individually classified additions are excluded.
        import html
        comparable = sections[item['native_path']].replace('<p>Instance: '+html.escape(item['package'])+'</p>', '', 1)
        comparable = comparable.replace(' Ada array assignment is distinct from OpenCV Mat storage ownership.', '', 1)
        require(html.unescape(comparable) == html.unescape(match[0]),
                'upstream member/argument/ownership semantic parity failed')
        parity.append({'package':item['package'],'hyperlinks':'identical destinations',
                       'differences':[{'classification':'intentional improvement',
                           'detail':'explicit qualified instance identity and Ada assignment/Mat ownership distinction'},
                          {'classification':'equivalent presentation','detail':'shared theme rather than Core theme'}]})
        if item['template'] == 'opencv.core.fixed_matrices':
            parity[-1]['differences'].append({'classification':'intentional improvement',
                'detail':'ASCII character reference for multiplication sign avoids charset-less HTTP mojibake'})
    write(args.output/'upstream-parity.json', {'executed':True,'revision':PIN,'script_sha256':digest(script.read_bytes()),
          'commands':commands,'stdout':logs,'instances':parity,'counts':counts,
          'scope':'executed original instance enhancer and --check, not entire consumer publication pipeline'})


if __name__ == '__main__': main()