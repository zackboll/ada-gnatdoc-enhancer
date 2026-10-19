#!/usr/bin/env python3
"""Independent occurrence oracle and fresh same-base MEL qualification.

No production resolver, extractor, emitted manifest or counters grant authority.
The unchanged consumer inventory supplies immutable declarations/native ledger;
its current auditor is never modified, subclassed or monkeypatched. New short
owners are independently admitted here only for the explicit source census.
"""
from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import html
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

# Reading pinned consumer inventory must not create interpreter-specific cache
# files in the isolated input tree (including when changing Python versions).
sys.dont_write_bytecode = True

REVISION = 'a5484514cfae3b7bccde078118b838fa40ce4d0e'
BASE = '23cf51d3765e7b3f68411e25a57f52f4c0efc7e1'
IMAGE = 'ams.mel.ir.image'
INSTRUMENTATION = 'ams.mel.ir.instrumentation'
REQUIRED = (
    (IMAGE, 'sensor_inertial_state', 'uncertainty', 'uncertainty', 98),
    (IMAGE, 'sensor_nav_state', 'orientation', 'orientation', 122),
    (IMAGE, 'sensor_nav_state', 'orientation_velocity', 'orientation', 124),
    (IMAGE, 'sensor_nav_state', 'orientation_acceleration', 'orientation', 126),
    (IMAGE, 'sensor_nav_state', 'coordinate_system', 'coordinate_system', 128),
    (IMAGE, 'navigation_report', 'attitude_rate', 'attitude_rate', 666),
    (IMAGE, 'navigation_report', 'position_velocity_covariance', 'position_velocity_covariance', 672),
    (INSTRUMENTATION, 'instrumentation_level_command', 'priority', 'priority', 87),
    (INSTRUMENTATION, 'instrumentation_report', 'priority', 'priority', 98),
)
SECTION = re.compile(r'(<h4 id=([a-f0-9]{64})>[^<]+</h4>\s*<pre class=ada-code-snippet><code>)(.*?)(</code></pre>)', re.S)
LINK = re.compile(r'<a class="type-reference" href="([^"<>]+)" data-type="([a-z0-9_.]+)">([^<>]+)</a>')
SPAN = re.compile(r'<span class="ada-(keyword|number|string|character|attribute|comment|operator)">([^<]*)</span>')


def require(ok, message):
    if not ok:
        raise ValueError('current-package independent audit: '+message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hashes(root):
    require(root.is_dir() and not any(p.is_symlink() for p in (root,*root.parents)), 'unsafe input root')
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'symlink input member')
        if path.is_dir():continue
        require(path.is_file(), 'nonregular input member')
        result[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    return result


def write(path, data):
    with path.open('x') as stream:
        stream.write(json.dumps(data,indent=2,sort_keys=True)+'\n')


class Snippet(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.text = ''
        self.links = []
        self.active = None
        self.feed(raw)
        self.close()
        require(self.active is None, 'unclosed link')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            require(self.active is None and set(attrs)=={'class','href','data-type'} and
                    attrs['class']=='type-reference', 'unexpected link markup')
            self.active = {'start':len(self.text),'href':attrs['href'],'identity':attrs['data-type']}
        else:
            require(tag=='span' and self.active is None and
                    re.fullmatch('ada-(keyword|number|string|character|attribute|comment|operator)',
                                 attrs.get('class','')) is not None, 'unexpected snippet markup')

    def handle_endtag(self, tag):
        if tag == 'a':
            require(self.active is not None, 'unexpected closing link')
            self.links.append({**self.active,'end':len(self.text)})
            self.active = None

    def handle_data(self, data):
        self.text += data


def check_snippet(raw, pristine, expected):
    """Exact complete-token and destination equality, independent of manifests."""
    parsed = Snippet(raw)
    require(parsed.text==pristine, 'visible declaration changed')
    actual = sorted(parsed.links,key=lambda x:x['start'])
    wanted = sorted(expected,key=lambda x:x['start'])
    require(actual==wanted, 'occurrence inventory/destination mismatch')
    restored = LINK.sub(lambda m:m[3], SPAN.sub(lambda m:m[2],raw))
    require('<' not in restored and html.unescape(restored)==pristine, 'non-flat restoration')
    return restored


def source_binding(authority, entry, tokens, first, last):
    source = authority.lex(entry['declaration'])
    matches = SequenceMatcher(None,[t[0] for t in tokens],[t[0] for t in source],autojunk=False)
    blocks = [b for b in matches.get_matching_blocks() if b.a<=first and last<b.a+b.size]
    require(len(blocks)==1,'token span lacks complete source ownership')
    b = blocks[0]; a = b.b+first-b.a; z = b.b+last-b.a
    return source[a][1],source[z][2]


def short_scope(root, owner, entry, lex):
    """Independent token walk: reject any unqualified short-name token publicly.

    Reject all possible defining uses, not only inventory declarations. This
    over-approximation intentionally includes harmless bare uses too.
    """
    tokens = lex((root/entry['source']).read_text())
    words = [t[0] for t in tokens]
    package = words.index('package')
    cursor = package+1; name = words[cursor]; cursor += 1
    while words[cursor]=='.':
        name += '.'+words[cursor+1]; cursor += 2
    require(name==owner and words[cursor]=='is' and 'generic' not in words[:package], 'source package identity/scope')
    public = words[cursor+1:]
    for i, word in enumerate(public):
        if word=='private' and (i+1==len(public) or public[i+1]!=';'):
            public = public[:i];break
    else:
        # Exclude the package end name, not a possible nested scope.
        end = len(public)-1
        while end>=0 and public[end]!='end':end -= 1
        require(end>=0,'missing source package end')
        public = public[:end]
    require(not set(public)&{'package','generic','renames','task','protected','begin','declare'}, 'unsupported scope')
    short = owner.split('.')[-1]
    for i, word in enumerate(public):
        if word==short:
            require((i and public[i-1]=='.') or (i+1<len(public) and public[i+1]=='.'), 'actual short-prefix shadow')
    return {'ordinary_public_package':owner,'actual_short_prefix':short,
            'full_unit_sha256':sha((root/entry['source']).read_bytes()),
            'public_scope':'flat; no bare short-prefix tokens, aliases or nested scopes'}


def oracle(root, pristine):
    # Read-only imports of the pinned independent consumer inventory. No change
    # to its acceptance contract; no candidate module participates in this oracle.
    sys.path.insert(0,str(root/'scripts'))
    sys.path.insert(0,str(root/'docs/tools'))
    import local_type_audit as consumer
    authority = consumer.Authority(root,pristine)
    expected = {}; baseline = {}; ledger = []; census = []
    for (page, anchor), entry in sorted(authority.sections.items()):
        text = entry['native']; tokens = consumer.lex(text); words = [t[0] for t in tokens]
        expected[page,anchor] = []; baseline[page,anchor] = []
        i = 0
        while i<len(tokens):
            if not consumer.IDENT.fullmatch(words[i]) or (i and words[i-1]=='.'):
                i += 1;continue
            j = i
            while j+2<len(tokens) and words[j+1]=='.' and consumer.IDENT.fullmatch(words[j+2]):j += 2
            start,end = tokens[i][1],tokens[j][2]; spelling = text[start:end]
            new = None
            try:
                if words[:1]==['subtype'] and i==3 and words[2]=='is':
                    # GNATDOC-009A admits only flat public source scopes. These
                    # independent tokens preserve that bounded eligibility;
                    # aliases elsewhere in a package still disqualify bases.
                    unit = consumer.lex((root/entry['source']).read_text())
                    unit_words = [t[0] for t in unit]
                    header = unit_words.index('package')
                    body = unit_words[unit_words.index('is',header)+1:]
                    for k,w in enumerate(body):
                        if w=='private' and (k+1==len(body) or body[k+1]!=';'):
                            body=body[:k];break
                    if set(body)&{'package','generic','task','protected','begin','declare'}:
                        i=j+1;continue
                    context='ordinary-subtype-base'
                else:context=consumer.type_context(tokens,i,end)
            except ValueError:
                i = j+1;continue
            for owner, declaration, component, target, line in REQUIRED:
                if (entry['package'],entry['name'].lower(),spelling.lower())==(owner,declaration,owner.split('.')[-1]+'.'+target):
                    # Three Orientation uses are distinguished by their defining
                    # component immediately before the colon, never spelling alone.
                    if i>=2 and words[i-1]==':' and words[i-2]==component:
                        new = (owner,component,target,line);break
            if new:
                identity = new[0]+'.'+new[2]; target = authority.types[identity]
                scope = short_scope(root,entry['package'],entry,consumer.lex)
            else:
                try:identity,target = authority.destination(spelling,entry['package'])
                except ValueError:
                    i = j+1;continue
                scope = {'ordinary_existing_rule':context}
            # Use independent lexical alignment, never production type_positions.
            adapter = type('Lex',(),{'lex':staticmethod(consumer.lex)})
            a,b = source_binding(adapter,entry,tokens,i,j)
            require(entry['declaration'][a:b].lower()==spelling.lower(), 'source spelling changed')
            source_line = entry['line']+entry['declaration'][:a].count('\n')
            if new:require(source_line==new[3],'source census line changed')
            href = target['page']+'#'+target['anchor']
            occurrence = {'start':start,'end':end,'identity':identity,'href':href}
            expected[page,anchor].append(occurrence)
            if not new:baseline[page,anchor].append(occurrence)
            row = {'revision':REVISION,'source':entry['source'],'declaration':entry['name'],
                   'component_or_formal':new[1] if new else None,'source_line':source_line,
                   'source_declaration':entry['declaration'],'source_span':[a,b],
                   'pristine':text,'pristine_span':[start,end],'spelling':spelling,
                   'containing_page':page,'containing_anchor':anchor,'destination_identity':identity,
                   'destination_page':target['page'],'destination_anchor':target['anchor'],
                   'destination_source':target,'scope':scope,
                   'baseline':'plain' if new else 'linked','candidate':'linked'}
            ledger.append(row)
            if new:census.append(row)
            i = j+1
    require(len(census)==9,'nine source/native-backed additions required')
    require(sum(map(len,baseline.values()))==1419 and sum(map(len,expected.values()))==1428,'independent census counts')
    return authority,baseline,expected,ledger,census


def audit_site(site, authority, expected):
    found = set(); total = 0
    for path in sorted((site/'api').glob('*.html')):
        text = path.read_text()
        for m in SECTION.finditer(text):
            key = path.name,m[2]
            require(key in authority.sections,'unowned native section')
            check_snippet(m[3],authority.sections[key]['native'],expected[key])
            found.add(key); total += len(expected[key])
        outside = SECTION.sub('',text)
        require('type-reference' not in outside,'extra link outside declarations')
    require(found==set(authority.sections),'missing source/native section')
    return total


def run_cli(python, root, site, log, *, dry=False, off=False):
    # Config bytes remain unchanged; types-off uses dataclasses.replace only in
    # a disposable subprocess, as an explicit control, not consumer adoption.
    code = ('from pathlib import Path; from dataclasses import replace; '
            'from ada_gnatdoc_enhancer.config import load; '
            'from ada_gnatdoc_enhancer.pipeline import enhance,verify; import json,sys; '
            'c=load(Path(sys.argv[1]),"docs/gnatdoc-enhance.toml"); '
            'c=replace(c,type_links=False) if sys.argv[4]=="off" else c; '
            'print(json.dumps(enhance(c,Path(sys.argv[2]),dry_run=sys.argv[3]=="dry"),sort_keys=True)); '
            'print(json.dumps(verify(c,Path(sys.argv[2])),sort_keys=True)) if sys.argv[3]!="dry" else None')
    command = [str(python),'-c',code,str(root),str(site),'dry' if dry else 'write','off' if off else 'on']
    write(log.with_suffix('.command.json'),command)
    with log.open('x') as stream:
        subprocess.run(command,check=True,stdout=stream,stderr=subprocess.STDOUT,
                       cwd=log.parent,env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'})


def mutations(out, site, authority, expected, census):
    """Real complete-publication copies; forged hashes never change the oracle."""
    row = next(r for r in census if r['declaration']=='Navigation_Report' and r['component_or_formal']=='attitude_rate')
    destination = row['destination_page']+'#'+row['destination_anchor']
    other = next(e for e in authority.types.values() if e['package']==IMAGE and e['name']=='North_East_Down')
    alternate = other['page']+'#'+other['anchor']
    wrong_page = next(e for e in authority.types.values() if e['package']==INSTRUMENTATION)
    changes = (
        ('wrong-existing-anchor',lambda s:s.replace(destination,alternate,1)),
        ('wrong-existing-page',lambda s:s.replace(destination,wrong_page['page']+'#'+wrong_page['anchor'],1)),
        ('consistent-forged-pair',lambda s:s.replace(destination,alternate,1).replace('data-type="'+row['destination_identity']+'"',
                                                                                   'data-type="'+IMAGE+'.north_east_down"',1)),
        ('forged-output-hash',lambda s:s.replace(destination,alternate,1)),
        ('removed-required-link',lambda s:s.replace('<a class="type-reference" href="'+destination+'" data-type="'+row['destination_identity']+'">'+row['spelling']+'</a>',row['spelling'],1)),
        ('unsupported-extra-link',lambda s:s.replace('System_Time_NS', '<a class="type-reference" href="'+destination+'" data-type="'+row['destination_identity']+'">System_Time_NS</a>',1)),
        ('changed-retained-north-east-down',lambda s:s.replace('href="'+alternate+'" data-type="'+IMAGE+'.north_east_down"',
                                                            'href="'+destination+'" data-type="'+IMAGE+'.north_east_down"',1)),
    )
    results = []
    for name,change in changes:
        copy = out/('tamper-'+name);shutil.copytree(site,copy)
        page = copy/'api'/row['containing_page'];before = page.read_text();after = change(before)
        require(before!=after,'mutation did not change publication: '+name);page.write_text(after)
        if name in ('forged-output-hash','consistent-forged-pair'):
            manifest = copy/'api/presentation.json';data=json.loads(manifest.read_text())
            data['output_sha256']['api/'+page.name]=sha(page.read_bytes())
            manifest.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
        try:audit_site(copy,authority,expected)
        except ValueError as error:results.append({'mutation':name,'rejected':True,'diagnosis':str(error)})
        else:raise ValueError('independent audit accepted tampering: '+name)
    return results


def run(args):
    root,pristine,out = args.source_root.resolve(),args.pristine.resolve(),args.workspace.resolve()
    require(not out.exists() and not out.is_symlink(),'workspace must be fresh')
    require(not any(out.is_relative_to(p) or p.is_relative_to(out) for p in (root,pristine)), 'workspace containment')
    out.mkdir(parents=True)
    before_source,before_pristine = hashes(root),hashes(pristine)
    sys.path.insert(0,str(root/'docs/tools'));sys.path.insert(0,str(root/'scripts'))
    import build_enhanced_site as consumer
    consumer.qualified_original(pristine,root)  # Unchanged trusted-input checker only.
    authority,baseline,expected,ledger,census = oracle(root,pristine)
    write(out/'complete-occurrence-ledger.json',ledger)
    write(out/'nine-occurrences.json',census)
    states = {}; reports = {}
    for label,python in (('baseline',args.baseline_python),('candidate',args.candidate_python)):
        sites = []
        for ordinal in ('first','second'):
            api = out/(label+'-api-'+ordinal);api.mkdir();shutil.copytree(pristine/'api',api/'api')
            before = hashes(api)
            run_cli(python,root,api,out/(label+'-'+ordinal+'-dry.log'),dry=True)
            require(hashes(api)==before and hashes(root)==before_source and hashes(pristine)==before_pristine,'dry-run mutated inputs')
            run_cli(python,root,api,out/(label+'-'+ordinal+'.log'))
            state = hashes(api)
            run_cli(python,root,api,out/(label+'-'+ordinal+'-enhanced-dry.log'),dry=True)
            require(hashes(api)==state,'already-enhanced dry-run mutated output')
            run_cli(python,root,api,out/(label+'-'+ordinal+'-idempotent.log'))
            require(hashes(api)==state,'already-enhanced not byte-idempotent')
            site = out/(label+'-publication-'+ordinal);shutil.copytree(pristine,site)
            shutil.copytree(api/'api',site/'api',dirs_exist_ok=True)
            audit_site(site,authority,baseline if label=='baseline' else expected)
            write(out/(label+'-'+ordinal+'-hashes.json'),hashes(site));sites.append(site)
        require(hashes(sites[0])==hashes(sites[1]),'fresh generation not deterministic')
        states[label] = hashes(sites[0])
        reports[label] = json.loads((out/(label+'-first.log')).read_text().splitlines()[0])
        off = out/(label+'-off-api');off.mkdir();shutil.copytree(pristine/'api',off/'api')
        run_cli(python,root,off,out/(label+'-off.log'),off=True)
        write(out/(label+'-off-hashes.json'),hashes(off))
        off_publication = out/(label+'-off-publication');shutil.copytree(pristine,off_publication)
        shutil.copytree(off/'api',off_publication/'api',dirs_exist_ok=True)
        write(out/(label+'-off-publication-hashes.json'),hashes(off_publication))
    require(hashes(out/'baseline-off-api')==hashes(out/'candidate-off-api'),'types-off bytes differ')
    require(hashes(out/'baseline-off-publication')==hashes(out/'candidate-off-publication'),'types-off complete publication differs')
    changed = sorted(p for p in states['baseline'] if states['baseline'][p]!=states['candidate'][p])
    pages = sorted({'api/'+r['containing_page'] for r in census})
    require(changed==sorted(pages+['api/presentation.json']),'unexpected complete-file delta')
    require(len(states['candidate'])==42 and sum(n.endswith('.html') for n in states['candidate'])==37,'publication inventory')
    # Reconstruct complete candidate page bytes from baseline + exact independent
    # new spans. Dot punctuation spans are absorbed into each complete anchor.
    before = out/'baseline-publication-first'; after = out/'candidate-publication-first'
    punctuation = []
    for name in pages:
        def insert(m):
            additions = [r for r in census if r['containing_page']==Path(name).name and r['containing_anchor']==m[2]]
            raw = m[3]
            remaining = Counter(r['spelling'] for r in additions)
            for row in additions:
                spelling = html.escape(row['spelling'],quote=False)
                lexical = spelling.replace('.', '<span class="ada-operator">.</span>')
                anchor = ('<a class="type-reference" href="'+row['destination_page']+'#'+row['destination_anchor']+
                          '" data-type="'+row['destination_identity']+'">'+spelling+'</a>')
                require(raw.count(lexical)==remaining[row['spelling']],'punctuation occurrence count differs')
                raw = raw.replace(lexical,anchor,1)
                remaining[row['spelling']] -= 1
                punctuation.append({'page':name,'spelling':row['spelling'],'before':lexical,'after':anchor})
            return m[1]+raw+m[4]
        require(SECTION.sub(insert,(before/name).read_text()).encode()==(after/name).read_bytes(),'complete expected page differs')
    # Independent manifest reconstruction, including unchanged pristine/source maps.
    manifest = json.loads((before/'api/presentation.json').read_text())
    manifest['counts']['linked_types'] += 9;manifest['counts']['linked_local_types'] += 9
    for page in pages:manifest['output_sha256'][page] = states['candidate'][page]
    encoded = (json.dumps(manifest,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode()
    require(encoded==(after/'api/presentation.json').read_bytes(),'complete expected manifest differs')
    # All literal/highlight tokens and pristine entity bytes restore exactly in
    # affected declarations, separately from full enhanced-byte reconstruction.
    for name in pages:
        raw_sections = {m[2]:m[3] for m in SECTION.finditer((pristine/name).read_text())}
        for m in SECTION.finditer((after/name).read_text()):
            restored = check_snippet(m[3],authority.sections[Path(name).name,m[2]]['native'],expected[Path(name).name,m[2]])
            require(restored==raw_sections[m[2]],'exact pristine entity restoration')
    require(hashes(root)==before_source and hashes(pristine)==before_pristine,'consumer/pristine changed')
    write(out/'punctuation-accounting.json',punctuation)
    tampering = mutations(out,after,authority,expected,census)
    write(out/'tamper-results.json',tampering)
    # Count the complete publication, not the API-only staging tree. The
    # unchanged original validator parser reads links without accepting this
    # candidate under MEL's deliberately deferred production contract.
    from validate_docs import Page
    references = {label:sum(len(Page(p.read_text()).links) for p in
                            (out/(label+'-publication-first')).rglob('*.html'))
                  for label in ('baseline','candidate')}
    require(references=={'baseline':2966,'candidate':2975},'complete reference count')
    write(out/'qualification.json',{'base':BASE,'consumer_revision':REVISION,'reports':reports,
          'complete_reference_counts':references,
          'changed_files':changed,'unchanged_complete_files':42-len(changed),'new_occurrences':9,
          'baseline_occurrences':1419,'candidate_occurrences':1428,'external_occurrences':0,
          'source_sha256':before_source,'pristine_sha256':before_pristine,
          'baseline_sha256':states['baseline'],'candidate_sha256':states['candidate'],
          'independent_occurrences':True,'complete_expected_page_and_manifest_reconstruction':True,
          'exact_pristine_restoration':True,'types_off_complete_equality':True,
          'two_fresh_baseline_and_candidate_runs':True,'byte_idempotent':True,'dry_run_immutable':True})
    print(json.dumps({'status':'PASS','new':9,'changed_files':changed},indent=2))


def retained(args):
    """Retained full real profiles, not synthetic/reduced CI fixtures.

    The immutable acquisition hashes bind complete public source/pristine API.
    Later authored/generic/external configuration is retained byte-for-byte from
    the already reviewed metadata campaign. No expected zero delta is assumed:
    independently enumerate short-prefix lexical candidates first, and require
    explicit classification if this pinned census ever contains one.
    """
    repo = Path(__file__).resolve().parents[1]
    name = args.profile; root = args.source_root.resolve(); pristine = args.pristine.resolve()
    out = args.workspace.resolve()
    require(not out.exists() and not any(out.is_relative_to(p) or p.is_relative_to(out)
                                        for p in (root,pristine)), 'fresh external retained workspace required')
    out.mkdir(parents=True)
    evidence = json.loads((repo/f'docs/evidence/gnatdoc002/{name}-input.json').read_text())
    before_source,before_pristine = hashes(root),hashes(pristine)
    for path,digest in evidence['pristine_sha256'].items():
        require(before_pristine[path]==digest,'retained pristine acquisition hash changed')
    # A separate independent tokenizer masks comments/literals by excluding their
    # complete tokens. It never invokes inventory.mask_ada or type_positions.
    lexer = re.compile(r'--[^\n]*|"(?:""|[^"\n])*"|\'[^\n]\'|[A-Za-z][A-Za-z0-9_]*|\S')
    census = []; sources = {}
    for path in evidence['public_sources']:
        require(sha((root/path).read_bytes())==evidence['source_sha256'][path],'retained complete source changed')
        staged = root/'qualification-public'/path
        require(staged.read_bytes()==(root/path).read_bytes(),'retained staged source mismatch')
        text = staged.read_text(); sources[path] = sha(staged.read_bytes())
        tokens = [(m[0].lower(),m.start(),m.end()) for m in lexer.finditer(text)
                  if not m[0].startswith(('--','"',"'"))]
        words = [t[0] for t in tokens]
        header = words.index('package'); cursor = header+1; owner = words[cursor]; cursor += 1
        while words[cursor]=='.':owner += '.'+words[cursor+1];cursor += 2
        short = owner.split('.')[-1]
        for i in range(cursor,len(tokens)-2):
            if words[i]==short and words[i+1]=='.' and re.fullmatch('[a-z][a-z0-9_]*',words[i+2]) and (i==0 or words[i-1]!='.'):
                census.append({'source':path,'owner':owner,'line':text.count('\n',0,tokens[i][1])+1,
                               'spelling':text[tokens[i][1]:tokens[i+2][2]],'span':[tokens[i][1],tokens[i+2][2]]})
    write(out/'independent-source-census.json',census)
    require(not census,'retained relative candidates need independent classification; do not assume zero')
    states = {}; reports = {}
    for label,python in (('baseline',args.baseline_python),('candidate',args.candidate_python)):
        for ordinal in ('first','second'):
            site = out/(label+'-'+ordinal);shutil.copytree(pristine,site)
            # Reuse identical source/config with a separate invocation; nothing
            # in the input root or any historical publication is written.
            command = [str(python),'-m','ada_gnatdoc_enhancer','enhance','--source-root',str(root),
                       '--config','qualification.toml','--site',str(site)]
            write(out/(label+'-'+ordinal+'-command.json'),command)
            with (out/(label+'-'+ordinal+'.log')).open('x') as stream:
                subprocess.run(command,check=True,stdout=stream,stderr=subprocess.STDOUT,cwd=out,
                               env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'})
            state = hashes(site);write(out/(label+'-'+ordinal+'-hashes.json'),state)
            if ordinal=='first':states[label]=state
            else:require(states[label]==state,'retained determinism')
        reports[label] = json.loads((out/(label+'-first.log')).read_text())
    require(states['baseline']==states['candidate'],'unclassified retained publication delta')
    require(hashes(root)==before_source and hashes(pristine)==before_pristine,'retained input mutation')
    write(out/'qualification.json',{'profile':name,'revision':evidence['revision'],'reports':reports,
          'complete_source_sha256':sources,'pristine_sha256':before_pristine,
          'baseline_sha256':states['baseline'],'candidate_sha256':states['candidate'],
          'changed_occurrences':[],'source_relative_candidates':census,'complete_publication_equal':True})
    print(name,'PASS: independently empty current-package candidate census; complete publication byte equality')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-root','pristine','workspace','baseline-python','candidate-python'):
        parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--profile',choices=('core','imgproc','geometry'))
    args = parser.parse_args()
    retained(args) if args.profile else run(args)