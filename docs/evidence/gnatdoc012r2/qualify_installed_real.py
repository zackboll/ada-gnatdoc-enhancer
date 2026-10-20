"""Regenerate real publications using each installed release archive."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

E = Path(__file__).resolve().parent
W = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
M = Path('/home/zboll/qualification/mel-doc010-20261019')
env = dict(os.environ); env.pop('PYTHONPATH', None)


def qualify(job):
    version, kind = job
    python = E/'final'/('python-'+version)/(kind+'-env')/'bin/python'
    results = {}
    for label in ('core-current', 'core-050', 'mel'):
        modes = ('symbols',) if label == 'mel' else ('symbols', 'instance')
        for mode in modes:
            while True:
                try:
                    comparisons = json.loads((E/'publication-comparisons-progress.json').read_text())
                    if label+'-'+mode in comparisons: break
                except (FileNotFoundError, json.JSONDecodeError): pass
                time.sleep(5)
            root = E/(label+'-authority')
            config = 'docs/symbols.toml' if label == 'mel' else ('disabled.toml' if mode == 'symbols' else 'qualification.toml')
            pristine = E/'mel-api-pristine' if label == 'mel' else W/(label+'-pristine')
            destination = E/('installed-'+version+'-'+kind+'-'+label+'-'+mode)
            shutil.copytree(pristine, destination)
            program = '''import json,sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes
c=load(Path(sys.argv[1]),sys.argv[2]);p=Path(sys.argv[3]);expected=Path(sys.argv[4])
counts=enhance(c,p);verify(c,p);before=hashes(p)
assert before==hashes(expected)
enhance(c,p);verify(c,p);assert before==hashes(p)
print(json.dumps(dict(counts=counts,publication_equal_source=True,idempotence=True)))'''
            command = [str(python), '-c', program, str(root), config, str(destination),
                       str(E/(label+'-'+mode+'-release'))]
            output = subprocess.check_output(command, env=env, cwd=E, text=True)
            results[label+'-'+mode] = json.loads(output)
    (E/('installed-real-'+version+'-'+kind+'.json')).write_text(json.dumps(results,indent=2)+'\n')
    print(version,kind,'real publications identical to qualified source',flush=True)
    return dict(python=version, archive=kind, publications=results)


with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results = list(pool.map(qualify, [(v,k) for v in ('3.11','3.12','3.13') for k in ('wheel','sdist')]))
(E/'installed-real-publications.json').write_text(json.dumps(results,indent=2)+'\n')