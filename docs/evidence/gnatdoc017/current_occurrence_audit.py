#!/usr/bin/env python3
"""GNATDOC-011R1 occurrence oracle, independent of the shared resolver.

Only the unchanged Core source/native scanner and genuine legacy publication
establish expected occurrences. Candidate HTML is compared at decoded type-mark
offsets, not aggregate counters. Each source declaration, context import,
instantiation and observed destination is retained for review and browser use.
Run in a fresh process for each pinned revision to isolate consumer imports.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True


def require(ok, why):
    if not ok:raise ValueError('independent occurrence audit: '+why)


def source_text(source, declaration):
    return '\n'.join(source.lines[declaration['start']-1:declaration['end']])


def audit(core, pristine, legacy, candidate, baseline):
    revision = subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip()
    require(revision in {'33a2a4f3b83606a5c779b8a93abeb6c91fa49a21',
                         'f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'}, 'wrong source pin')
    require(not subprocess.check_output(['git','-C',str(core),'diff','HEAD','--','src','scripts']),
            'modified consumer sources/oracle')
    sys.path.insert(0,str(core/'scripts'))
    import link_gnatdoc_types as oracle
    import enhance_gnatdoc_instances as instances
    from highlight_gnatdoc_ada import strip_highlighting
    source = oracle.sources(core/'src')
    pages, native_targets = oracle.pages_and_targets(pristine/'api',source)
    # The oracle rechecks legacy instance source, exact summaries, pristine
    # originals and template/type anchors; legacy metadata alone is not trusted.
    qualified, _ = instances.process(legacy/'api',core/'src',check=True)
    require(qualified == instances.qualified_instances(), 'unapproved instance families')
    explanatory = dict(native_targets)
    legacy_pages, _ = oracle.pages_and_targets(legacy/'api',source)
    oracle.instance_targets(legacy/'api',core/'src',source,legacy_pages,explanatory)
    approved_summaries = {}
    for instance in qualified:
        filename = pages[instance][0].name
        old = re.search(r'<section class="generic-instance-summary".*?</section>',legacy_pages[instance][1],re.S)
        published = (candidate/'api'/filename).read_text()
        found = re.findall(r'<section class="generic-instance-summary".*?</section>',published,re.S)
        require(old is not None and len(found)==1 and
                published.count('id="instance-members-summary"')==1 and '<h4' not in published,
                'missing/duplicate explanatory section or false native declaration')
        canonical_name = re.search(r'<h1>([^<]+)</h1>',legacy_pages[instance][1])[1]
        # Existing reviewed shared summaries add only these two explicit
        # explanatory labels. Reconstruct the rest using the legacy oracle.
        expected = old[0].replace('<p>Generic template:', '<p>Instance: '+canonical_name+'</p><p>Generic template:',1)
        expected = expected.replace('this generic introduces no native handle.</p>',
            'this generic introduces no native handle. Ada array assignment is distinct from OpenCV Mat storage ownership.</p>',1)
        expected = expected.encode('ascii','xmlcharrefreplace').decode('ascii')
        require(found[0] == expected,'explanatory section differs from independent reconstruction')
        approved_summaries[instance] = found[0]
    navigation = (candidate/'api/index.html').read_text()
    indexed = re.findall(r'<a href="([^"]+)" data-instance="([^"]+)"></a>',navigation)
    expected_index = {identity:filename+'#'+fragment for identity,(filename,fragment) in explanatory.items()
                      if identity not in native_targets}
    require(len(indexed)==len(expected_index) and {identity:url for url,identity in indexed}==expected_index,
            'forged/missing instance-reference navigation authority')
    def links(raw):
        raw = strip_highlighting(raw); result = {}
        for m in oracle.LINK.finditer(raw):
            a = len(html.unescape(oracle.LINK.sub(lambda x:x[3],raw[:m.start()])))
            label = html.unescape(m[3]); b = a+len(label)
            require((a,b) not in result, 'duplicate type-mark span')
            result[a,b] = {'identity':m[2], 'url':html.unescape(m[1]), 'label':label}
        return html.unescape(oracle.plain(raw)), result
    def sections(site, filename):
        return {m[1]:m for m in oracle.SECTION.finditer((site/'api'/filename).read_text())}
    ledger = []; extras = []; all_legacy = 0; all_shared = 0; missing = []
    inventory = {}
    for owner, (path, _, original_sections) in sorted(pages.items()):
        current = sections(candidate,path.name); old = sections(legacy,path.name)
        off = sections(baseline,path.name)
        require(set(current) == set(old) == set(off) == {s[1] for s in original_sections}, 'native section identity changed')
        for native in original_sections:
            anchor = native[1]; rendered = html.unescape(native[3])
            declaration = source[owner].match(native[3]); full = source_text(source[owner],declaration)
            tokens = oracle.tokens(rendered); owned = oracle.tokens(full)
            require([x[0] for x in tokens] == [x[0] for x in owned[:len(tokens)]], 'source/native token alignment')
            actual_text, actual = links(current[anchor][3]); old_text, historical = links(old[anchor][3])
            off_text, disabled = links(off[anchor][3])
            require(actual_text == old_text == off_text == rendered, 'visible Ada declaration changed')
            all_legacy += len(historical); all_shared += len(actual)
            positions = {(a,b):name for name,a,b in oracle.type_positions(rendered)}
            for (a,b), link in historical.items():
                expected = dict(link)
                expected['url'] = path.name+link['url'] if link['url'].startswith('#') else link['url']
                observed = actual.get((a,b))
                normalized = dict(observed) if observed else None
                if normalized and normalized['url'].startswith('#'):normalized['url'] = path.name+normalized['url']
                if normalized != expected:missing.append({'page':path.name,'anchor':anchor,'span':[a,b],'expected':expected,'actual':normalized})
                if not link['url'].endswith('#instance-members-summary'):continue
                require((a,b) in positions, 'legacy link not in a type-mark context')
                identity, status = oracle.resolve(positions[a,b],owner,declaration,source,explanatory)
                require(identity == link['identity'] and status == 'linked', 'independent visibility resolution failed')
                instance = identity.rpartition('.')[0]; template, element, dimensions = qualified[instance]
                require(instance not in native_targets and identity not in native_targets, 'synthetic native symbol authority')
                require(explanatory[identity] == (pages[instance][0].name,'instance-members-summary'), 'wrong existing summary page')
                require(native_targets[template+'.'+identity.rsplit('.',1)[1]][0] == pages[template][0].name,
                        'template member destination mismatch')
                ti = next(i for i,t in enumerate(tokens) if t[1:]==(a,b)); sa,sb = owned[ti][1:]
                require(full[sa:sb].lower() == rendered[a:b].lower(), 'source type span mismatch')
                context = source[owner].code.split('package',1)[0]
                require(instance in source[owner].imports, 'missing ordinary exact import')
                summary = approved_summaries[instance]
                summary_links = re.findall(r'<a href="([^"]+)">([^<]+)</a>',summary)
                source_instance = source[instance]
                row = {'occurrence':len(ledger)+1,'source_package':owner,'source_file':next(
                    p.relative_to(core).as_posix() for p in (core/'src').glob('*.ads') if '\n'.join(p.read_text().splitlines()) == '\n'.join(source[owner].lines)),
                    'declaration':declaration['scope'],'declaration_line':declaration['start'],
                    'complete_source_declaration':full,'native_profile':rendered,
                    'source_type_span':[sa,sb],'source_type_line':declaration['start']+full[:sa].count('\n'),
                    'native_type_span':[a,b],'type_mark':rendered[a:b],'identity':identity,
                    'visibility':{'ordinary_import':instance,'all_ordinary_imports':sorted(source[owner].imports),
                                  'context':context,'legacy_oracle_status':status,'qualified_resolution':'exact imported owner under lexical ancestors; no suffix search'},
                    'instance_source':'\n'.join(source_instance.lines),'template':template,'actual_type':element,
                    'dimensions':dimensions,'template_source':'\n'.join(source[template].lines),
                    'source_page':path.name,'source_anchor':anchor,'destination_page':pages[instance][0].name,
                    'summary_anchor':'instance-members-summary','summary_sha256':hashlib.sha256(summary.encode()).hexdigest(),
                    'summary_links':[{'url':u,'label':html.unescape(label)} for u,label in summary_links],
                    'legacy':expected,'shared':normalized,'disabled':disabled.get((a,b)),
                    'classification':'pass' if normalized == expected else 'fail'}
                require(row['disabled'] is None, 'negative-first link unexpectedly present')
                ledger.append(row)
                inventory[identity] = {'instance':instance,'template':template,'element':element,'dimensions':dimensions,
                                       'page':pages[instance][0].name,'anchor':'instance-members-summary',
                                       'native_declarations':len(pages[instance][2])}
            for span, link in actual.items():
                if span in historical:continue
                a,b = span
                require(link['identity'] == 'opencv.size' and rendered[a:b].lower() == 'size', 'unexplained extra reference')
                ti = next(i for i,t in enumerate(tokens) if t[1:]==span); sa,sb = owned[ti][1:]
                identity,status = oracle.resolve('size',owner,declaration,source,native_targets)
                blockers = source['opencv'].members.get('size',[])
                require(status == 'ambiguous' and len(blockers)>1, 'legacy Size difference unexplained')
                require(owner == 'opencv.core' and not source[owner].members.get('size') and
                        {d['scope'] for d in blockers} == {'OpenCV.Size','OpenCV.Rotated_Rect.Size'},
                        'Size ownership/blocker census changed')
                require(native_targets['opencv.size'] == tuple(link['url'].split('#')), 'wrong Size native destination')
                extras.append({'source_package':owner,'declaration':declaration['scope'],'line':declaration['start'],
                    'complete_source_declaration':full,'source_type_span':[sa,sb],'native_type_span':[a,b],
                    'source_page':path.name,'source_anchor':anchor,'link':link,'native_profile':rendered,
                    'legacy_status':status,'legacy_blockers':blockers,
                    'classification':'legitimate source-verified improvement: OpenCV.Size is ancestor-visible; Rotated_Rect.Size is a record component, not a package-visible homograph',
                    'legacy_reason':'legacy Source.members deliberately treats deeper component names as potential blockers; its conservative ambiguity is not an Ada visibility conflict'})
    return {'revision':revision,'public_packages':len(pages),'native_sections':sum(len(p[2]) for p in pages.values()),
            'public_symbols':len(native_targets),'legacy_type_references':all_legacy,'shared_type_references':all_shared,
            'incoming_occurrences':len(ledger),'incoming_by_destination':dict(Counter(r['identity'] for r in ledger)),
            'targets':inventory,'occurrences':ledger,'missing':missing,'additional_Size':extras,
            'all_approved_incoming_restored':all(r['classification']=='pass' for r in ledger)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('core','pristine','legacy','candidate','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args(); require(not a.output.exists(),'report must be new')
    result = audit(a.core,a.pristine,a.legacy,a.candidate,a.baseline)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print({k:result[k] for k in ('revision','legacy_type_references','shared_type_references','incoming_occurrences','all_approved_incoming_restored')})


if __name__ == '__main__':main()