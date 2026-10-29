"""Explicit preflight audit only; no enhancement-time network behavior."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path('/home/zboll/gnatdoc-018-evidence')
BASE = 'https://zackboll.github.io/opencv_core_ada/'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect rejected: '+newurl)

def check(item):
    name, expected = item
    url = BASE+name
    for attempt in range(3):
        try:
            with urllib.request.build_opener(NoRedirect).open(url, timeout=45) as response:
                assert response.status == 200 and response.url == url
                data = response.read(8_000_001)
                assert len(data) <= 8_000_000
                actual = hashlib.sha256(data).hexdigest()
                assert actual == expected, (name, expected, actual)
                return name, dict(url=url, sha256=actual, bytes=len(data), redirected=False)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1)

def audit(label):
    inventory = json.loads((ROOT/'artifact-identity.json').read_text())['publication_sha256']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        files = dict(pool.map(check, inventory.items()))
    report = dict(status='all-inventoried-publication-bytes-match', files=files,
                  inventory_scope='all 209 members of both immutable review and deployed Pages artifacts',
                  extra_live_paths='not enumerable over HTTP; no claim of exhaustive server path discovery',
                  timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    (Path('/home/zboll/qualifications/gnatdoc020/publisher')/(label+'.json')).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(label, len(files), 'matched', flush=True)

if __name__ == '__main__':
    import sys
    audit(sys.argv[1])
