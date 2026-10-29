"""Verify completed exact-head reports without repeating successful test suites."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--tree', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Never overwrite an existing reconciliation'
    actual_tree = subprocess.check_output(
        ['git', '-C', str(args.repository), 'rev-parse', args.head + '^{tree}'],
        text=True).strip()
    assert actual_tree == args.tree
    archived = subprocess.check_output(
        ['git', '-C', str(args.repository), 'archive', args.head])
    with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
        source_hashes = {m.name: sha(archive.extractfile(m).read())
                         for m in archive if m.isfile()}
    for name, digest in source_hashes.items():
        assert sha((args.source / name).read_bytes()) == digest, name
    matrix = json.loads((args.matrix / 'distribution-matrix.json').read_text())
    baseline = json.loads((args.repository / 'docs/evidence/gnatdoc020/test-retention.json').read_text())
    baseline_ids = set(baseline['baseline_ids'])
    assert len(baseline_ids) == 653
    expected_assets = {p.relative_to(args.source / 'src/ada_gnatdoc_enhancer').as_posix():
                       sha(p.read_bytes())
                       for p in (args.source / 'src/ada_gnatdoc_enhancer').rglob('*')
                       if p.is_file() and p.suffix in ('.py', '.css', '.js')}
    canonical = args.matrix / 'python-3.11/artifacts/ada_gnatdoc_enhancer-0.1.2-py3-none-any.whl'
    assert sorted(row['version'] for row in matrix) == ['3.11', '3.12', '3.13']
    results = {}
    input_files = {}

    def retain(path):
        input_files[str(path)] = dict(sha256=sha(path.read_bytes()), bytes=path.stat().st_size)

    all_ids = None
    for row in matrix:
        version = row['version']
        base = args.matrix / ('python-' + version)
        wheel = next((base / 'artifacts').glob('*.whl'))
        sdist = next((base / 'artifacts').glob('*.tar.gz'))
        rebuilt = next((base / 'rebuilt').glob('*.whl'))
        for path in (wheel, sdist, rebuilt):
            retain(path)
        with zipfile.ZipFile(wheel) as archive:
            original_members = {n: archive.read(n) for n in archive.namelist()}
        with zipfile.ZipFile(rebuilt) as archive:
            assert original_members == {n: archive.read(n) for n in archive.namelist()}
        py = base / 'source-env/bin/python'
        audit = subprocess.check_output(
            [str(py), str(args.source / 'scripts/check_distributions.py'),
             '--source', str(args.source), '--wheel', str(wheel),
             '--sdist', str(sdist), '--rebuilt', str(rebuilt)])
        audit_path = args.output.parent / (version + '-reconciled-content-audit.json')
        assert not audit_path.exists()
        audit_path.write_bytes(audit)
        retain(audit_path)
        provenance = subprocess.check_output(
            [str(py), str(args.source / 'scripts/record_candidate_provenance.py'),
             '--repository', str(args.repository), '--source', str(args.source),
             '--expected-source-commit', args.head, '--expected-source-tree', args.tree,
             '--wheel', str(wheel), '--sdist', str(sdist), '--rebuilt', str(rebuilt)])
        provenance_path = args.output.parent / (version + '-reconciled-provenance.json')
        assert not provenance_path.exists()
        provenance_path.write_bytes(provenance)
        retain(provenance_path)
        assert json.loads(provenance)['publication_authorized'] is False
        assert set(row['environments']) == {'source', 'wheel', 'sdist'}
        for kind, report in row['environments'].items():
            prefix = version + '-' + kind
            result_path = args.matrix / (prefix + '-result.json')
            observed = json.loads(result_path.read_text())
            for key, value in observed.items():
                assert report[key] == value, (prefix, key)
            ids = set(report['test_ids'])
            assert len(ids) == report['tests'] == report['distinct'] == 661
            assert baseline_ids <= ids
            assert report['failures'] == report['errors'] == report['skips'] == 0
            assert report['version'] == '0.1.2'
            assert report['python'].startswith(version + '.')
            if all_ids is None:
                all_ids = ids
            assert all_ids == ids
            if kind == 'source':
                assert Path(report['module']).is_relative_to(args.source)
                assert report['archive_sha256'] is None
            else:
                assert 'site-packages' in Path(report['module']).parts
                assert Path(report['module']).is_relative_to(base / (kind + '-env'))
                assert report['archive_sha256'] == sha(
                    (canonical if kind == 'wheel' else rebuilt).read_bytes())
                smoke = args.matrix / (prefix + '-smoke.json')
                json.loads(smoke.read_text())
                retain(smoke)
            content_path = args.matrix / (prefix + '-installed-content.json')
            assert json.loads(content_path.read_text()) == expected_assets
            conformance_path = args.matrix / (prefix + '-conformance.json')
            profiles = json.loads(conformance_path.read_text())['profiles']
            assert set(profiles) == {'core', 'geometry', 'imgproc', 'mel'}
            assert all(p['deterministic'] and p['idempotent'] for p in profiles.values())
            log_path = args.matrix / (prefix + '-tests.log')
            log = log_path.read_text()
            assert 'Ran 661 tests in ' in log and log.rstrip().endswith('OK')
            pip_check = args.matrix / (prefix + '-pip-check.log')
            assert pip_check.read_text().strip() == 'No broken requirements found.'
            for path in (result_path, content_path, conformance_path, log_path, pip_check):
                retain(path)
            results[prefix] = dict(tests=661, failures=0, errors=0, skips=0,
                                   retained_baseline_ids=653, module=report['module'],
                                   archive_sha256=report['archive_sha256'])
    retain(args.matrix / 'distribution-matrix.json')
    result = dict(status='pass', head=args.head, tree=args.tree,
                  source_files=len(source_hashes), environments=results,
                  tests=5949, baseline_executions=5877,
                  complete_rebuilt_members_equal=True,
                  installed_modules_assets_equal=True,
                  strict_archive_record_metadata_provenance='pass',
                  conformance_scope='four synthetic profiles, not full consumer sites',
                  evidence_files=input_files, publication_authorized=False)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('PASS: exact-head nine-environment reports and archive identities reconciled')


if __name__ == '__main__':
    main()