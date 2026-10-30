"""Fail-closed classification of the two independent release output baselines."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    'release_output_audit', Path(__file__).resolve().parents[1]/'scripts/compare_release_outputs.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ReleaseOutputContracts(unittest.TestCase):
    def publications(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        roots = [Path(temporary.name)/name for name in ('baseline', 'candidate')]
        for root, version in zip(roots, ('0.1.2', '0.1.3')):
            (root/'api').mkdir(parents=True)
            (root/'api/index.html').write_bytes(b'unchanged authentic input stand-in')
            (root/'api/presentation.json').write_text(json.dumps(
                dict(enhancer_version=version, output_sha256={}, native=['unchanged'])))
        return roots

    def test_version_only_is_accepted_for_both_baselines(self):
        for official in (False, True):
            with self.subTest(official=official):
                result = audit.compare(*self.publications(), official=official)
                self.assertEqual(result['changed_files'], ['api/presentation.json'])
                self.assertEqual(result['permitted_manifest_fields'], ['enhancer_version'])

    def test_unclassified_file_and_manifest_differences_are_rejected(self):
        for mutation in ('extra', 'missing', 'html', 'manifest', 'version', 'symlink'):
            with self.subTest(mutation=mutation):
                old, new = self.publications()
                if mutation == 'extra':(new/'extra').write_bytes(b'extra')
                if mutation == 'missing':(new/'api/index.html').unlink()
                if mutation == 'html':(new/'api/index.html').write_bytes(b'changed')
                if mutation in ('manifest', 'version'):
                    path = new/'api/presentation.json'; data = json.loads(path.read_text())
                    data['native' if mutation == 'manifest' else 'enhancer_version'] = 'changed'
                    path.write_text(json.dumps(data))
                if mutation == 'symlink':(new/'alias').symlink_to(new/'api/index.html')
                with self.assertRaises(ValueError):audit.compare(old, new)

    def test_official_default_requires_unchanged_router_bytes(self):
        old, new = self.publications()
        for root in (old, new):(root/'api/gnatdoc-navigation.js').write_bytes(b'approved baseline')
        audit.compare(old, new, official=True, default_router=True)
        (new/'api/gnatdoc-navigation.js').write_bytes(b'unexpected new router')
        with self.assertRaisesRegex(ValueError, 'unclassified publication difference'):
            audit.compare(old, new, official=True, default_router=True)

    def labelled_publications(self):
        roots = self.publications()
        for root, label in zip(roots, (audit.OLD_LABEL, audit.NEW_LABEL)):
            (root/'api/index.html').write_bytes(b'<html>'+label+b'</html>')
            manifest = root/'api/presentation.json'; data = json.loads(manifest.read_text())
            data['output_sha256']['api/index.html'] = hashlib.sha256((root/'api/index.html').read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data))
        return roots

    def test_intentional_label_and_affected_hash_are_classified(self):
        result = audit.compare(*self.labelled_publications(), official=True)
        self.assertEqual(result['changed_files'], ['api/index.html', 'api/presentation.json'])
        self.assertEqual(result['permitted_manifest_fields'], ['enhancer_version', 'output_sha256.api/index.html'])
        self.assertEqual(set(result['changed_output_hashes']), {'api/index.html'})

    def test_label_mutations_and_rehashed_unexpected_output_are_rejected(self):
        for mutation in ('missing', 'unexpected', 'hash', 'duplicate'):
            with self.subTest(mutation=mutation):
                old, new = self.labelled_publications()
                index = new/'api/index.html'
                if mutation == 'missing':index.write_bytes((old/'api/index.html').read_bytes())
                if mutation == 'unexpected':index.write_bytes(index.read_bytes()+b'extra')
                if mutation == 'duplicate':(old/'api/index.html').write_bytes(audit.OLD_LABEL*2)
                manifest = new/'api/presentation.json'; data = json.loads(manifest.read_text())
                data['output_sha256']['api/index.html'] = 'forged' if mutation == 'hash' else hashlib.sha256(index.read_bytes()).hexdigest()
                manifest.write_text(json.dumps(data))
                with self.assertRaises(ValueError):audit.compare(old, new)

    def test_search_assets_are_never_classified_as_default_output(self):
        for name in ('gnatdoc-search-index.json', 'gnatdoc-search.css'):
            old, new = self.publications()
            for root in (old, new):(root/'api'/name).write_bytes(b'search asset')
            with self.assertRaisesRegex(ValueError, 'search opt-in'):
                audit.compare(old, new)