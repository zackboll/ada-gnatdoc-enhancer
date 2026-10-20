"""Sequential complete real-site browser campaigns, with durable per-run exits."""
import json
import os
from pathlib import Path
import subprocess
import time

E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work');W2=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
env=dict(os.environ,TMPDIR=str(E/'tmp'),DOC_EVIDENCE=str(E/'legacy-equivalent-screens'))
jobs=[]
for label in ['core-current','core-050']:
    while not (E/(label+'-browser-oracle.json')).exists():time.sleep(2)
    for script,mode,flags in [
        ('symbol_canonicalization','symbols',['--oracle',str(E/(label+'-browser-oracle.json'))]),
        ('symbol_bookmarks','symbols',['--ledger',str(W/(label+'-symbol-ledger.json'))]),
        ('core_symbols_equivalent','symbols',[]),
        ('core_navigation_equivalent','instance',[]),
        ('symbol_bookmarks','instance',['--ledger',str(W/(label+'-symbol-ledger.json'))]),
        ('instance_references','instance',['--instance-ledger',str(W2/(label+'-occurrences.json'))]),
        ('instance_canonicalization','instance',['--instance-ledger',str(W2/(label+'-occurrences.json'))]),
    ]:
        jobs.append((label,script,mode,flags))
for label,script,mode,flags in jobs:
    name=label+'-'+mode+'-'+script
    if (E/(name+'.exit')).exists() and (E/(name+'.exit')).read_text().strip()=='0':
        continue
    command=['python3',str(E/'run_browser.py'),str(R/'tests'/(script+'.cjs')),
             str(E/(label+'-'+mode+'-first')),str(E/(name+'.json')),*flags]
    (E/(name+'.command.json')).write_text(json.dumps(command)+'\n')
    with (E/(name+'.log')).open('w') as log:
        result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    (E/(name+'.exit')).write_text(str(result.returncode)+'\n')
    print(name,result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
(E/'browser-campaign.exit').write_text('0\n')