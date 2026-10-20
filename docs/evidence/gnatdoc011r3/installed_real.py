"""Installed-wheel and rebuilt-sdist regeneration must equal source publications."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
env=dict(os.environ,TMPDIR=str(E/'tmp'));env.pop('PYTHONPATH',None)
def hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
source=hashes(R/'src/ada_gnatdoc_enhancer');report={}
for kind in ['wheel','sdist']:
    package=E/(kind+'-3.11/lib/python3.11/site-packages/ada_gnatdoc_enhancer')
    while not package.exists():time.sleep(2)
    assert hashes(package)==source,(kind,'implementation or packaged asset mismatch')
    report[kind]={'implementation_assets_equal_source':True,
                  'package_fingerprint':hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    for label in ['core-current','core-050']:
        for mode,config in [('symbols','disabled.toml'),('instance','qualification.toml')]:
            dest=E/(kind+'-real-'+label+'-'+mode);shutil.copytree(W/(label+'-pristine'),dest)
            command=[str(E/(kind+'-3.11/bin/gnatdoc-enhancer')),'enhance',
                     '--source-root',str(E/(label+'-authority')),'--config',config,'--site',str(dest)]
            with (E/(kind+'-real-'+label+'-'+mode+'.log')).open('w') as log:
                subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            assert hashes(dest)==hashes(E/(label+'-'+mode+'-first')),(kind,label,mode)
            report[kind][label+'-'+mode]={'files':len(hashes(dest)),'exact_source_publication_equal':True}
    dest=E/(kind+'-real-mel');shutil.copytree(E/'mel-symbols-pristine',dest)
    program='from dataclasses import replace;from pathlib import Path;from ada_gnatdoc_enhancer.config import load;from ada_gnatdoc_enhancer.pipeline import enhance,verify;c=replace(load(Path('+repr(str(E/'mel-authority'))+'),"docs/gnatdoc-enhance.toml"),symbol_bookmarks=True,default_package="AMS.MEL");enhance(c,Path('+repr(str(dest))+'));verify(c,Path('+repr(str(dest))+'))'
    subprocess.run([str(E/(kind+'-3.11/bin/python')),'-c',program],env=env,check=True)
    assert hashes(dest)==hashes(E/'mel-symbols-first')
    report[kind]['mel']={'exact_source_publication_equal':True}
(E/'installed-real-publications.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)