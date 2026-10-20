import json
import os
from pathlib import Path
import subprocess
E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work');W2=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
env=dict(os.environ,TMPDIR=str(E/'tmp'),PYTHONPATH=str(R/'src')+':'+str(R/'scripts'))
for label in ['core-current','core-050']:
    command=[str(E/'py-3.13/bin/python'),str(R/'scripts/qualify_instance_references.py'),
        '--core',str(W/label),'--pristine',str(W/(label+'-pristine')),
        '--legacy',str(W/label/'_site'),'--candidate',str(E/(label+'-instance-first')),
        '--baseline',str(E/(label+'-symbols-first')),'--output',str(E/(label+'-occurrences.json'))]
    subprocess.run(command,env=env,check=True)
    actual=json.loads((E/(label+'-occurrences.json')).read_text());old=json.loads((W2/(label+'-occurrences.json')).read_text())
    assert actual==old,label
    print(label,'complete source/native incoming occurrence ledger equal R2',flush=True)
(E/'occurrence-preservation.exit').write_text('0\n')