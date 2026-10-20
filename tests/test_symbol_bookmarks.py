"""Additive opt-in tests; synthetic inputs never certify real Core output."""
import json
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.symbols import public_symbols
from ada_gnatdoc_enhancer.theme import asset
from ada_gnatdoc_enhancer.util import digest
from _helper import Fixture


class SymbolBookmarks(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.config = replace(self.fx.config, symbol_bookmarks=True, default_package='OpenCV.Core')

    def test_disabled_asset_identity(self):
        enhance(self.fx.config, self.fx.site)
        self.assertEqual(digest((self.fx.site/'api/gnatdoc-navigation.js').read_bytes()),
                         'b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd')
        self.assertNotIn('type-navigation', (self.fx.site/'api/index.html').read_text())

    def test_explicit_false_retains_every_byte(self):
        from ada_gnatdoc_enhancer.pipeline import expected_output
        self.assertEqual(expected_output(self.fx.config, self.fx.site)[1:],
                         expected_output(replace(self.fx.config, symbol_bookmarks=False), self.fx.site)[1:])

    def test_real_observed_destinations_and_source_spelling(self):
        native = snapshot(self.config, self.fx.site)
        symbols = dict(public_symbols(self.config, native))
        self.assertIn('OpenCV.Core.Mat', symbols)
        for identity, d in symbols.items():
            self.assertEqual(identity, d.package+'.'+d.declaration.name)
            self.assertIn(d.section, d.page.sections)
            self.assertIn(d.section.anchor, d.page.original)

    def test_opt_in_exact_asset_and_idempotence(self):
        enhance(self.config, self.fx.site)
        self.assertEqual((self.fx.site/'api/gnatdoc-navigation.js').read_bytes(),
                         asset('gnatdoc-symbol-navigation.js'))
        before = hashes(self.fx.site)
        verify(self.config, self.fx.site); enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))

    def test_unknown_default_fails_without_writes(self):
        before = hashes(self.fx.site)
        with self.assertRaises(EnhancementError):
            enhance(replace(self.config, default_package='Unknown.Owner'), self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))

    def test_wrong_existing_section_rejected(self):
        native = snapshot(self.config, self.fx.site)
        page = native.pages['opencv.core']
        page.sections[0] = replace(page.sections[0], code=page.sections[1].code)
        with self.assertRaises(EnhancementError):public_symbols(self.config, native)

    def test_duplicate_native_profile_rejected(self):
        native = snapshot(self.config, self.fx.site)
        page = native.pages['opencv.core']
        page.sections.append(replace(page.sections[0], anchor='f'*64))
        with self.assertRaises(EnhancementError):public_symbols(self.config, native)

    def test_mutations_observed_rejected_and_restored(self):
        enhance(self.config, self.fx.site); before = hashes(self.fx.site)
        index = self.fx.site/'api/index.html'; original = index.read_text()
        manifest = self.fx.site/'api/presentation.json'
        data = json.loads(manifest.read_text()); data['counts']['public_symbols'] = 999
        cases = [(index, original.replace('data-symbol="OpenCV.Core.Mat"',
                                          'data-symbol="OpenCV.Core.Invented"')),
                 (index, original.replace('data-symbol="OpenCV.Core.Mat"',
                                          'data-symbol="OpenCV.Core.Sparse.Sparse_Mat"')),
                 (index, original.replace('<div id="type-navigation"', '<div id="forged-navigation"')),
                 (manifest, json.dumps(data)),
                 (self.fx.site/'api/gnatdoc-navigation.js', '/* forged */'),
                 (index, original.replace('data-symbol=', 'data-forged-symbol='))]
        for path, changed in cases:
            with self.subTest(path=path):
                saved = path.read_bytes(); self.assertNotEqual(saved, changed.encode())
                try:
                    path.write_text(changed)
                    self.assertNotEqual(before, hashes(self.fx.site))
                    with self.assertRaises(EnhancementError):verify(self.config, self.fx.site)
                finally:path.write_bytes(saved)
                self.assertEqual(before, hashes(self.fx.site)); verify(self.config, self.fx.site)


class SymbolConfiguration(unittest.TestCase):
    def test_settings_fail_closed(self):
        fx = Fixture(); self.addCleanup(fx.cleanup)
        path = fx.root/'project.toml'; original = path.read_text()
        cases = ['symbol_bookmarks = true', 'symbol_bookmarks = "true"',
                 'default_package = "OpenCV.Core"',
                 'symbol_bookmarks = true\ndefault_package = "../Core"',
                 'symbol_bookmarks = true\ndefault_package = "OpenCV.Core"\nunknown = true']
        for settings in cases:
            with self.subTest(settings=settings):
                path.write_text(original.replace('mode = "packages"', 'mode = "packages"\n'+settings))
                with self.assertRaises(EnhancementError):load(fx.root,'project.toml')

    def test_valid_opt_in_and_incompatible_modes(self):
        fx = Fixture(); self.addCleanup(fx.cleanup)
        path = fx.root/'project.toml'; original = path.read_text()
        for mode in ('packages', 'operations', 'none'):
            path.write_text(original.replace('mode = "packages"', 'mode = "'+mode+'"\n'
                'symbol_bookmarks = true\ndefault_package = "OpenCV.Core"'))
            if mode == 'packages':self.assertTrue(load(fx.root,'project.toml').symbol_bookmarks)
            else:
                with self.assertRaises(EnhancementError):load(fx.root,'project.toml')