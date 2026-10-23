"""Fresh actual publications using independently installed official/candidate wheels.

Only reads retained native/source authorities. This is not fresh Ada compilation.
Only enhancer_version may change in the canonical presentation manifest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
for key in ('source', 'retained', 'official-python', 'candidate-python', 'output'):
    parser.add_argument('--'+key, type=Path, required=True)
args = parser.parse_args()
S = args.source.resolve(); R = args.retained.resolve(); E = args.output.resolve()
E.mkdir(parents=True, exist_ok=False)
environment = dict(os.environ); environment.pop('PYTHONPATH', None)
program = '''import sys,json
from pathlib import Path
import ada_gnatdoc_enhancer as package
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes
c=load(Path(sys.argv[1]),sys.argv[2]);p=Path(sys.argv[3])
enhance(c,p);verify(c,p)
print(json.dumps(dict(module=package.__file__,version=package.__version__,sha256=hashes(p))))
'''


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}


entries = []
for label in ('core-current', 'core-050'):
    entries.extend([(label+'-default', R/(label+'-default-authority'), 'default.toml'),
                    (label+'-symbols', R/(label+'-authority'), 'disabled.toml'),
                    (label+'-instance', R/(label+'-authority'), 'qualification.toml')])
entries.extend([('mel-default', R/'mel-authority', 'docs/gnatdoc-enhance.toml'),
                ('mel-symbols', R/'mel-authority', 'docs/symbols.toml')])
entries.extend(('synthetic-'+label, S/'tests/fixtures'/label, 'project.toml')
               for label in ('core', 'imgproc', 'geometry', 'mel'))
report = {}
for label, root, config in entries:
    before = hashes(root)
    pristine = E/label/'native'; (pristine/'api').mkdir(parents=True)
    historical = None if label.startswith('synthetic-') else R/(label+'-release')
    if historical:
        manifest = json.loads((historical/'api/presentation.json').read_text())
        for name, text in manifest['original_api_html'].items():
            (pristine/name).write_text(text)
        (pristine/'api/gnatdoc.css').write_bytes((historical/'api/gnatdoc.css').read_bytes())
    else:
        shutil.rmtree(pristine)
        shutil.copytree(root/'_site', pristine)
    results = {}
    for kind, python in [('official', args.official_python), ('candidate', args.candidate_python)]:
        site = E/label/kind; shutil.copytree(pristine, site)
        results[kind] = json.loads(subprocess.check_output(
            [python.resolve(), '-c', program, root, config, site], cwd=E,
            env=environment, text=True))
        assert 'site-packages' in results[kind]['module'], 'not an installed module'
    a = results['official']['sha256']; b = results['candidate']['sha256']
    assert a.keys() == b.keys(), label+' membership drift'
    assert [n for n in a if a[n] != b[n]] == ['api/presentation.json'], label+' output drift'
    old = json.loads((E/label/'official/api/presentation.json').read_text())
    new = json.loads((E/label/'candidate/api/presentation.json').read_text())
    assert old['enhancer_version'] == '0.1.0' and new['enhancer_version'] == '0.1.1'
    old['enhancer_version'] = '0.1.1'
    assert old == new, label+' manifest changed beyond version'
    official_bytes = (E/label/'official/api/presentation.json').read_bytes()
    assert official_bytes.replace(b'"enhancer_version": "0.1.0"',
                                  b'"enhancer_version": "0.1.1"', 1) == (
                                      E/label/'candidate/api/presentation.json').read_bytes()
    if historical:
        assert a == hashes(historical), label+' official release differs from retained publication'
    assert before == hashes(root), label+' read-only source authority changed'
    report[label] = dict(only_manifest_version_changed=True, files=len(a),
                         historical_publication_reconstructed=bool(historical), results=results)
    (E/'parity.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(label, len(a), 'only authorized version-bound manifest transition', flush=True)