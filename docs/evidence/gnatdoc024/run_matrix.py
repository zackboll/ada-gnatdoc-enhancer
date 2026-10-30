import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/tmp/gnatdoc024')
SOURCE = ROOT/'source'
SDIST = ROOT/'sdist-source/ada_gnatdoc_enhancer-0.1.3'
ENV = dict(os.environ)
ENV.pop('PYTHONPATH', None)

def run(version, mode):
    label = mode+'-'+version
    started = time.time()
    env = ROOT/'envs'/label
    python = env/'bin/python'
    log = ROOT/'logs'/(label+'.log')
    work = SOURCE if mode == 'source' else SDIST if mode == 'sdist' else ROOT
    tests = work/'tests' if mode != 'wheel' else SOURCE/'tests'
    with log.open('w') as out:
        def command(words, cwd=work):
            print('$ '+' '.join(map(str, words)), file=out, flush=True)
            subprocess.run(list(map(str, words)), cwd=cwd, env=ENV, stdout=out,
                           stderr=subprocess.STDOUT, check=True)
        try:
            command(['python'+version, '-m', 'venv', env], ROOT)
            artifact = SOURCE if mode == 'source' else next((ROOT/('dist' if mode == 'wheel' else 'rebuilt')).glob('*.whl'))
            command([python, '-m', 'pip', 'install', *(['-e'] if mode == 'source' else []), str(artifact)+'[guides]'])
            (ROOT/(label+'.installed')).touch()
            command([python, '-m', 'unittest', 'discover', '-s', tests, '-v'])
            command([python, '-m', 'ada_gnatdoc_enhancer', '--version'], ROOT)
            command([env/'bin/gnatdoc-enhancer', '--version'], ROOT)
            command([python, '-m', 'compileall', '-q', SOURCE/'src'])
            if mode == 'source':
                command([env/'bin/gnatdoc-enhancer', 'conformance', '--fixtures', SOURCE/'tests/fixtures'], ROOT)
            else:
                command([python, (SDIST if mode == 'sdist' else SOURCE)/'scripts/test_installed.py', '--fixtures', tests/'fixtures'], ROOT)
            result = dict(environment=label, status='passed', seconds=round(time.time()-started, 2))
        except Exception as error:
            result = dict(environment=label, status='failed', error=str(error), seconds=round(time.time()-started, 2))
    (ROOT/(label+'.json')).write_text(json.dumps(result, indent=2)+'\n')
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
    results = list(pool.map(lambda args: run(*args), [(v, m) for v in ('3.11', '3.12', '3.13') for m in ('source', 'wheel', 'sdist')]))
(ROOT/'matrix.json').write_text(json.dumps(results, indent=2)+'\n')
raise SystemExit(any(r['status'] != 'passed' for r in results))