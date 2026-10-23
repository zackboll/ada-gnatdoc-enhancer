"""Compare complete candidate/base publications from retained native inputs.

No native generation or consumer modification. Reconstruct raw API input from
the historical publication and require historical/current/base output equality.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--baseline-src', type=Path, required=True)
parser.add_argument('--retained', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
S = args.source.resolve(); R = args.retained.resolve(); E = args.output.resolve()
E.mkdir(parents=True, exist_ok=False)
sys.path[:0] = [str(S/'src'), str(S/'scripts')]
from compare_default_symbol_outputs import output
from ada_gnatdoc_enhancer.qualification import hashes

entries = []
for label in ('core-current', 'core-050'):
    entries.extend([
        (label+'-default', R/(label+'-default-authority'), 'default.toml'),
        (label+'-symbols', R/(label+'-authority'), 'disabled.toml'),
        (label+'-instance', R/(label+'-authority'), 'qualification.toml')])
entries.extend([('mel-default', R/'mel-authority', 'docs/gnatdoc-enhance.toml'),
                ('mel-symbols', R/'mel-authority', 'docs/symbols.toml')])
report = {}
program = '''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from compare_default_symbol_outputs import output
print(json.dumps(output(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))))'''
# The helper intentionally refuses incoming-reference profiles. Use its exact
# reconstruction algorithm without that historical comparison-only exclusion.
program_instance = '''import sys,json
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import MANIFEST,_presentation,expected_output
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest,sorted_json
c=load(Path(sys.argv[2]),sys.argv[3]);p=Path(sys.argv[4])
_,v,counts=expected_output(c,p)
raw={f.relative_to(p).as_posix():f.read_text() for f in (p/'api').glob('*.html')}
v[MANIFEST]=sorted_json(_presentation(c,p,raw,v,counts)).encode()
r=hashes(p);r.update({n:digest(b) for n,b in v.items()});print(json.dumps(r))'''
for label, root, config in entries:
    before = hashes(root)
    historical = R/(label+'-release')
    pristine = E/label; (pristine/'api').mkdir(parents=True)
    manifest = json.loads((historical/'api/presentation.json').read_text())
    for name, text in manifest['original_api_html'].items():(pristine/name).write_text(text)
    (pristine/'api/gnatdoc.css').write_bytes((historical/'api/gnatdoc.css').read_bytes())
    results = {}
    for kind, source in [('base', args.baseline_src.resolve()), ('candidate', S/'src')]:
        results[kind] = json.loads(subprocess.check_output([sys.executable, '-c',
            program_instance if label.endswith('-instance') else program,
            str(S/'scripts'), str(root), config, str(pristine)],
            cwd=E, env=dict(os.environ, PYTHONPATH=str(source)), text=True))
    assert results['base'] == results['candidate'], label
    historical_hashes = hashes(historical)
    assert results['candidate'] == historical_hashes, label+' retained release differs'
    assert before == hashes(root), label+' read-only authority changed'
    report[label] = dict(byte_identical=True, files=len(historical_hashes),
                         source_and_native_freshly_built=False, sha256=historical_hashes)
    (E/'parity.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(label, len(historical_hashes), 'exact historical/base/candidate equality', flush=True)
for label in ('core', 'imgproc', 'geometry', 'mel'):
    root = S/'tests/fixtures'/label; pristine = root/'_site'
    candidate = output(root, 'project.toml', pristine)
    baseline = json.loads(subprocess.check_output([sys.executable, '-c', program,
        str(S/'scripts'), str(root), 'project.toml', str(pristine)], cwd=E,
        env=dict(os.environ, PYTHONPATH=str(args.baseline_src.resolve())), text=True))
    assert candidate == baseline, label
    report['synthetic-'+label] = dict(byte_identical=True, files=len(candidate), sha256=candidate)
(E/'parity.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')