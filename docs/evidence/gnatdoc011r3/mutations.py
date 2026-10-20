"""Dedicated mutation copies; never mutate active browser/publication inputs."""
import os
from pathlib import Path
import shutil
import subprocess
import time

E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
env=dict(os.environ,TMPDIR=str(E/'tmp'),PYTHONPATH=str(R/'src'))
while not (E/'publication-comparisons.json').exists():time.sleep(2)
for label in ['core-current','core-050']:
    root=E/(label+'-mutation-authority')
    if not root.exists():shutil.copytree(E/(label+'-authority'),root)
    # The original symbol mutator expects qualification.toml to select symbols.
    shutil.copy2(root/'disabled.toml',root/'qualification.toml')
    site=E/(label+'-mutation-symbols')
    if not site.exists():shutil.copytree(E/(label+'-symbols-first'),site)
    jobs=[('symbol',[
        str(R/'scripts/tamper_symbol_bookmarks.py'),'--core',str(W/label),
        '--authority',str(root),'--pristine',str(W/(label+'-pristine')),
        '--candidate',str(site),'--output',str(E/(label+'-symbol-mutations.json'))]),
        ('instance',[
        str(R/'scripts/tamper_instance_references.py'),'--core',str(W/label),
        '--authority',str(E/(label+'-authority')),'--pristine',str(W/(label+'-pristine')),
        '--candidate',str(E/(label+'-instance-first')),'--workspace',str(E/(label+'-instance-mutation-work')),
        '--installed',str(E/'wheel-3.11'),
        '--output',str(E/(label+'-instance-mutations.json'))])]
    for name,args in jobs:
        if (E/(label+'-'+name+'-mutations.json')).exists():continue
        if label=='core-050' and name=='instance' and (E/'core-050-instance-mutation-work').exists():
            while not (E/'core-050-instance-mutations.exit').exists():time.sleep(2)
            assert (E/'core-050-instance-mutations.exit').read_text().strip()=='0'
            continue
        with (E/(label+'-'+name+'-mutations.log')).open('w') as log:
            result=subprocess.run([str(E/'py-3.13/bin/python'),*args],env=env,stdout=log,stderr=subprocess.STDOUT)
        (E/(label+'-'+name+'-mutations.exit')).write_text(str(result.returncode)+'\n')
        print(label,name,result.returncode,flush=True)
        if result.returncode:raise SystemExit(result.returncode)
(E/'mutations.exit').write_text('0\n')