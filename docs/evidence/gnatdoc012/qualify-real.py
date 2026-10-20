"""Local orchestration over independently hash-pinned retained acquisitions."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

B = Path('/tmp/gnatdoc012-candidate')
S = B/'source'
R1 = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
R2 = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
sys.path.insert(0, str(S/'scripts'))
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from compare_default_symbol_outputs import output


def save(name, value):
    (B/name).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def run(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True, cwd='/tmp')


source_proof = json.loads((R1/'acquisition-source-proof.json').read_text())
native_proof = json.loads((R2/'acquisition-preservation.json').read_text())
history = {}
for directory in ('gnatdoc011', 'gnatdoc011r1', 'gnatdoc011r2'):
    history.update({str(p.relative_to(S)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (S/'docs/evidence'/directory).rglob('*') if p.is_file()})
save('historical-evidence-sha256.json', history)
identities = {}
for name in ('core-current', 'core-050'):
    core = R1/name
    pristine = R1/(name+'-pristine')
    revision = subprocess.check_output(['git', '-C', str(core), 'rev-parse', 'HEAD'], text=True).strip()
    assert revision == source_proof[name]['revision'] == native_proof[name]['source_revision']
    assert {n: hashlib.sha256((core/n).read_bytes()).hexdigest()
            for n in source_proof[name]['source_sha256']} == source_proof[name]['source_sha256']
    assert hashes(pristine) == native_proof[name]['pristine_sha256']
    assert not subprocess.check_output(['git', '-C', str(core), 'diff', 'HEAD', '--', 'src', 'scripts'])
    identities[name] = {'revision': revision, 'source_files_verified': len(source_proof[name]['source_sha256']),
                        'pristine_files_verified': len(hashes(pristine)), 'fresh_Ada_GNATdoc_acquisition': False}
save('retained-input-verification.json', identities)

results = {}
for name in ('core-current', 'core-050'):
    core = R1/name; pristine = R1/(name+'-pristine')
    authority = B/(name+'-authority')
    shutil.copytree(R1/(name+'-authority'), authority)
    before = hashes(authority)
    config = load(authority, 'qualification.toml')
    site = B/(name+'-first'); second = B/(name+'-second')
    shutil.copytree(pristine, site); shutil.copytree(pristine, second)
    counts = enhance(config, site); enhance(config, second)
    original = hashes(site)
    assert original == hashes(second)
    enhance(config, site); verify(config, site)
    assert original == hashes(site) and before == hashes(authority)
    old = hashes(R2/(name+'-candidate'))
    changes = sorted(n for n in old if old[n] != original[n])
    assert changes == ['api/presentation.json'], changes
    previous = (R2/(name+'-candidate')/'api/presentation.json').read_bytes()
    assert (site/'api/presentation.json').read_bytes() == previous.replace(b'"enhancer_version": "0.1.0.dev0"', b'"enhancer_version": "0.1.0"')
    # Fresh processes isolate the two independently pinned consumer oracle imports.
    program = ('import json; from pathlib import Path; from qualify_symbol_bookmarks import audit; '
               'r=audit(Path('+repr(str(core))+'),Path('+repr(str(pristine))+'),Path('+repr(str(site))+'),'
               'Path('+repr(str(core/'_site'))+'),instance_references=True); '
               'Path('+repr(str(B/(name+'-native-audit.json')))+').write_text(json.dumps(r,sort_keys=True,indent=2))')
    run('-c', program)
    run(S/'scripts/qualify_instance_references.py', '--core', core, '--pristine', pristine,
        '--legacy', core/'_site', '--candidate', site, '--baseline', R1/(name+'-disabled'),
        '--output', B/(name+'-occurrences.json'))
    ledger = json.loads((B/(name+'-occurrences.json')).read_text())
    assert ledger == json.loads((R1/(name+'-occurrences-final.json')).read_text())
    assert ledger['incoming_occurrences'] == 242 and not ledger['missing']
    audit = json.loads((B/(name+'-native-audit.json')).read_text())
    assert audit['public_symbols'] == 215 and audit['public_packages'] == 195
    results[name] = {'revision': identities[name]['revision'], 'counts': counts, 'two_copy_determinism': True,
                     'byte_idempotence': True, 'authority_unchanged': True, 'native_symbols': 215,
                     'incoming_occurrences': 242, 'occurrence_ledger_equal_reviewed_R1': True,
                     'only_delta_from_R2': changes, 'manifest_single_version_substitution': True,
                     'native_signature_destination_preservation': True,
                     'publication_sha256': original}
save('real-core-results.json', results)

parity = {}
for entry in json.loads((R1/'default-inputs.json').read_text()):
    label = entry['label']; root = Path(entry['root']); publication = Path(entry['publication'])
    pristine = B/('parity-'+label); (pristine/'api').mkdir(parents=True)
    manifest = json.loads((publication/'api/presentation.json').read_text())
    for n, text in manifest['original_api_html'].items():(pristine/n).write_text(text)
    shutil.copyfile(publication/'api/gnatdoc.css', pristine/'api/gnatdoc.css')
    actual = output(root, entry['config'], pristine)
    program = ('import json,sys; from pathlib import Path; '
               'sys.path.insert(0,'+repr(str(S/'scripts'))+'); '
               'import ada_gnatdoc_enhancer.pipeline as pipeline; '
               'pipeline.__version__="0.1.0"; '
               'from compare_default_symbol_outputs import output; '
               'print(json.dumps(output(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]))))')
    environment = dict(os.environ, PYTHONPATH='/tmp/gnatdoc012/src')
    expected = json.loads(subprocess.check_output([sys.executable, '-c', program, str(root),
                          entry['config'], str(pristine)], text=True, env=environment))
    assert actual == expected, label
    parity[label] = {'files': len(actual), 'all_bytes_equal_except_manifest_version': True,
                     'baseline_manifest_version_normalized_only': True, 'sha256': actual}
save('default-symbol-only-parity.json', parity)
print('Real Core and six retained default/symbol-only publication profiles passed', flush=True)