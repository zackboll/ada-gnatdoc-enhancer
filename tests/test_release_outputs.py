"""Fail-closed classification of the two independent release output baselines."""
import importlib.util
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
        for root, version in zip(roots, ('0.1.1', '0.1.2')):
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

    def test_official_default_requires_exact_approved_router_bytes(self):
        old, new = self.publications()
        for root in (old, new):(root/'api/gnatdoc-navigation.js').write_bytes(b'unapproved')
        with self.assertRaisesRegex(ValueError, 'unapproved official default router'):
            audit.compare(old, new, official=True, default_router=True)