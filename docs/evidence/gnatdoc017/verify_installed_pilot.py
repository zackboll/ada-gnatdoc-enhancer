"""Reconstruct real Core custom output with each final installed distribution."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess

E = Path('/home/zboll/gnatdoc-017-evidence')
env = dict(os.environ); env.pop('PYTHONPATH',None)
def run(entry):
    version, kind = entry
    cli = E/'distributions-final'/('python-'+version)/(kind+'-env')/'bin/gnatdoc-enhancer'
    outputs = {}
    for site, config in [('candidate','custom.toml'),('incoming-custom','custom-incoming.toml')]:
        command = [cli,'verify','--source-root',E/'authority','--config',config,'--site',E/site]
        outputs[site] = json.loads(subprocess.check_output(command,cwd=E,env=env,text=True))
    return version+'-'+kind, outputs
entries = [(v,k) for v in ('3.11','3.12','3.13') for k in ('source','wheel','sdist')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result = dict(pool.map(run,entries))
(E/'installed-core-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('Nine final installed CLI environments verified both authentic Core custom profiles')