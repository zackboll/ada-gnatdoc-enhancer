"""Collect completed qualification without changing qualified source inputs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

E = Path(__file__).resolve().parent
F = E/'final'
R = Path('/home/zboll/git/ada-gnatdoc-enhancer')
D = R/'docs/evidence/gnatdoc012r2'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (E/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


matrix = read(F/'distribution-matrix.json')
assert len(matrix) == 3
for record in matrix:
    assert set(record['environments']) == {'source', 'wheel', 'sdist'}
    for result in record['environments'].values():
        assert result['tests'] == result['distinct'] == 564
        assert result['skips'] == result['failures'] == result['errors'] == 0
        assert result['version'] == '0.1.0'
assert (E/'browser-campaign.exit').read_text().strip() == '0'
assert (E/'mutations.exit').read_text().strip() == '0'
assert len(read(E/'installed-real-publications.json')) == 6
assert len(read(E/'distribution-audit-negative-controls.json')) == 17
assert len(read(E/'six-profile-publication-comparisons.json')) == 6
consumers = read(E/'real-qualification-complete.json')
assert consumers['mel_symbols'] == 238 and consumers['mel_references'] == 3259
counts = read(E/'publication-counts.json')
for label, sections, links in [('core-current', 1282, 2745), ('core-050', 1268, 2701)]:
    c = counts[label+'-instance-release']
    assert c['public_packages'] == 195 and c['declaration_snippets'] == sections
    assert c['linked_local_types'] == links
    assert c['qualified_generic_instances'] == 25 and c['generic_summary_links'] == 102
    ledger = read(E/(label+'-occurrences.json'))
    assert ledger['incoming_occurrences'] == 242 and not ledger['missing']
    for mode in ('symbols', 'instance'):
        native = read(E/(label+'-'+mode+'-native-audit.json'))
        assert native['public_symbols'] == 215 and native['native_sections'] == sections
browser = {}
for p in E.glob('*.command.json'):
    name = p.name.removesuffix('.command.json')
    assert (E/(name+'.exit')).read_text().strip() == '0', name
    report = E/(name+'.json')
    if report.exists():
        data = read(report)
        assert not data.get('failure') and not data.get('errors'), name
        browser[name] = dict(traces=len(data.get('traces', [])), browser=data.get('browser'),
                             requests=len(data.get('requests', [])), exit=0)
    else:
        browser[name] = dict(exit=0, report='assertion log (legacy runner)')
assert len(browser) == 15, len(browser)
for label in ('core-current', 'core-050', 'mel'):
    assert browser[label+'-symbols-symbol_canonicalization']['traces'] == 416
save('browser-summary.json', browser)
mutations = {}
for label in ('core-current', 'core-050'):
    mutations[label] = {}
    for mode, expected in [('symbol', 15), ('instance', 38)]:
        result = read(E/(label+'-'+mode+'-mutations.json'))
        assert len(result['mutations']) == expected
        assert result['byte_idempotent']
        for case in result['mutations'].values():
            assert case['mutation_observed']
            assert case.get('shared_rejected') or case.get('rejected')
            assert case.get('restored_hashes_and_independent_audit') or case.get('restored_complete_hashes_and_independent_audit')
        mutations[label][mode] = expected
save('mutation-summary.json', mutations)
history = read(E/'historical-evidence-sha256.json')
for name, expected in history.items(): assert sha(R/name) == expected, name
installed = {}
expected = read(F/'3.13-content-audit.json')['module_asset_sha256']
expected = {k.removeprefix('ada_gnatdoc_enhancer/'): v for k,v in expected.items()}
for version in ('3.11', '3.12', '3.13'):
    for kind in ('source', 'wheel', 'sdist'):
        name = version+'-'+kind+'-installed-content.json'
        assert read(F/name) == expected
        installed[name] = dict(all_modules_assets_equal_source=True,
            fingerprint=hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':')).encode()).hexdigest())
save('installed-content-identities.json', installed)
head, tree = (E/'final-qualified-source.txt').read_text().splitlines()
assert subprocess.check_output(['git', '-C', str(R), 'rev-parse', 'HEAD'], text=True).strip() == head
subprocess.run(['git', '-C', str(R), 'merge-base', '--is-ancestor',
                '524b7610e21e9a7b87e8e0761580ed59a3b0295c', head], check=True)
save('qualification-summary.json', dict(
    original_PR14_head='d8d73eb677952ce83a8188b8c20a7c032580409e',
    merged_main='524b7610e21e9a7b87e8e0761580ed59a3b0295c',
    merge_commit='76b58917de776564aae3e72c75999e6a0cf309eb',
    qualified_source=head, qualified_tree=tree, version='0.1.0',
    test_population=dict(R2=540, R3_additions=18, release_additions=3, archive_security_additions=3, total=564),
    matrix=matrix, local_gates_passed=True, browser=browser, mutations=mutations,
    historical_records_unchanged=len(history),
    source_qualification_separate_from_evidence=True,
    no_consumer_changes=True, no_tag_release_publish_or_merge=True,
    external_workspace=str(E),
    exact_final_head_CI='Recorded after evidence-only commit/push in external FINAL-HANDOFF.md and PR #14; never substitute earlier CI'))
D.mkdir()
names = [
    'qualified-source.txt', 'final-qualified-source.txt', 'starting-identities.txt', 'SHA256SUMS',
    'source-changed-files.txt', 'source-ancestry.txt', 'production-source-relationship.json',
    'retained-input-verification.json', 'historical-evidence-sha256.json', 'consumer-final-preservation.json',
    'implementation-fingerprints.json', 'navigation-selection-contracts.json',
    'retained-test-files.json', 'R3-test-retention.json', 'final-discovered-test-ids.json',
    'distribution-audit-negative-controls.json', 'archive-symlink-negative-first.json',
    'archive-negatives.log', 'shipped-R3-inputs.json', 'toolchain.json',
    'core-only-install.log', 'core-only-smoke.json', 'core-only-packages.json',
    'publication-comparisons.json', 'publication-counts.json', 'six-profile-publication-comparisons.json',
    'six-profile-campaign.log', 'real-campaign.log', 'real-campaign-initial-harness-failure.log',
    'real-qualification-complete.json', 'harness-notes.json',
    'default-synthetic-browser.log', 'browser-summary.json', 'browser-campaign.log',
    'mutation-summary.json', 'mutation-campaign.log', 'installed-real-publications.json',
    'installed-real-campaign.log', 'installed-content-identities.json', 'qualification-summary.json',
    'qualify_real.py', 'qualify_default_profiles.py', 'qualify_browsers.py', 'qualify_mutations.py',
    'qualify_installed_real.py', 'negative_archives.py', 'run_browser.py', 'finalize_evidence.py', 'inspect_hosted.py',
]
for name in names: shutil.copy2(E/name, D/name)
for label in ('core-current', 'core-050'):
    for suffix in ('symbols-native-audit.json','instance-native-audit.json','occurrences.json',
                   'symbol-mutations.json','instance-mutations.json'):
        shutil.copy2(E/(label+'-'+suffix), D/(label+'-'+suffix))
for path in E.glob('*.command.json'):
    name = path.name.removesuffix('.command.json')
    for suffix in ('.command.json','.exit','.log','.json'):
        file = E/(name+suffix)
        if file.exists(): shutil.copy2(file, D/file.name)
for p in F.iterdir():
    if p.is_file() and p.suffix in ('.json', '.log', '.py'):
        shutil.copy2(p, D/p.name)
(D/'README.md').write_text('''# GNATDOC-012R2 corrective qualification

The existing PR #14 is reconciled by a normal two-parent merge with reviewed
R3 main. No router was edited during reconciliation. Version remains 0.1.0.
The 561 required tests are retained; three additive malformed-wheel tests bring
the total to 564 after an observed wheel-symlink audit failure was repaired.
All nine source/wheel/rebuilt-sdist environments pass without skips or errors.

`qualification-summary.json` binds the qualified source commit/tree. These
evidence-only files were collected later and are excluded from distributions.
Historical GNATDOC-011/R1/R2/R3 and original GNATDOC-012 evidence is unchanged.
The old 543-test, 860-file and archive-hash claims are historical only.

R2, actual merged R3 development, old release and corrected release publications
are independently reconstructed. R3 development to release differs only by the
manifest version field. Old symbol-only output additionally changes the approved
router and dependent manifest; it is not called byte-identical. Native/source
authority is checked independently, never authorized by candidate manifests.

Retained Core and MEL acquisitions were hash-checked, not freshly compiled or
generated with GNATdoc. Consumer repositories are unchanged. The complete
workspace (archives, screenshots, prior/superseded runs and intermediate sites)
is `/home/zboll/qualification/gnatdoc012r2/`.

Exact submitted head, normal-push identity agreement and final-head hosted run/job
IDs and inspected conclusions are recorded after push in that workspace's
`FINAL-HANDOFF.md` and existing PR #14. This avoids self-referential artifacts.
The final evidence manifest binds the permanent record, excluding itself.
No release publication, tag, PR merge or consumer migration is authorized.
''')
manifest = {str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file()}
(D/'evidence-sha256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('Collected',len(manifest),'evidence files; manifest SHA-256',sha(D/'evidence-sha256.json'))