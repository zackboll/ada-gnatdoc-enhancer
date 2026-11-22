"""Mutations against the distinct official and frozen compatibility contracts."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


with patch.object(sys, 'path', [str(Path(__file__).resolve().parents[1]/'scripts'), *sys.path]):
    audit = importlib.import_module('compare_release_017_018')


class ReleaseParity(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.old = Path(tmp.name)/'old'; self.new = Path(tmp.name)/'new'

    def write(self, root, name, data):
        path = root/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)

    def fixture(self, schema):
        for root, version in ((self.old, '0.1.7'), (self.new, '0.1.8')):
            self.write(root, 'api/native.html', b'<h1>X</h1>')
            self.write(root, 'api/search.js', b'/* unchanged */')
            source = 'api/source/x.ads.html'
            if schema:
                self.write(root, source, b'<code>package X;</code>')
                self.write(root, audit.CSS, b'retained style')
            data = dict(enhancer_version=version, inventory=['a', 'b'], output_sha256={
                n: audit.sha(d) for n, d in audit.files(root).items() if n != audit.MANIFEST})
            if schema:
                data['source_view'] = {'schema_version': schema, 'files': [{'page': source}]}
            self.write(root, audit.MANIFEST, (json.dumps(data, indent=2, sort_keys=True)+'\n').encode())

    def compare(self, authority='frozen', schema=0, **kwargs):
        return audit.compare(self.old, self.new, authority=authority, schema=schema, **kwargs)

    def reseal(self):
        path = self.new/audit.MANIFEST
        data = json.loads(path.read_bytes())
        data['output_sha256'] = {n: audit.sha(d) for n, d in audit.files(self.new).items() if n != audit.MANIFEST}
        path.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')

    def test_version_only_for_both_baselines_and_every_frozen_mode(self):
        self.fixture(0)
        self.assertEqual(self.compare('official')['changed_files'], [audit.MANIFEST])
        for schema in (0, 1, 2):
            self.fixture(schema)
            self.assertEqual(self.compare(schema=schema)['changed_files'], [audit.MANIFEST])
        with self.assertRaisesRegex(ValueError, 'does not support schema 2'):
            self.compare('official', 2)

    def test_exact_serialization_and_manifest_inventory(self):
        for old, new in ((b'[\n    "a",\n    "b"', b'[\n    "b",\n    "a"'),
                         (audit.NEW, audit.OLD), (audit.NEW, audit.NEW+b',\n  '+audit.NEW),
                         (audit.NEW, b'"enhancer_version":"0.1.8"')):
            with self.subTest(new=new):
                self.fixture(0)
                path = self.new/audit.MANIFEST
                path.write_bytes(path.read_bytes().replace(old, new))
                with self.assertRaises(ValueError): self.compare()

    def test_resealed_mutations_and_inventory_changes_rejected(self):
        for name in ('api/native.html', 'api/search.js', 'api/extra.css'):
            self.fixture(0)
            self.write(self.new, name, b'changed'); self.reseal()
            with self.assertRaises(ValueError): self.compare('official')
            if name.endswith('extra.css'): (self.new/name).unlink()
        (self.new/'api/native.html').unlink()
        with self.assertRaisesRegex(ValueError, 'file inventory'): self.compare()
        (self.new/'api/native.html').symlink_to(self.old/'api/native.html')
        with self.assertRaisesRegex(ValueError, 'nonregular'): self.compare()

    def test_only_official_schema1_allows_classified_highlighting(self):
        self.fixture(1)
        new_css = b'new style'
        self.write(self.new, audit.CSS, new_css); self.reseal()
        with patch.object(audit, 'STYLESHEETS', (audit.sha(b'retained style'), audit.sha(new_css))):
            self.compare('official', 1, highlighted=False)
            source = 'api/source/x.ads.html'
            self.write(self.new, source, b'<code><span class="ada-keyword">package</span> X;</code>'); self.reseal()
            self.compare('official', 1)
            for mode in ('frozen', 'plain', 'active', 'text', 'css'):
                with self.subTest(mode=mode):
                    if mode == 'active':
                        self.write(self.new, source, b'<code><span class="ada-keyword" onclick="x">package</span> X;</code>')
                    if mode == 'text': self.write(self.new, source, b'<code>package Y;</code>')
                    if mode == 'css': self.write(self.new, audit.CSS, b'arbitrary style')
                    self.reseal()
                    with self.assertRaises(ValueError):
                        self.compare('frozen' if mode == 'frozen' else 'official', 1, highlighted=mode != 'plain')