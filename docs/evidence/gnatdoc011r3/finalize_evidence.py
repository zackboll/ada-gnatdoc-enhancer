"""Fail closed on local gates, then stage compact permanent R3 evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
D=R/'docs/evidence/gnatdoc011r3'
required=['browser-campaign','mel-canonicalization-exact-final',
          'core-current-symbols-symbol_canonicalization-exact-final',
          'core-050-symbols-symbol_canonicalization','existing-synthetic-browser',
          'occurrence-preservation','distributions','mutations']
required += ['python-'+v+'-final' for v in ['3.11','3.12','3.13']]
required += [kind+'-'+v for v in ['3.11','3.12','3.13'] for kind in ['wheel','sdist']]
for name in required:
    assert (E/(name+'.exit')).read_text().strip()=='0',name
for label in ['core-current','core-050']:
    for script,mode in [('symbol_bookmarks','symbols'),('core_symbols_equivalent','symbols'),
                        ('core_navigation_equivalent','instance'),('symbol_bookmarks','instance'),
                        ('instance_references','instance'),('instance_canonicalization','instance')]:
        name=label+'-'+mode+'-'+script
        assert (E/(name+'.exit')).read_text().strip()=='0',name
for kind in ['wheel','sdist']:
    for version in ['3.11','3.12','3.13']:
        text=(E/(kind+'-'+version+'-tests.log')).read_text()
        assert 'Ran 558 tests' in text and text.rstrip().endswith('OK')
for n,d in json.loads((E/'historical-evidence-sha256.json').read_text()).items():
    assert hashlib.sha256((R/n).read_bytes()).hexdigest()==d,n
package=json.loads((E/'installed-real-publications.json').read_text())
comparisons=json.loads((E/'publication-comparisons.json').read_text())
browser={}
for name in ['mel-canonicalization-exact-final','core-current-symbols-symbol_canonicalization-exact-final',
             'core-050-symbols-symbol_canonicalization']:
    record=json.loads((E/(name+'.json')).read_text());assert not record['failure'] and not record['errors']
    browser[name]={'traces':len(record['traces']),'requests':len(record['requests']),
                   'browser':record['browser'],'all_eight_contexts_passed':True}
mutations={}
for label in ['core-current','core-050']:
    symbol=json.loads((E/(label+'-symbol-mutations.json')).read_text())
    instance=json.loads((E/(label+'-instance-mutations.json')).read_text())
    mutations[label]={'symbol_cases':len(symbol['mutations']) if 'mutations' in symbol else len(symbol),
                      'instance_cases':len(instance['mutations'])}
summary={'starting_head':'697d4ca91dc81812e501e501c9766d9b3ec88924',
         'branch':'corrective/011r3-symbol-url-canonicalization','local_gates_passed':True,
         'hosted_ci':'not claimed until exact committed HEAD is pushed and checked; external final handoff records outcomes',
         'source_matrix':{v:558 for v in ['3.11','3.12','3.13']},
         'wheel_matrix':{v:558 for v in ['3.11','3.12','3.13']},
         'rebuilt_sdist_matrix':{v:558 for v in ['3.11','3.12','3.13']},
         'original_540_tests_retained':True,'additional_tests':18,
         'symbol_router_sha256':'233cf43211a711d0d64dfba2815bc2d9cc887720faed0ca38f464bc6d29e145f',
         'package_fingerprint':package['wheel']['package_fingerprint'],
         'browser':browser,'mutation_cases':mutations,
         'publications':{k:{x:v[x] for x in ['files','changed','fingerprint']} for k,v in comparisons.items()},
         'default_and_instance_assets_unchanged':True,'two_copy_generation':True,'byte_idempotence':True,
         'core_source_native_symbols_each':215,'core_source_native_occurrences_each':242,
         'core_occurrence_ledgers_equal_R2':True,
         'mel':json.loads((E/'mel-inventory-preservation.json').read_text()),
         'historical_evidence_unchanged':True,'MEL_repository_unchanged':True,
         'release_pr14_unchanged_head':'d8d73eb677952ce83a8188b8c20a7c032580409e',
         'external_evidence':str(E)}
(E/'qualification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
D.mkdir(exist_ok=False)
names=['README-evidence.md','negative-first.json','negative-source-identity.json','new-regression-negative.json',
       'new-regression-negative.log','packaged-writer-negative-first.log',
       'router-comparison.json','corrected-package-fingerprint.json','publication-comparisons.json',
       'mel-inventory-preservation.json','independent-symbol-inventory.json','retained-source-verification.json',
       'reviewed-parity-authority.json','core-disabled-parity.json','installed-real-publications.json',
       'conformance.json','qualification-summary.json','historical-evidence-sha256.json',
       'release-pr14-before.json','release-coordination.json','existing-synthetic-browser.log','retained-test-files.json']
names += ['python-'+v+'-final.log' for v in ['3.11','3.12','3.13']]
names += [kind+'-'+v+'-'+suffix for v in ['3.11','3.12','3.13'] for kind in ['wheel','sdist']
          for suffix in ['tests.log','smoke.json','conformance.json']]
names += [n+'.json' for n in browser]
for label in ['core-current','core-050']:
    names += [label+'-native-symbol-audit.json',label+'-occurrences.json',label+'-symbol-mutations.json',label+'-instance-mutations.json']
    for script,mode in [('symbol_bookmarks','symbols'),('core_symbols_equivalent','symbols'),
                       ('core_navigation_equivalent','instance'),('symbol_bookmarks','instance'),
                       ('instance_references','instance'),('instance_canonicalization','instance')]:
        stem=label+'-'+mode+'-'+script
        names.append(stem+'.log')
        if (E/(stem+'.json')).exists():names.append(stem+'.json')
for name in names:shutil.copy2(E/name,D/name)
for name in ['generate.py','run_browser.py','browser_campaign.py','distributions.sh','installed_real.py',
             'mutations.py','check_parity_authority.py','core_default_parity.py','recheck_sources.py',
             'recheck_occurrences.py','make_mel_oracle.py','release_coordination.py','finalize_evidence.py']:
    shutil.copy2(E/name,D/name)
identities={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*')) if p.is_file()}
(D/'evidence-sha256.json').write_text(json.dumps(identities,indent=2)+'\n')
print(json.dumps(summary,indent=2))