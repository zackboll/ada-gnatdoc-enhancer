"""GNATDOC-014: target syntax is narrow; source/config still own authority."""
from dataclasses import replace
import html
import json
from pathlib import Path
import shutil
import unittest

from _helper import Fixture
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import _one
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.syntax import TYPE_LINK, highlighted, linked, plain
from ada_gnatdoc_enhancer.util import digest


class ExternalTypeTarget(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture('imgproc'); self.addCleanup(self.fx.cleanup)
        self.path = self.fx.root/'project.toml'
        self.original = self.path.read_text()
        self.config = replace(self.fx.config, external_type_target='_top',
                              externals={'opencv.core.mat': 'https://core.invalid/api/page.html#mat'},
                              allowed_hosts=frozenset({'core.invalid'}))
        source = self.fx.root/'consumer.ads'
        source.write_text('with OpenCV.Core;\npackage Consumer is\n'
                          'type Local is range 0 .. 9;\nend Consumer;')
        self.pkg = _one(source)

    def render(self, code, config=None, source=None, targets=None, pkg=None):
        return linked(html.escape(code, quote=False), pkg or self.pkg, source or {},
                      None, targets or {}, config or self.config)[0]

    def test_strict_configuration(self):
        self.assertIsNone(load(self.fx.root, 'project.toml').external_type_target)
        self.path.write_text(self.original+'\nexternal_type_target = "_top"\n')
        self.assertEqual(load(self.fx.root, 'project.toml').external_type_target, '_top')
        for value in ('""', '"_self"', '"_blank"', '"_parent"', '"document-content"',
                      '"_TOP"', '" _top"', '"_top "', 'true', 'false', '1',
                      '["_top"]', '{target="_top"}', '"_top\\\" onclick=\\\"evil"'):
            with self.subTest(value=value):
                self.path.write_text(self.original+'\nexternal_type_target = '+value+'\n')
                with self.assertRaises(ValueError):load(self.fx.root, 'project.toml')

    def test_unknown_and_misplaced_keys_rejected(self):
        for text in (self.original+'\nexternal_type_targets = "_top"\n',
                     'external_type_target = "_top"\n'+self.original,
                     self.original+'\n[navigation_extra]\nexternal_type_target = "_top"\n'):
            self.path.write_text(text)
            with self.assertRaises(ValueError):load(self.fx.root, 'project.toml')

    def test_external_only_and_preserved_regex_groups(self):
        code = 'function Copy (X : OpenCV.Core.Mat; Y : Local) return OpenCV.Core.Mat;'
        targets = {'consumer.local': (Path('local.html'), 'local')}
        default = self.render(code, replace(self.config, external_type_target=None), targets=targets)
        actual = self.render(code, targets=targets)
        self.assertEqual(actual.replace(' target="_top"', ''), default)
        links = list(TYPE_LINK.finditer(actual))
        self.assertEqual(len(links), 3)
        self.assertEqual([m[3] for m in links], ['OpenCV.Core.Mat', 'Local', 'OpenCV.Core.Mat'])
        self.assertEqual([bool('target=' in m[0]) for m in links], [True, False, True])
        self.assertEqual(plain(actual), code)
        self.assertEqual(plain(highlighted(actual)), code)
        self.assertEqual(list(TYPE_LINK.finditer(highlighted(actual)))[0].groups(), links[0].groups())

    def test_source_visibility_guards_unchanged(self):
        for context in ('', 'private with OpenCV.Core;', 'limited with OpenCV.Core;'):
            p = self.fx.root/'guard.ads'
            p.write_text(context+'\npackage Consumer is end Consumer;')
            actual = self.render('function Copy return OpenCV.Core.Mat;', pkg=_one(p))
            self.assertNotIn('<a ', actual)
        # Source-owned packages cannot fall through to an external mapping.
        self.assertNotIn('<a ', self.render('function Copy return OpenCV.Core.Mat;',
                                         source={'opencv.core': self.pkg}))
        for code in ('-- X : OpenCV.Core.Mat', 'S := "X : OpenCV.Core.Mat";',
                     'function Copy return Mat;'):
            self.assertNotIn('<a ', self.render(code))

    def test_local_ownership_wins(self):
        actual = self.render('function Copy return OpenCV.Core.Mat;',
                             targets={'opencv.core.mat': (Path('native.html'), 'mat')})
        self.assertIn('href="native.html#mat"', actual)
        self.assertNotIn('target=', actual)

    def test_strict_snippet_grammar(self):
        valid = self.render('function Copy return OpenCV.Core.Mat;')
        self.assertIn('target="_top"', valid)
        for attribute in (' target="_blank"', ' target="_self"', ' target="_parent"',
                          ' target="named"', ' target=_top', " target='_top'",
                          ' TARGET="_top"', ' target="_top" target="_top"',
                          ' target="_top" onclick="evil()"', ' rel="opener"'):
            with self.subTest(attribute=attribute), self.assertRaises(ValueError):
                plain(valid.replace(' target="_top"', attribute))
        with self.assertRaises(ValueError):
            plain(valid.replace('>OpenCV.Core.Mat</a>', '><a>OpenCV.Core.Mat</a></a>'))

    def test_no_external_links_means_exact_default_bytes(self):
        enhance(self.fx.config, self.fx.site); before = hashes(self.fx.site)
        config = replace(self.fx.config, external_type_target='_top')
        enhance(config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))
        verify(config, self.fx.site)

    def test_generic_instance_links_remain_local(self):
        fixture = Path(__file__).parent/'real-fixtures/generic-core'
        root = self.fx.root/'generic'; shutil.copytree(fixture, root)
        config = replace(load(root, 'enhancer.toml'), instance_references=True,
                         symbol_bookmarks=True, default_package='OpenCV.Core', external_type_target='_top')
        from ada_gnatdoc_enhancer.instance_references import targets
        from ada_gnatdoc_enhancer.inventory import packages
        from ada_gnatdoc_enhancer.native_html import snapshot
        source = packages(config); native = snapshot(config, root/'pristine')
        refs = targets(config, source, native)
        enhance(config, root/'pristine'); verify(config, root/'pristine')
        path = root/'accessor.ads'
        path.write_text('with OpenCV.Core.UInt8_Vec2;\npackage OpenCV.Core.Accessor is\n'
                        'function Get return UInt8_Vec2.Vector;\nend OpenCV.Core.Accessor;')
        pkg = _one(path); source[pkg.name.lower()] = pkg
        actual, count = linked('function Get return UInt8_Vec2.Vector;', pkg, source,
                               native, {}, config, refs)
        self.assertEqual(count, 1)
        self.assertIn('data-type="opencv.core.uint8_vec2.vector"', actual)
        self.assertNotIn('target=', actual)


class ExternalTargetPublication(unittest.TestCase):
    def setUp(self):
        from test_external_types import AuthenticPinnedExternals
        self.fixture = AuthenticPinnedExternals()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.config, _ = self.fixture.configure('0.5.0')
        self.site = self.fixture.root/'site'
        self.top = replace(self.config, external_type_target='_top')
        self.pristine = self.fixture.root/'pristine'
        shutil.copytree(self.site, self.pristine)

    def reset(self):
        shutil.rmtree(self.site)
        shutil.copytree(self.pristine, self.site)

    def test_manifest_dependencies_and_all_presentation_modes(self):
        for highlight in (True, False):
            for theme in (True, False):
                with self.subTest(highlight=highlight, theme=theme):
                    self.reset()
                    config = replace(self.top, highlight=highlight, theme=theme)
                    result = enhance(config, self.site)
                    self.assertEqual(result['linked_external_types'], 94)
                    self.assertEqual(result['linked_local_types'], 171)
                    pages = '\n'.join(p.read_text() for p in (self.site/'api').glob('*.html'))
                    self.assertEqual(pages.count('target="_top"'), 94)
                    verify(config, self.site)
                    before = hashes(self.site); enhance(config, self.site)
                    self.assertEqual(before, hashes(self.site))

    def test_disabled_type_links_and_no_target_bytes(self):
        config = replace(self.top, type_links=False)
        result = enhance(config, self.site)
        self.assertEqual(result['linked_types'], 0)
        self.assertNotIn('target="_top"', ''.join(p.read_text() for p in (self.site/'api').glob('*.html')))
        before = hashes(self.site)
        enhance(replace(config, external_type_target=None), self.site)
        self.assertEqual(before, hashes(self.site))

    def test_config_not_output_authorizes_target(self):
        enhance(self.config, self.site)
        with self.assertRaises(ValueError):verify(self.top, self.site)
        with self.assertRaises(ValueError):enhance(self.top, self.site)
        self.reset()
        enhance(self.top, self.site)
        with self.assertRaises(ValueError):verify(self.config, self.site)
        self.reset()
        enhance(self.config, self.site); verify(self.config, self.site)
        self.assertNotIn('target="_top"', ''.join(p.read_text() for p in (self.site/'api').glob('*.html')))

    def test_target_mutations_rejected_even_with_rehashed_manifest(self):
        enhance(self.top, self.site)
        page = next(p for p in (self.site/'api').glob('*.html') if 'target="_top"' in p.read_text())
        original = page.read_text()
        manifest = self.site/'api/presentation.json'; manifest_bytes = manifest.read_bytes()
        for replacement in ('', ' target="_blank"', ' target="_self"', ' target="_parent"',
                            ' target="named"', ' target="_top" target="_top"',
                            ' target="_top" onclick="evil()"'):
            with self.subTest(replacement=replacement):
                page.write_text(original.replace(' target="_top"', replacement, 1))
                data = json.loads(manifest_bytes)
                data['output_sha256'][page.relative_to(self.site).as_posix()] = digest(page.read_bytes())
                manifest.write_text(json.dumps(data))
                with self.assertRaises(ValueError):verify(self.top, self.site)
        page.write_text(original); manifest.write_bytes(manifest_bytes)
        # A valid grammar token on an internal link is still unauthorized.
        local = next(m for m in TYPE_LINK.finditer(original) if not m[1].startswith('https:'))
        page.write_text(original.replace(local[0], local[0].replace('>', ' target="_top">', 1), 1))
        with self.assertRaises(ValueError):verify(self.top, self.site)


if __name__ == '__main__':unittest.main()