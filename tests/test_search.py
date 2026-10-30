"""Dedicated deterministic index, authority, mutation and real-Core regressions."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.search import INDEX, flat_public, records, runtime
from ada_gnatdoc_enhancer.theme import asset
from ada_gnatdoc_enhancer.util import digest, sorted_json
from _helper import Fixture

REAL = Path(__file__).parent/'real-fixtures/search-core'


class Search(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.config = replace(self.fx.config, search=True)

    def test_explicit_versioned_configuration(self):
        path = self.fx.root/'project.toml'; original = path.read_text()
        self.assertFalse(self.fx.config.search)
        path.write_text(original + '\n[search]\nschema_version = 1\nmode = "documentation"\n')
        self.assertTrue(load(self.fx.root, 'project.toml').search)
        for options in ('schema_version = 2\nmode = "documentation"',
                        'schema_version = true\nmode = "documentation"',
                        'mode = "documentation"', 'schema_version = 1\nmode = "remote"',
                        'schema_version = 1\nmode = "documentation"\nurl = "evil"'):
            path.write_text(original + '\n[search]\n' + options)
            with self.subTest(options=options), self.assertRaises(EnhancementError):
                load(self.fx.root, 'project.toml')
        path.write_text(original.replace('mode = "packages"', 'mode = "none"') +
                        '\n[search]\nschema_version = 1\nmode = "documentation"')
        with self.assertRaises(EnhancementError): load(self.fx.root, 'project.toml')

    def test_opt_in_inventory_and_deterministic_reconstruction(self):
        other = self.fx.root/'second'; shutil.copytree(self.fx.site, other)
        enhance(self.config, self.fx.site); enhance(self.config, other)
        self.assertEqual(hashes(self.fx.site), hashes(other))
        before = hashes(self.fx.site)
        verify(self.config, self.fx.site); enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))
        self.assertIn(INDEX, before)
        self.assertIn('api/gnatdoc-search.css', before)
        with self.assertRaises(EnhancementError): verify(self.fx.config, self.fx.site)

    def test_default_has_accurate_label_and_no_new_files(self):
        enhance(self.fx.config, self.fx.site)
        self.assertFalse((self.fx.site/INDEX).exists())
        self.assertIn('Filter navigation links</label>', (self.fx.site/'api/index.html').read_text())
        self.assertNotIn('Search documentation</label>', (self.fx.site/'api/index.html').read_text())

    def test_three_variants_share_search_without_changing_legacy_assets(self):
        for name in ('gnatdoc-navigation.js', 'gnatdoc-symbol-navigation.js', 'gnatdoc-instance-navigation.js'):
            value = runtime(asset(name))
            self.assertTrue(value.startswith(asset('gnatdoc-search.js')))
            self.assertEqual(value.count(b'window.gnatdocDocumentationSearch ='), 1)
            self.assertNotIn(b'function filter()', value)
            self.assertIn(b'const filter = window.gnatdocDocumentationSearch', value)

    def test_modified_missing_duplicated_forged_and_rehashed_index_rejected(self):
        enhance(self.config, self.fx.site)
        path = self.fx.site/INDEX; original = path.read_bytes()
        data = json.loads(original)
        mutations = [b'{}', original + b' ', sorted_json(dict(data, records=data['records'][:-1])).encode(),
                     sorted_json(dict(data, records=data['records'] + [data['records'][0]])).encode()]
        forged = json.loads(original); forged['records'][0]['href'] = 'https://evil.invalid/'
        mutations.append(sorted_json(forged).encode())
        for value in mutations:
            with self.subTest(value=value[:50]):
                path.write_bytes(value)
                # Output-side checksums cannot bless a forged cache.
                mp = self.fx.site/'api/presentation.json'; manifest = json.loads(mp.read_text())
                manifest['output_sha256'][INDEX] = digest(value); mp.write_text(sorted_json(manifest))
                with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        path.unlink()
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_rehashed_shell_cannot_expand_destination_authority(self):
        enhance(self.config, self.fx.site)
        path = self.fx.site/'api/index.html'
        value = path.read_text().replace('data-search-name="OpenCV.Core"',
                                         'data-search-name="Forged.Public"', 1)
        path.write_text(value)
        mp = self.fx.site/'api/presentation.json'; data = json.loads(mp.read_text())
        data['output_sha256']['api/index.html'] = digest(value.encode())
        mp.write_text(sorted_json(data))
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_private_internal_and_unsupported_scopes_excluded(self):
        package = next(iter(packages(self.fx.config).values()))
        for source in ('package Example is\n type Public_View is private;\nprivate type Hidden is null record;\nend Example;',
                       'package Example is\n type Public_View is private;\nprivate\n type Hidden is null record;\nend Example;'):
            public = flat_public(replace(package, source=source))
            self.assertIn('Public_View', public); self.assertNotIn('Hidden', public)
        for source in ('package Example is\n package Nested is\n type Hidden is null record;\n end Nested;\nend Example;',
                       'package Example renames Other;', 'package Example is\n protected Thing is\nend Thing;\nend Example;'):
            self.assertEqual(flat_public(replace(package, source=source)), '')
        # Inventory packages with Internal components remain native-only.
        path = self.fx.root/'src/opencv-core-sparse.ads'
        path.write_text(path.read_text().replace('OpenCV.Core.Sparse', 'OpenCV.Core.Internal'))
        page = next(p for p in (self.fx.site/'api').glob('*.html') if '<h1>OpenCV.Core.Sparse</h1>' in p.read_text())
        page.write_text(page.read_text().replace('OpenCV.Core.Sparse', 'OpenCV.Core.Internal'))
        index = self.fx.site/'api/index.html'; index.write_text(index.read_text().replace('OpenCV.Core.Sparse', 'OpenCV.Core.Internal'))
        config = replace(self.config, expected_packages=())
        values = records(config, snapshot(config, self.fx.site), {})
        self.assertFalse(any('Internal' in r['name'] for r in values))


class RealCoreSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.root = Path(cls.temp.name)
        cls.authority = cls.root/'authority'; shutil.copytree(REAL/'authority', cls.authority)
        cls.config = replace(load(cls.authority, 'default.toml'), search=True)
        cls.site = cls.root/'site'; shutil.copytree(REAL/'pristine', cls.site)
        enhance(cls.config, cls.site)
        cls.records = json.loads((cls.site/INDEX).read_text())['records']

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_fixture_hashes(self):
        data = json.loads((REAL/'provenance.json').read_text())
        for name, expected in data['files'].items():
            self.assertEqual(digest((REAL/name).read_bytes()), expected, name)

    def test_required_queries(self):
        for query, kind, identity in (
                ('Sparse', 'package', 'OpenCV.Core.Sparse'),
                ('Mat', 'symbol', 'OpenCV.Core.Mat'),
                ('Create', 'operation', 'OpenCV.Core.Create'),
                ('Clone', 'operation', 'OpenCV.Core.Clone'),
                ('OpenCV.Core.Mat', 'symbol', 'OpenCV.Core.Mat'),
                ('ownership', 'guide', 'Ownership and views')):
            with self.subTest(query=query):
                found = [r for r in self.records if query.lower() in (r['name']+' '+r['text']).lower()]
                self.assertTrue(any(r['kind'] == kind and r['name'] == identity for r in found))
        self.assertFalse(any('unknown-gnatdoc023' in (r['name']+' '+r['text']).lower() for r in self.records))

    def test_independent_native_oracle_and_overloads(self):
        oracle = json.loads((REAL/'oracle.json').read_text())
        allowed = {r['href']:r for r in oracle}
        for record in self.records:
            if record['kind'] not in ('operation', 'symbol'): continue
            self.assertIn(record['href'], allowed)
            expected = allowed[record['href']]
            self.assertEqual(record['name'], expected['package']+'.'+expected['name'])
        create = [r for r in self.records if r['name'] == 'OpenCV.Core.Create']
        self.assertEqual(len(create), 3)
        self.assertEqual(len({r['href'] for r in create}), 3)
        self.assertEqual([r['label'] for r in create],
                         [f'OpenCV.Core.Create (overload {i}/3)' for i in range(1,4)])
        self.assertTrue(all('function Create' in r['text'] for r in create))

    def test_no_private_internal_or_fabricated_instances(self):
        self.assertFalse(any('.internal.' in r['name'].lower() for r in self.records))
        native = snapshot(self.config, REAL/'pristine')
        allowed = {d.href for group in source_destinations(self.config, native).values() for d in group}
        self.assertTrue(all(r['href'] in allowed for r in self.records if r['kind'] in ('operation','symbol')))
        # Instance-specific Matrix/Vector member anchors do not exist natively.
        self.assertFalse(any(r['name'] == 'OpenCV.Core.Float32_Vec3.Vector' for r in self.records))

    def test_custom_theme_and_native_bytes_preserved(self):
        verify(self.config, self.site)
        self.assertEqual((self.site/'api/gnatdoc-theme.css').read_bytes(),
                         (self.authority/'docs/assets/gnatdoc-theme.css').read_bytes())
        self.assertEqual((self.site/'api/gnatdoc.css').read_bytes(), (REAL/'pristine/api/gnatdoc.css').read_bytes())
        self.assertEqual(len([r for r in self.records if r['kind'] == 'guide']), 5)