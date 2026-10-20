"""Reconstruct six historical publications against immutable R2 authorization."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

E = Path(__file__).resolve().parent
S = E/'final-source'
W = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
approved = json.loads((S/'docs/evidence/gnatdoc011r2/default-and-symbol-only-parity.json').read_text())
report = {}
for entry in json.loads((W/'default-inputs.json').read_text()):
    label = entry['label']
    pristine = E/('historical-profile-'+label)
    (pristine/'api').mkdir(parents=True)
    publication = Path(entry['publication'])
    manifest = json.loads((publication/'api/presentation.json').read_text())
    for name, text in manifest['original_api_html'].items():
        (pristine/name).write_text(text)
    (pristine/'api/gnatdoc.css').write_bytes((publication/'api/gnatdoc.css').read_bytes())
    outputs = {}
    for kind, source in [('R2', E/'source-R2'), ('R3', E/'source-R3'), ('release', S)]:
        program = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from compare_default_symbol_outputs import output
print(json.dumps(output(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))))'''
        env = dict(os.environ, PYTHONPATH=str(source/'src'))
        outputs[kind] = json.loads(subprocess.check_output([sys.executable, '-c', program,
            str(S/'scripts'), entry['root'], entry['config'], str(pristine)], text=True, env=env, cwd=E))
    assert outputs['R2'] == approved[label]['sha256'], label
    assert outputs['R2'].keys() == outputs['R3'].keys() == outputs['release'].keys()
    r2_delta = sorted(k for k in outputs['R2'] if outputs['R2'][k] != outputs['R3'][k])
    assert r2_delta == (['api/gnatdoc-navigation.js','api/presentation.json'] if label == 'core-symbols' else []), label
    release_delta = sorted(k for k in outputs['R3'] if outputs['R3'][k] != outputs['release'][k])
    assert release_delta == ['api/presentation.json'], label
    # Independently reconstruct the expected release manifest with only the
    # version presentation value changed, retaining the R3 implementation.
    program = '''import json,sys
from pathlib import Path
import ada_gnatdoc_enhancer.pipeline as p
p.__version__='0.1.0'
sys.path.insert(0,sys.argv[1])
from compare_default_symbol_outputs import output
print(json.dumps(output(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]))))'''
    expected = json.loads(subprocess.check_output([sys.executable, '-c', program, str(S/'scripts'),
        entry['root'], entry['config'], str(pristine)], text=True,
        env=dict(os.environ, PYTHONPATH=str(E/'source-R3/src')), cwd=E))
    assert expected == outputs['release'], label
    report[label] = dict(files=len(expected), R2_reconstructs_reviewed_authority=True,
                         R2_to_R3_changed=r2_delta, R3_to_release_changed=release_delta,
                         independently_reconstructed_version_only=True, campaigns=outputs,
                         configuration_sha256=hashlib.sha256((Path(entry['root'])/entry['config']).read_bytes()).hexdigest())
    print(label,'passed',flush=True)
(E/'six-profile-publication-comparisons.json').write_text(json.dumps(report,indent=2)+'\n')