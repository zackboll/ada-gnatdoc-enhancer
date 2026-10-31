"""Current release differential; the historical 012/013 tests stay unchanged."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    'release_013_014', Path(__file__).resolve().parents[1]/'scripts/compare_release_013_014.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class Release013014Contracts(unittest.TestCase):
    def publications(self, search=False):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        roots = [Path(temporary.name)/name for name in ('baseline', 'candidate')]
        for root, version in zip(roots, ('0.1.3', '0.1.4')):
            (root/'api').mkdir(parents=True)
            (root/'api/index.html').write_bytes(b'unchanged native index')
            (root/'api/presentation.json').write_text(json.dumps(
                dict(enhancer_version=version, output_sha256={}, native=['unchanged'])))
            if search:
                (root/'api/gnatdoc-search-index.json').write_bytes(b'approved search records')
                (root/'api/gnatdoc-search.css').write_bytes(b'approved search CSS')
        return roots

    def test_only_version_changes_with_or_without_search(self):
        for search in (False, True):
            result = audit.compare(*self.publications(search))
            self.assertEqual(result['changed_files'], ['api/presentation.json'])
            self.assertEqual(result['permitted_manifest_fields'], ['enhancer_version'])
            self.assertTrue(result['all_other_bytes_equal'])

    def test_unclassified_deltas_are_rejected_even_when_rehashed(self):
        for mutation in ('extra', 'missing', 'html', 'manifest', 'version', 'symlink',
                         'search', 'css', 'router', 'format', 'rehashed'):
            with self.subTest(mutation=mutation):
                old, new = self.publications(search=True)
                manifest = new/'api/presentation.json'
                data = json.loads(manifest.read_text())
                if mutation == 'extra':(new/'extra').write_bytes(b'extra')
                if mutation == 'missing':(new/'api/index.html').unlink()
                if mutation == 'html':(new/'api/index.html').write_bytes(b'changed')
                if mutation == 'manifest':data['native'] = []
                if mutation == 'version':data['enhancer_version'] = '0.1.2'
                if mutation == 'symlink':(new/'alias').symlink_to(new/'api/index.html')
                if mutation == 'search':(new/'api/gnatdoc-search-index.json').write_bytes(b'forged')
                if mutation == 'css':(new/'api/gnatdoc-search.css').write_bytes(b'forged')
                if mutation == 'router':
                    for root in (old, new):(root/'api/gnatdoc-navigation.js').write_bytes(str(root).encode())
                if mutation == 'rehashed':
                    import hashlib
                    (new/'api/index.html').write_bytes(b'forged')
                    data['output_sha256']['api/index.html'] = hashlib.sha256(b'forged').hexdigest()
                manifest.write_text(json.dumps(data, indent=2) if mutation == 'format' else json.dumps(data))
                with self.assertRaises(ValueError):audit.compare(old, new)

    def test_root_alias_and_missing_manifest_are_rejected(self):
        old, new = self.publications()
        alias = new.parent/'alias'; alias.symlink_to(new, target_is_directory=True)
        with self.assertRaises(ValueError):audit.compare(old, alias)
        for root in (old, new):(root/'api/presentation.json').unlink()
        with self.assertRaisesRegex(ValueError, 'missing presentation'):audit.compare(old, new)