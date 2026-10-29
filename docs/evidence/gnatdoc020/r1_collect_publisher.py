"""Read-only publisher API capture; never retain credentials or signed URLs."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request


OUTPUT = Path('/home/zboll/qualifications/gnatdoc020/r1/http')
REPO = 'repos/zackboll/opencv_core_ada/'
REQUESTS = {
    'pages-metadata': REPO + 'actions/artifacts/12703258126',
    'pages-download': REPO + 'actions/artifacts/12703258126/zip',
    'run': REPO + 'actions/runs/40433988181',
    'jobs': REPO + 'actions/runs/40433988181/jobs',
    'artifacts': REPO + 'actions/runs/40433988181/artifacts',
    'deployment': REPO + 'deployments/7348179998',
    'deployment-statuses': REPO + 'deployments/7348179998/statuses',
    'deployments': REPO + 'deployments?environment=github-pages&per_page=100',
    'retention': REPO + 'actions/permissions/artifact-and-log-retention',
    'workflow': REPO + 'contents/.github/workflows/documentation.yml'
    '?ref=33a2a4f3b83606a5c779b8a93abeb6c91fa49a21',
    'review-metadata': REPO + 'actions/artifacts/12702919800',
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def capture(item, token):
    label, endpoint = item
    url = 'https://api.github.com/' + endpoint
    headers = {'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'GNATDOC-020R1-read-only-evidence',
               'Cache-Control': 'no-cache'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(url, headers=headers, method='GET')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        response = urllib.request.build_opener(NoRedirect).open(request, timeout=60)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        # Retain server response headers, but not cookies or signed redirect queries.
        response_headers = {}
        for name, value in response.headers.items():
            if name.lower() in ('set-cookie', 'authorization', 'proxy-authorization'):
                value = '[REDACTED]'
            if name.lower() == 'location':
                parsed = urllib.parse.urlsplit(value)
                value = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc,
                                                parsed.path, '', ''))
            response_headers[name] = value
        metadata = dict(method='GET', url=url, started_utc=started,
                        completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        authentication='gh credential in memory' if token else 'anonymous',
                        request_headers={k: v for k, v in headers.items() if k != 'Authorization'},
                        status=response.status, response_headers=response_headers,
                        body_sha256=hashlib.sha256(body).hexdigest(), body_bytes=len(body))
    (OUTPUT / (label + '.body')).write_bytes(body)
    (OUTPUT / (label + '.json')).write_text(json.dumps(metadata, indent=2) + '\n')
    return label, metadata['status']


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if any(OUTPUT.iterdir()):
        raise SystemExit('Refusing to overwrite an existing capture')
    credential = subprocess.check_output(['gh', 'auth', 'token'], text=True).strip()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        print(list(pool.map(lambda item: capture(item, credential), REQUESTS.items())))
    for name in ('pages-metadata', 'pages-download'):
        print(capture((name + '-anonymous', REQUESTS[name]), None))