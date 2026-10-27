"""Fresh, non-editable archive qualification for each supported Python."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import zipfile

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace', type=Path, required=True)
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
E = args.workspace.resolve()
S = args.source.resolve()
E.mkdir(parents=True, exist_ok=False)
ENV = dict(os.environ)
ENV.pop('PYTHONPATH', None)


def run(args, log, cwd=E, env=ENV):
    with (E/log).open('w') as output:
        subprocess.run(list(map(str, args)), cwd=cwd, env=env, stdout=output,
                       stderr=subprocess.STDOUT, check=True)
    path = E/log
    if path.suffix == '.json':
        # pip may append an upgrade notice even with --format=json. Preserve
        # that notice separately without turning JSON evidence into mixed text.
        text = path.read_text()
        value, end = json.JSONDecoder().raw_decode(text)
        if text[end:].strip():
            path.with_suffix('.notice.txt').write_text(text[end:].strip()+'\n')
        path.write_text(json.dumps(value, indent=2)+'\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def qualify(version):
    base = E/('python-'+version)
    base.mkdir()
    source = base/'source-env'
    run(['python'+version, '-m', 'venv', source], version+'-venv.log')
    py = source/'bin/python'
    run([py, '-m', 'pip', 'install', 'build', 'twine', 'setuptools>=77',
         'markdown-it-py==3.0.0', 'mdurl==0.1.2'], version+'-tools.log')
    run([py, '-m', 'pip', 'list', '--format=json'], version+'-toolchain.json')
    # Independent clean build trees prevent shared backend products.
    import shutil
    build_source = base/'build-source'
    shutil.copytree(S, build_source, ignore=shutil.ignore_patterns('__pycache__', '*.egg-info', '.git', 'build', 'dist', '.venv'))
    run([py, '-m', 'pip', 'install', '-e', S], version+'-source-install.log')
    artifacts = base/'artifacts'
    run([py, '-m', 'build', '--wheel', '--sdist', '--outdir', artifacts],
        version+'-build.log', cwd=build_source)
    wheel = next(artifacts.glob('*.whl'))
    sdist = next(artifacts.glob('*.tar.gz'))
    extracted = base/'extracted'
    extracted.mkdir()
    with tarfile.open(sdist) as archive:
        # Audit before extracting; no links or nonregular members are accepted.
        for member in archive.getmembers():
            assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            assert member.isdir() or member.isfile()
        archive.extractall(extracted)
    extracted = extracted/'ada_gnatdoc_enhancer-0.1.1'
    run([py, '-m', 'build', '--wheel', '--outdir', base/'rebuilt'],
        version+'-rebuild.log', cwd=extracted)
    rebuilt = next((base/'rebuilt').glob('*.whl'))
    run([py, '-m', 'twine', 'check', '--strict', wheel, sdist, rebuilt], version+'-twine.log')
    run([py, S/'scripts/check_distributions.py', '--source', S, '--wheel', wheel,
         '--sdist', sdist, '--rebuilt', rebuilt], version+'-content-audit.json')
    if version == '3.11':
        (E/'python-3.11-ready').touch()
    report = {'version': version, 'node': subprocess.check_output(['node', '--version'], text=True).strip(),
              'environments': {}}
    canonical = E/'python-3.11/artifacts/ada_gnatdoc_enhancer-0.1.1-py3-none-any.whl'
    # All three Python wheel campaigns install the one canonical candidate.
    import time
    deadline = time.monotonic()+600
    while not (E/'python-3.11-ready').exists():
        assert time.monotonic() < deadline, 'canonical build did not pass audit'
        time.sleep(1)
    for kind, archive, tests in [('source', None, S), ('wheel', canonical, S),
                                  ('sdist', rebuilt, extracted)]:
        prefix = version+'-'+kind
        venv = source if kind == 'source' else base/(kind+'-env')
        python = venv/'bin/python'
        if archive:
            run(['python'+version, '-m', 'venv', venv], prefix+'-venv.log')
            run([python, '-m', 'pip', 'install', '--no-deps', archive], prefix+'-install.log')
            run([python, '-m', 'pip', 'install', 'markdown-it-py==3.0.0', 'mdurl==0.1.2'],
                prefix+'-guides.log')
            run([python, tests/'scripts/test_installed.py', '--fixtures', tests/'tests/fixtures'],
                prefix+'-smoke.json')
        program = '''import unittest,json,sys
from pathlib import Path
from importlib.metadata import version
import ada_gnatdoc_enhancer as package
tests=Path(sys.argv[1]); report=Path(sys.argv[2]); sys.path.insert(0,str(tests))
suite=unittest.defaultTestLoader.discover(str(tests))
def flatten(s):
 for t in s:
  if isinstance(t,unittest.TestSuite): yield from flatten(t)
  else: yield t.id()
ids=list(flatten(suite)); assert len(ids)==len(set(ids))==609
result=unittest.TextTestRunner(verbosity=2).run(suite)
data=dict(tests=result.testsRun,distinct=len(set(ids)),test_ids=ids,skips=len(result.skipped),failures=len(result.failures),errors=len(result.errors),module=package.__file__,python=sys.version,version=version('ada-gnatdoc-enhancer'))
report.write_text(json.dumps(data,indent=2))
assert data['version']==package.__version__=='0.1.1'
assert result.wasSuccessful() and not result.skipped and result.testsRun==609
'''
        run([python, '-c', program, tests/'tests', E/(prefix+'-result.json')], prefix+'-tests.log')
        run([venv/'bin/gnatdoc-enhancer', 'conformance', '--fixtures', tests/'tests/fixtures'],
            prefix+'-conformance.json')
        run([python, '-m', 'pip', 'check'], prefix+'-pip-check.log')
        run([python, '-m', 'compileall', '-q', S/'src'], prefix+'-compileall.log')
        program = '''import json,hashlib,ada_gnatdoc_enhancer as p
from pathlib import Path
root=Path(p.__file__).parent
print(json.dumps({str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file() and f.suffix in ('.py','.css','.js')},sort_keys=True,indent=2))'''
        run([python, '-c', program], prefix+'-installed-content.json')
        report['environments'][kind] = json.loads((E/(prefix+'-result.json')).read_text())
        if archive:
            assert 'site-packages' in report['environments'][kind]['module']
        report['environments'][kind]['archive_sha256'] = sha(archive.read_bytes()) if archive else None
        run([python, '-m', 'pip', 'list', '--format=json'], prefix+'-packages.json')
    inventory = {}
    for label, file in [('wheel', wheel), ('sdist', sdist), ('rebuilt', rebuilt)]:
        if file.suffix == '.whl':
            with zipfile.ZipFile(file) as z:
                members = {n: sha(z.read(n)) for n in z.namelist() if not n.endswith('/')}
        else:
            with tarfile.open(file) as t:
                members = {m.name: sha(t.extractfile(m).read()) for m in t if m.isfile()}
        inventory[label] = {'path': str(file), 'sha256': sha(file.read_bytes()),
                            'bytes': file.stat().st_size, 'files': len(members), 'members': members}
    (E/(version+'-archive-inventory.json')).write_text(json.dumps(inventory, indent=2)+'\n')
    (E/(version+'-summary.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(version, 'all source/wheel/rebuilt qualification gates passed', flush=True)
    return report


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(qualify, ('3.11', '3.12', '3.13')))
    (E/'distribution-matrix.json').write_text(json.dumps(results, indent=2)+'\n')