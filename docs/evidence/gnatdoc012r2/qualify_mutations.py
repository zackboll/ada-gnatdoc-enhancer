"""Repeat retained symbol/instance mutation campaigns on dedicated copies."""
import os
from pathlib import Path
import shutil
import subprocess
import time
import json
import concurrent.futures

E = Path(__file__).resolve().parent
S = E/'final-source'
W = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
env = dict(os.environ, TMPDIR=str(E/'tmp'), PYTHONPATH=str(S/'scripts'))
def qualify(label):
    while True:
        try:
            comparisons = json.loads((E/'publication-comparisons-progress.json').read_text())
            if label+'-instance' in comparisons: break
        except (FileNotFoundError, json.JSONDecodeError): pass
        time.sleep(5)
    root = E/(label+'-mutation-authority')
    shutil.copytree(E/(label+'-authority'), root)
    shutil.copy2(root/'disabled.toml', root/'qualification.toml')
    site = E/(label+'-mutation-symbols')
    shutil.copytree(E/(label+'-symbols-release'), site)
    installed = E/'final/python-3.11/wheel-env'
    while not (installed/'bin/gnatdoc-enhancer').exists(): time.sleep(5)
    # Installed-code tampering uses a dedicated environment, never a matrix input.
    dedicated = E/(label+'-mutation-installed')
    shutil.copytree(installed, dedicated, symlinks=True)
    jobs = [('symbol', [str(S/'scripts/tamper_symbol_bookmarks.py'), '--core', str(W/label),
             '--authority', str(root), '--pristine', str(W/(label+'-pristine')),
             '--candidate', str(site), '--output', str(E/(label+'-symbol-mutations.json'))]),
            ('instance', [str(S/'scripts/tamper_instance_references.py'), '--core', str(W/label),
             '--authority', str(E/(label+'-authority')), '--pristine', str(W/(label+'-pristine')),
             '--candidate', str(E/(label+'-instance-release')), '--workspace', str(E/(label+'-instance-mutation-work')),
             '--installed', str(dedicated), '--output', str(E/(label+'-instance-mutations.json'))])]
    for name, args in jobs:
        with (E/(label+'-'+name+'-mutations.log')).open('w') as output:
            result = subprocess.run([str(installed/'bin/python'), *args],
                                    env=env, stdout=output, stderr=subprocess.STDOUT)
        (E/(label+'-'+name+'-mutations.exit')).write_text(str(result.returncode)+'\n')
        print(label, name, result.returncode, flush=True)
        if result.returncode: raise RuntimeError(label+' '+name+' mutation failed')


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(qualify, ('core-current', 'core-050')))
(E/'mutations.exit').write_text('0\n')