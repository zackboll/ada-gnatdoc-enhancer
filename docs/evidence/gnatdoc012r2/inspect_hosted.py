"""Inspect exact submitted-head push/PR jobs and their retained archive evidence."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

E = Path(__file__).resolve().parent
R = Path('/home/zboll/git/ada-gnatdoc-enhancer')
head = subprocess.check_output(['git', '-C', str(R), 'rev-parse', 'HEAD'], text=True).strip()
H = E/'hosted'; H.mkdir(exist_ok=True)


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, cwd=R)


while True:
    runs = json.loads(gh('run', 'list', '--commit', head, '--json',
                         'databaseId,headSha,event,status,conclusion,url', '--limit', '20'))
    (H/'runs.json').write_text(json.dumps(runs,indent=2)+'\n')
    expected = {r['event']: r for r in runs if r['event'] in ('push', 'pull_request')}
    if len(expected) == 2 and all(r['status'] == 'completed' for r in expected.values()): break
    print('Waiting exact final-head push/PR workflows',runs,flush=True)
    time.sleep(25)
results = {}
for event, run in expected.items():
    assert run['headSha'] == head and run['conclusion'] == 'success', run
    run_id = str(run['databaseId'])
    jobs = json.loads(gh('api', f'repos/zackboll/ada-gnatdoc-enhancer/actions/runs/{run_id}/jobs'))['jobs']
    assert len(jobs) == 6
    assert {j['name'] for j in jobs} == {f'{kind} ({version})' for kind in ('test','wheel') for version in ('3.11','3.12','3.13')}
    (H/(event+'-jobs.json')).write_text(json.dumps(jobs,indent=2)+'\n')
    result = []
    for job in jobs:
        assert job['conclusion'] == 'success', job
        log = gh('run','view',run_id,'--job',str(job['id']),'--log')
        (H/(str(job['id'])+'.log')).write_text(log)
        counts = re.findall(r'Ran (\d+) tests? in',log)
        required = 2 if job['name'].startswith('wheel') else 1
        assert counts.count('564') == required, (job['name'], counts)
        assert 'Record qualification source and test-tool identity' in log
        checkout_lines = [line for line in log.splitlines() if 'Record qualification source and test-tool identity' in line]
        checkout = [line for line in checkout_lines if re.search(r'\b[0-9a-f]{40}\b',line)]
        assert checkout, job['name']
        if event == 'push': assert any(head in line for line in checkout)
        else:
            pr_merge = re.search(r'\b([0-9a-f]{40})\b',checkout[0])[1]
            # GitHub PR checks run the synthetic merge. Record its identity and
            # verify that it contains the exact submitted head, not older PR CI.
            commit = json.loads(gh('api',f'repos/zackboll/ada-gnatdoc-enhancer/git/commits/{pr_merge}'))
            assert head in {p['sha'] for p in commit['parents']}, (head,commit)
            (H/(event+'-merge-commit.json')).write_text(json.dumps(commit,indent=2)+'\n')
        if job['name'].startswith('wheel'):
            assert 'Installed CLI, assets and four-profile conformance outside checkout' in log
            assert 'Qualify tests and fixtures shipped in the source distribution' in log
            assert 'Audit archive metadata, complete test inputs and source/module/asset identities' in log
        result.append(dict(id=job['id'],name=job['name'],conclusion=job['conclusion'],
                           test_counts=counts,checkout_log_lines=checkout,log_sha256=hashlib.sha256(log.encode()).hexdigest(),url=job['html_url']))
    results[event] = dict(run=run,jobs=result)
    artifacts = H/(event+'-artifacts')
    if not artifacts.exists():
        subprocess.run(['gh','run','download',run_id,'--dir',str(artifacts)],cwd=R,check=True)
    for audit in artifacts.rglob('content-audit.json'):
        data = json.loads(audit.read_text())
        assert data['source_wheel_sdist_rebuilt_module_assets_equal']
        assert data['sdist_files'] == 863 and data['wheel_files'] == 41
        assert data['module_asset_sha256'] == json.loads((E/'final/3.13-content-audit.json').read_text())['module_asset_sha256']
        wheel = next(audit.parent.glob('*.whl'))
        with zipfile.ZipFile(wheel) as archive:
            for name, digest in data['module_asset_sha256'].items():
                assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        sums = (audit.parent/'SHA256SUMS').read_text().splitlines()
        for line in sums:
            digest, name = line.split(None,1)
            assert hashlib.sha256((audit.parent/Path(name).name).read_bytes()).hexdigest() == digest
    assert len(list(artifacts.rglob('content-audit.json'))) == 3
(H/'qualification.json').write_text(json.dumps(dict(head=head,events=results,all_six_jobs_each_event=True),indent=2)+'\n')
print('Exact-head push and PR hosted CI passed; all 12 job logs and six distribution artifacts inspected',flush=True)