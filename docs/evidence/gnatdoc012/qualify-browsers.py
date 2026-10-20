import concurrent.futures
import functools
import http.server
import json
import os
from pathlib import Path
import subprocess
import threading
import time

B = Path('/tmp/gnatdoc012-candidate')
S = B/'source'
while not (B/'real-core-results.json').exists():
    if (B/'real.exit').exists():raise RuntimeError((B/'real.log').read_text())
    time.sleep(3)
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(B))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()


def campaign(name):
    results = {}
    for suite in ('symbol_bookmarks', 'instance_references', 'instance_canonicalization'):
        label = name+'-'+suite
        environment = dict(os.environ,
            PLAYWRIGHT_MODULE='/tmp/doc-browser/node_modules/playwright',
            CHROME='/home/zboll/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
            DOC_URL=f'http://127.0.0.1:{server.server_port}/{name}-first/api/index.html',
            SYMBOL_LEDGER='/home/zboll/git/ada-gnatdoc-enhancer-011r1-work/'+name+'-symbol-ledger.json',
            INSTANCE_LEDGER=str(B/(name+'-occurrences.json')),
            BROWSER_REPORT=str(B/(label+'.json')))
        with (B/(label+'.log')).open('w') as log:
            result = subprocess.run(['node', str(S/'tests'/(suite+'.cjs'))], env=environment,
                                    cwd='/tmp', stdout=log, stderr=subprocess.STDOUT)
        (B/(label+'.exit')).write_text(str(result.returncode)+'\n')
        results[suite] = result.returncode
    return name, results


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = dict(pool.map(campaign, ('core-current', 'core-050')))
server.shutdown()
(B/'browser-summary.json').write_text(json.dumps(results, indent=2)+'\n')
assert all(code == 0 for cases in results.values() for code in cases.values()), results