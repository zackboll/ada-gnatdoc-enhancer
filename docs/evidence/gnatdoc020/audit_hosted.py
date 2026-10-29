"""Independent exact-head download, source/member, checksum and install audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

p=argparse.ArgumentParser();p.add_argument('--head',required=True);p.add_argument('--tree',required=True)
p.add_argument('--run',required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
args=p.parse_args();O=args.output;O.mkdir(exist_ok=False)
repo='zackboll/ada-gnatdoc-enhancer'
def gh(*a):return subprocess.check_output(['gh',*map(str,a)])
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,d):(O/n).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
run=json.loads(gh('run','view',args.run,'--repo',repo,'--json','status,conclusion,headSha,url,jobs'))
write('ci.json',run);assert run['headSha']==args.head and run['status']=='completed' and run['conclusion']=='success'
assert len(run['jobs'])==6 and all(j['conclusion']=='success' for j in run['jobs'])
artifacts=json.loads(gh('api',f'repos/{repo}/actions/runs/{args.run}/artifacts'));write('artifacts.json',artifacts)
env=dict(os.environ);env.pop('PYTHONPATH',None)
build=Path('/home/zboll/qualifications/gnatdoc020/distributions/python-3.11/source-env/bin/python')
summary={}
for version in ('3.11','3.12','3.13'):
    matches=[a for a in artifacts['artifacts'] if a['name']=='release-candidate-python-'+version];assert len(matches)==1
    a=matches[0];assert a['workflow_run']['head_sha']==args.head and not a['expired']
    data=gh('api',f'repos/{repo}/actions/artifacts/{a["id"]}/zip');assert 'sha256:'+sha(data)==a['digest']
    zpath=O/(version+'.zip');zpath.write_bytes(data);dest=O/version;dest.mkdir()
    with zipfile.ZipFile(zpath) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        for n in z.namelist():assert not Path(n).is_absolute() and '..' not in Path(n).parts
        z.extractall(dest)
    wheel=next(dest.rglob('*.whl'));sdist=next(dest.rglob('*.tar.gz'));prov=next(dest.rglob('candidate-provenance.json'));checks=next(dest.rglob('SHA256SUMS'))
    for line in checks.read_text().splitlines():
        expected,name=line.split(maxsplit=1);assert sha((dest/Path(name).name).read_bytes())==expected
    provenance=json.loads(prov.read_text());assert provenance['expected_source_commit']==args.head and provenance['expected_source_tree']==args.tree
    assert provenance['publication_authorized'] is False and provenance['release_version']=='0.1.2'
    for n,claim in provenance['source_files'].items():assert sha((args.source/n).read_bytes())==claim['sha256']
    assert sha(wheel.read_bytes())==provenance['archives']['wheel']['sha256']
    assert sha(sdist.read_bytes())==provenance['archives']['sdist']['sha256']
    rebuilt=dest/'rebuilt';rebuilt.mkdir()
    with (dest/'rebuild.log').open('w') as log:subprocess.run([build,'-m','pip','wheel','--no-deps','--wheel-dir',rebuilt,sdist],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
    second=next(rebuilt.glob('*.whl'))
    audit=json.loads(subprocess.check_output([build,args.source/'scripts/check_distributions.py','--source',args.source,'--wheel',wheel,'--sdist',sdist,'--rebuilt',second],env=env))
    write(version+'-content-audit.json',audit)
    venv=dest/'installed';subprocess.run(['python'+version,'-m','venv',venv],check=True,env=env)
    with (dest/'install.log').open('w') as log:subprocess.run([venv/'bin/python','-m','pip','install','--no-deps',wheel],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
    program='''import json,hashlib,ada_gnatdoc_enhancer as p
from pathlib import Path
from importlib.metadata import version
assert 'site-packages' in p.__file__
print(json.dumps(dict(module=p.__file__,version=version('ada-gnatdoc-enhancer'),assets={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(p.__file__).parent.joinpath('assets').glob('*.js')})))'''
    installed=json.loads(subprocess.check_output([venv/'bin/python','-c',program],cwd=O,env=env));assert installed['version']=='0.1.2'
    for n,digest in installed['assets'].items():assert digest==sha((args.source/'src/ada_gnatdoc_enhancer/assets'/n).read_bytes())
    summary[version]=dict(artifact_id=a['id'],zip_sha256=sha(data),wheel_sha256=sha(wheel.read_bytes()),sdist_sha256=sha(sdist.read_bytes()),rebuilt_sha256=sha(second.read_bytes()),installed=installed)
write('summary.json',dict(status='pass',head=args.head,tree=args.tree,run=args.run,candidates=summary))
print('Exact final-head hosted CI and all immutable candidate downloads independently audited')