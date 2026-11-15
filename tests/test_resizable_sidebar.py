"""Opt-in authorization, exact reconstruction and adversarial publication tests."""
from dataclasses import replace
import json
import shutil
import unittest

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.resize import DIVIDER
from ada_gnatdoc_enhancer.theme import asset
from ada_gnatdoc_enhancer.util import digest, sorted_json
from _helper import Fixture


class ResizableSidebar(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.config = replace(self.fx.config, resizable_sidebar=True)

    def test_explicit_boolean_configuration(self):
        path = self.fx.root/'project.toml'; original = path.read_text()
        self.assertFalse(self.fx.config.resizable_sidebar)
        for value in ('true', 'false', '1', '0', '"true"', '[]', '{}'):
            path.write_text(original.replace('[navigation]', '[navigation]\nresizable_sidebar = '+value))
            with self.subTest(value=value):
                if value in ('true', 'false'):
                    self.assertEqual(load(self.fx.root, 'project.toml').resizable_sidebar, value == 'true')
                else:
                    with self.assertRaises(EnhancementError): load(self.fx.root, 'project.toml')
        path.write_text(original.replace('[navigation]', '[navigation]\nresizable_sidebar = true').replace(
            'theme = true', 'theme = false'))
        with self.assertRaises(EnhancementError): load(self.fx.root, 'project.toml')
        with self.assertRaises(EnhancementError):
            enhance(replace(self.config, theme=False), self.fx.site)

    def test_disabled_omitted_and_false_identical(self):
        other = self.fx.root/'second'; shutil.copytree(self.fx.site, other)
        enhance(self.fx.config, self.fx.site)
        path = self.fx.root/'project.toml'
        path.write_text(path.read_text().replace('[navigation]', '[navigation]\nresizable_sidebar = false'))
        enhance(load(self.fx.root, 'project.toml'), other)
        self.assertEqual(hashes(self.fx.site), hashes(other))
        self.assertFalse(any('resize' in name for name in hashes(other)))
        self.assertNotIn(DIVIDER, (other/'api/index.html').read_text())

    def test_exact_opt_in_delta_deterministic_and_idempotent(self):
        baseline = self.fx.root/'baseline'; shutil.copytree(self.fx.site, baseline)
        other = self.fx.root/'second'; shutil.copytree(self.fx.site, other)
        enhance(self.fx.config, baseline)
        enhance(self.config, self.fx.site); enhance(self.config, other)
        before = hashes(self.fx.site)
        self.assertEqual(before, hashes(other))
        verify(self.config, self.fx.site); enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))
        old = hashes(baseline)
        self.assertEqual(set(before) - set(old), {'api/gnatdoc-resize.css', 'api/gnatdoc-resize.js'})
        self.assertEqual({n for n in old if old[n] != before[n]},
                         {'api/index.html', 'api/presentation.json'})
        for name in ('gnatdoc-resize.css', 'gnatdoc-resize.js'):
            self.assertEqual((self.fx.site/'api'/name).read_bytes(), asset(name))
        self.assertIn(DIVIDER, (self.fx.site/'api/index.html').read_text())
        with self.assertRaises(EnhancementError): verify(self.fx.config, self.fx.site)

    def test_all_navigation_modes(self):
        for profile in ('core', 'imgproc', 'geometry', 'mel'):
            fx = Fixture(profile)
            try:
                config = replace(fx.config, resizable_sidebar=True)
                enhance(config, fx.site); verify(config, fx.site)
            finally: fx.cleanup()
        # Resizing has no dependency on a router, even native navigation alone.
        config = replace(self.config, navigation='none')
        enhance(config, self.fx.site); verify(config, self.fx.site)
        self.assertFalse((self.fx.site/'api/gnatdoc-navigation.js').exists())

    def test_changed_assets_and_rehashed_manifest_rejected(self):
        enhance(self.config, self.fx.site)
        manifest = self.fx.site/'api/presentation.json'; original = manifest.read_bytes()
        for name in ('gnatdoc-resize.js', 'gnatdoc-resize.css', 'index.html'):
            path = self.fx.site/'api'/name; content = path.read_bytes()
            for rehash in (False, True):
                with self.subTest(name=name, rehash=rehash):
                    path.write_bytes(content+b'<!-- altered -->')
                    if rehash:
                        data = json.loads(original)
                        data['output_sha256']['api/'+name] = digest(path.read_bytes())
                        manifest.write_text(sorted_json(data))
                    with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
                    path.write_bytes(content); manifest.write_bytes(original)

    def test_unapproved_assets_and_scripts_rejected(self):
        enhance(self.fx.config, self.fx.site)
        for name in ('gnatdoc-resize.js', 'gnatdoc-resize.css', 'unauthorized-resize.js'):
            path = self.fx.site/'api'/name; path.write_bytes(b'/* unauthorized */')
            with self.subTest(name=name), self.assertRaises(EnhancementError):
                verify(self.fx.config, self.fx.site)
            path.unlink()
        index = self.fx.site/'api/index.html'
        index.write_text(index.read_text().replace('</head>',
                         '<script src="gnatdoc-resize.js" defer></script></head>'))
        with self.assertRaises(EnhancementError): verify(self.fx.config, self.fx.site)

    def test_missing_and_symlink_assets_rejected(self):
        enhance(self.config, self.fx.site)
        for name in ('gnatdoc-resize.js', 'gnatdoc-resize.css'):
            path = self.fx.site/'api'/name; content = path.read_bytes(); path.unlink()
            with self.subTest(name=name), self.assertRaises(EnhancementError):
                verify(self.config, self.fx.site)
            outside = self.fx.root/name; outside.write_bytes(content); path.symlink_to(outside)
            with self.subTest(name=name), self.assertRaises(EnhancementError):
                verify(self.config, self.fx.site)
            path.unlink(); path.write_bytes(content)

    def test_enabled_cannot_verify_disabled_output(self):
        enhance(self.fx.config, self.fx.site)
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_native_shell_must_be_qualified(self):
        path = self.fx.site/'api/index.html'
        path.write_text(path.read_text().replace('<div class=document-content>', '<div class=unknown>'))
        before = hashes(self.fx.site)
        with self.assertRaises(EnhancementError): enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))