"""Repeat unchanged Chromium contracts against release-version publications."""
import json
import os
from pathlib import Path
import subprocess
import time
import concurrent.futures

E = Path(__file__).resolve().parent
S = E/'final-source'
W = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
W2 = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
env = dict(os.environ, TMPDIR=str(E/'tmp'), DOC_EVIDENCE=str(E/'legacy-equivalent-screens'))
jobs = []
for label in ('core-current', 'core-050'):
    for script, mode, flags in [
        ('symbol_canonicalization', 'symbols', ['--oracle', str(E/(label+'-browser-oracle.json'))]),
        ('symbol_bookmarks', 'symbols', ['--ledger', str(W/(label+'-symbol-ledger.json'))]),
        ('core_symbols_equivalent', 'symbols', []),
        ('core_navigation_equivalent', 'instance', []),
        ('symbol_bookmarks', 'instance', ['--ledger', str(W/(label+'-symbol-ledger.json'))]),
        ('instance_references', 'instance', ['--instance-ledger', str(W2/(label+'-occurrences.json'))]),
        ('instance_canonicalization', 'instance', ['--instance-ledger', str(W2/(label+'-occurrences.json'))]),
    ]:
        jobs.append((label, script, mode, flags))
jobs.append(('mel', 'symbol_canonicalization', 'symbols', ['--oracle', str(E/'mel-browser-oracle.json')]))
def qualify(job):
    label, script, mode, flags = job
    name = label+'-'+mode+'-'+script
    # Publication comparisons and source/native audits authorize browser input.
    while True:
        try:
            comparisons = json.loads((E/'publication-comparisons-progress.json').read_text())
            if label+'-'+mode in comparisons: break
        except (FileNotFoundError, json.JSONDecodeError): pass
        time.sleep(5)
    if (E/(name+'.exit')).exists() and (E/(name+'.exit')).read_text().strip() == '0':
        return
    site = E/(label+'-'+mode+'-release'+('-complete' if label == 'mel' else ''))
    command = ['python3', str(E/'run_browser.py'), str(S/'tests'/(script+'.cjs')),
               str(site), str(E/(name+'.json')), *flags]
    (E/(name+'.command.json')).write_text(json.dumps(command)+'\n')
    with (E/(name+'.log')).open('w') as output:
        result = subprocess.run(command, env=env, stdout=output, stderr=subprocess.STDOUT)
    (E/(name+'.exit')).write_text(str(result.returncode)+'\n')
    print(name, result.returncode, flush=True)
    if result.returncode: raise RuntimeError(name+' failed')


def site_campaign(label):
    for job in jobs:
        if job[0] == label: qualify(job)


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(site_campaign, ('core-current', 'core-050', 'mel')))
(E/'browser-campaign.exit').write_text('0\n')