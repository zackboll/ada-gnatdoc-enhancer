"""Replay consumer, live browser and official-release parity after final-head build.

Run from outside the checkout after the canonical build passes its content audit.
All original attempts/logs remain in the workspace; no historical files are edited.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description=__doc__)
for key in ('source', 'workspace'):
    parser.add_argument('--'+key, type=Path, required=True)
args = parser.parse_args()
S = args.source.resolve(); W = args.workspace.resolve()
E = S/'docs/evidence/gnatdoc015'
D = W/'distributions-final'
environment = dict(os.environ); environment.pop('PYTHONPATH', None)
deadline = time.monotonic()+600
while not (D/'python-3.11-ready').exists():
    assert time.monotonic() < deadline, 'canonical final build did not pass audit'
    time.sleep(1)


def run(command, name, env=environment):
    with (W/name).open('w') as log:
        subprocess.run(list(map(str, command)), check=True, cwd=W, env=env,
                       stdout=log, stderr=subprocess.STDOUT)


def campaign(kind):
    venv = W/('final-consumer-'+kind+'-env')
    run(['python3.13', '-m', 'venv', venv], 'final-'+kind+'-venv.log')
    python = venv/'bin/python'
    archive = D/'python-3.11'/('artifacts' if kind == 'wheel' else 'rebuilt')
    wheel = archive/'ada_gnatdoc_enhancer-0.1.1-py3-none-any.whl'
    run([python, '-m', 'pip', 'install', '--no-deps', wheel], 'final-'+kind+'-install.log')
    run([python, '-m', 'pip', 'install', 'markdown-it-py==3.0.0', 'mdurl==0.1.2'],
        'final-'+kind+'-guides.log')
    dest = W/('final-consumer-'+kind)
    run([python, E/'qualify_consumer.py', '--consumer', W/'consumer-snapshot',
         '--retained', '/home/zboll/git/opencv/imgproc-gnatdoc009-r1-work',
         '--native', '/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native',
         '--legacy-site', '/home/zboll/git/opencv/imgproc-gnatdoc009/_site',
         '--official-python', W/'official-env/bin/python',
         '--baseline-src', W/'merged-main/src', '--output', dest],
        'final-consumer-'+kind+'.log')
    browser_env = dict(environment,
                       PLAYWRIGHT_MODULE='/home/zboll/.npm/_npx/e41f203b7505f1fb/node_modules/playwright',
                       GNATDOC014_WORKSPACE=str(dest),
                       GNATDOC014_REPORT=str(W/('final-browser-'+kind+'.json')))
    run(['node', S/'tests/external_type_target_browser.cjs'],
        'final-browser-'+kind+'.log', browser_env)
    browser = json.loads((W/('final-browser-'+kind+'.json')).read_text())
    assert not browser['failures'] and sum(x.get('topLevel', False)
                                          for x in browser['assertions']) == 224
    return dict(archive=kind, browser_top_traces=224,
                consumer=json.loads((dest/'qualification.json').read_text()))


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(campaign, ('wheel', 'sdist')))
run([W/'final-consumer-wheel-env/bin/python', E/'qualify_default_outputs.py',
     '--source', S, '--retained', '/home/zboll/qualification/gnatdoc012r2',
     '--official-python', W/'official-env/bin/python',
     '--candidate-python', W/'final-consumer-wheel-env/bin/python',
     '--output', W/'final-default-parity'], 'final-default-parity.log')
(W/'final-consumer-summary.json').write_text(json.dumps(results, indent=2)+'\n')
print('Both final-head installed consumer/browser campaigns and all 12 default profiles pass')