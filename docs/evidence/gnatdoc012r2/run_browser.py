import argparse
import functools
import http.server
import os
from pathlib import Path
import subprocess
import threading

p=argparse.ArgumentParser()
p.add_argument('script');p.add_argument('site');p.add_argument('report')
p.add_argument('--oracle');p.add_argument('--ledger');p.add_argument('--instance-ledger')
a=p.parse_args()
E=Path('/home/zboll/qualification/gnatdoc012r2')
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=a.site))
t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
env=dict(os.environ,TMPDIR=str(E/'tmp'),PLAYWRIGHT_MODULE='/tmp/doc-browser/node_modules/playwright',
         CHROME='/home/zboll/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome',
         DOC_URL=f'http://127.0.0.1:{server.server_port}/api/index.html',BROWSER_REPORT=a.report)
if a.oracle:env['SYMBOL_ORACLE']=a.oracle
if a.ledger:env['SYMBOL_LEDGER']=a.ledger
if a.instance_ledger:env['INSTANCE_LEDGER']=a.instance_ledger
screens=Path(a.report+'-screens');screens.mkdir(exist_ok=True);env['SCREENSHOT_DIR']=str(screens)
try:result=subprocess.run(['node',a.script],env=env)
finally:server.shutdown();server.server_close();t.join()
raise SystemExit(result.returncode)