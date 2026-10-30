import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/tmp/gnatdoc024')
SOURCE = ROOT/'source'
PYTHON = ROOT/'envs/wheel-3.13/bin/python'
environment = dict(os.environ); environment.pop('PYTHONPATH', None)

def run(label, words):
    with (ROOT/'logs'/(label+'.log')).open('w') as out:
        subprocess.run([str(w) for w in words], cwd=ROOT, env=environment,
                       stdout=out, stderr=subprocess.STDOUT, check=True)

while not (ROOT/'wheel-3.13.installed').exists(): time.sleep(3)
run('browser-tool-install', [PYTHON, '-m', 'pip', 'install', 'playwright==1.64.0'])
run('search-browser', [PYTHON, SOURCE/'scripts/check_search_browser.py',
                      '--workspace', ROOT/'search-sites', '--output', ROOT/'search-evidence'])
run('legacy-synthetic-browser', [PYTHON, SOURCE/'scripts/test_browser.py'])
while not (ROOT/'compatibility.ok').exists(): time.sleep(3)
for name in ('core', 'geometry', 'imgproc', 'mel'):
    run(name+'-real-browser', [PYTHON, SOURCE/'scripts/check_real_browser.py',
        '--workspace', ROOT/'real-sites'/name, '--output', ROOT/(name+'-real-browser.json')])
(ROOT/'browser.ok').touch()