"""Ordinary subtype candidates use the unchanged source/native resolver."""
import copy
from dataclasses import replace
import html
import json
from pathlib import Path
import tempfile
import unittest

from _helper import Fixture
import test_external_types as external_fixture
from ada_gnatdoc_enhancer.external_types import destinations, inventory, read_json
from ada_gnatdoc_enhancer.inventory import _one, Declaration
from ada_gnatdoc_enhancer.native_html import SECTION
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.syntax import (
    TYPE_LINK, SPAN, highlighted, linked, plain, type_positions,
)
from ada_gnatdoc_enhancer.util import digest, sorted_json

NEW = external_fixture.NEW
OLD = external_fixture.OLD
POINT_PAGE = 'ea2ebcbc108269c77d7c6d44d2dabdfb5f6d0179ad5622b1be3cbceaee5c44aa.html'
POINT_ANCHOR = 'da696e09a1f1b297516365244e16533e23cca626f26df4bb3f727a64beb697b0'
POINT_URL = 'https://core.invalid/' + NEW + '/api/' + POINT_PAGE + '#' + POINT_ANCHOR
UINT8_URL = ('https://core.invalid/' + NEW + '/api/' + POINT_PAGE +
             '#126c1f5d92cb06b013208cdd3e16f14713f74cc2cf2b63dc4ec9ab2558a5981e')


class SubtypeContexts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / 'consumer.ads'
        path.write_text('with OpenCV;\npackage Consumer is\n'
                        'type Base is range 0 .. 100;\nend Consumer;')
        self.pkg = _one(path)
        self.fx = Fixture('geometry')
        self.addCleanup(self.fx.cleanup)
        self.config = replace(self.fx.config, externals={
            'opencv.point_array': POINT_URL, 'opencv.uint8_value': UINT8_URL})
        self.targets = {'consumer.base': (Path('local.html'), 'actual-base')}

    def render(self, code, pkg=None, targets=None):
        return linked(code, pkg or self.pkg, {'consumer': pkg or self.pkg},
                      None, self.targets if targets is None else targets, self.config)[0]

    def test_exact_external_occurrence_and_destination(self):
        code = 'subtype Contour is OpenCV.Point_Array;'
        self.assertEqual(type_positions(code), [(19, 37, 'OpenCV.Point_Array')])
        result = self.render(code)
        self.assertEqual(TYPE_LINK.findall(result), [(POINT_URL, 'opencv.point_array',
                                                     'OpenCV.Point_Array')])
        self.assertEqual(plain(result), code)
        self.assertEqual(TYPE_LINK.sub(lambda m: m[3], result), code)

    def test_local_base_target(self):
        code = 'subtype Small is Base range 0 .. 10;'
        self.assertEqual(type_positions(code), [(17, 21, 'Base')])
        self.assertEqual(TYPE_LINK.findall(self.render(code)),
                         [('local.html#actual-base', 'consumer.base', 'Base')])

    def test_line_breaks_and_comments_preserve_offsets(self):
        code = '  subtype Point_Set is -- base follows\n  OpenCV.Point_Array;'
        start = code.index('OpenCV.Point_Array')
        self.assertEqual(type_positions(code), [(start, start + 18, 'OpenCV.Point_Array')])
        self.assertEqual(plain(self.render(code)), code)
        self.assertEqual(TYPE_LINK.findall(self.render(code))[0][0], POINT_URL)

    def test_constrained_scalar_links_only_base(self):
        code = 'subtype Small_Value is OpenCV.UInt8_Value range Pkg.Low .. Pkg.High;'
        self.assertEqual(type_positions(code), [(23, 41, 'OpenCV.UInt8_Value')])
        links = TYPE_LINK.findall(self.render(code))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], (UINT8_URL, 'opencv.uint8_value', 'OpenCV.UInt8_Value'))

    def test_array_constraint_does_not_link_bounds(self):
        code = 'subtype C is OpenCV.Point_Array (Pkg.First .. Pkg.Last);'
        self.assertEqual(type_positions(code), [(13, 31, 'OpenCV.Point_Array')])
        self.assertEqual(TYPE_LINK.findall(self.render(code)),
                         [(POINT_URL, 'opencv.point_array', 'OpenCV.Point_Array')])

    def test_differently_named_subtypes_same_owner(self):
        for name in ('First', 'Second'):
            with self.subTest(name=name):
                result = self.render(f'subtype {name} is Base;')
                self.assertEqual(TYPE_LINK.findall(result),
                                 [('local.html#actual-base', 'consumer.base', 'Base')])

    def test_case_insensitive_candidate_canonical_identity(self):
        code = 'SuBtYpE C iS oPeNcV.pOiNt_ArRaY;'
        self.assertEqual(TYPE_LINK.findall(self.render(code)),
                         [(POINT_URL, 'opencv.point_array', 'oPeNcV.pOiNt_ArRaY')])

    def test_entities_highlighting_and_exact_link_removal(self):
        raw = 'subtype C is OpenCV&#46;Point_Array; -- &lt;constraint&gt;'
        rendered = self.render(raw)
        self.assertEqual(TYPE_LINK.findall(rendered),
                         [(POINT_URL, 'opencv.point_array', 'OpenCV&#46;Point_Array')])
        colored = highlighted(rendered)
        self.assertIn('<span class="ada-keyword">subtype</span>', colored)
        self.assertEqual(plain(colored), html.unescape(raw))
        self.assertEqual(TYPE_LINK.sub(lambda m: m[3],
                                      SPAN.sub(lambda m: m[1], colored)), raw)

    def test_derived_type_behavior_unchanged(self):
        code = 'type T is new Consumer.Base;'
        self.assertEqual(type_positions(code), [(14, 27, 'Consumer.Base')])
        self.assertEqual(TYPE_LINK.findall(self.render(code)),
                         [('local.html#actual-base', 'consumer.base', 'Consumer.Base')])

    def test_unrelated_contexts_and_literals_are_not_candidates(self):
        cases = ('type T is record null; end record;', 'type T is range 1 .. 10;',
                 'package T is end T;', 'X := Pkg.Base;',
                 '-- subtype C is OpenCV.Point_Array;',
                 'S := "subtype C is OpenCV.Point_Array;";',
                 "C := 's'; -- subtype C is OpenCV.Point_Array;",
                 'function F return Boolean is (Pkg.Base = Pkg.Other);',
                 'procedure F (X : Integer := Pkg.Base);',
                 'subtype C is Integer range 0 .. 10;',
                 "subtype C is Base'Base;",
                 'package Nested is\n subtype C is OpenCV.Point_Array;\nend Nested;')
        for code in cases:
            with self.subTest(code=code):
                self.assertTrue(code)
                self.assertEqual(type_positions(code), [])
                self.assertEqual(self.render(html.escape(code)), html.escape(code))

    def test_missing_owner_and_private_limited_contexts(self):
        code = 'subtype C is OpenCV.Point_Array;'
        variants = [replace(self.pkg, imports=frozenset())]
        for context in ('private with OpenCV;', 'limited with OpenCV;'):
            variants.append(replace(self.pkg, source=context + '\npackage Consumer is\nend Consumer;'))
        for pkg in variants:
            with self.subTest(source=pkg.source, imports=pkg.imports):
                self.assertEqual(self.render(code, pkg), code)

    def test_alias_nested_and_prefix_shadow_do_not_authorize(self):
        code = 'subtype C is OpenCV.Point_Array;'
        for body in ('package Alias renames OpenCV;',
                     'package Nested is\nsubtype C is OpenCV.Point_Array;\nend Nested;',
                     'OpenCV : Integer;'):
            pkg = replace(self.pkg, source='with OpenCV;\npackage Consumer is\n' + body + '\nend Consumer;')
            self.assertIn(body, pkg.source)
            self.assertEqual(self.render(code, pkg), code)

    def test_local_subtype_in_unsupported_nested_scope_unlinked(self):
        code = 'subtype C is Base;'
        pkg = replace(self.pkg, source=self.pkg.source.replace(
            'end Consumer;', 'package Nested is\nsubtype C is Base;\nend Nested;\nend Consumer;'))
        self.assertIn('package Nested is', pkg.source)
        self.assertEqual(self.render(code, pkg), code)

    def test_unqualified_ambiguous_imports_remain_unlinked(self):
        pkg = replace(self.pkg, imports=frozenset({'a', 'b'}), uses=frozenset({'a', 'b'}))
        targets = {'a.base': (Path('a.html'), 'a'), 'b.base': (Path('b.html'), 'b')}
        code = 'subtype C is Base;'
        self.assertEqual(self.render(code, pkg, targets), code)

    def test_non_type_shadow_and_local_precedence(self):
        code = 'subtype C is Base;'
        pkg = replace(self.pkg, declarations=[Declaration('function', 'Base',
                                                         'function Base return Integer;', 1)])
        self.assertEqual(self.render(code, pkg), code)
        config = replace(self.config, externals={'consumer.base': POINT_URL})
        result, _ = linked(code, self.pkg, {'consumer': self.pkg}, None, self.targets, config)
        self.assertEqual(TYPE_LINK.findall(result)[0][0], 'local.html#actual-base')


class AuthenticContour(unittest.TestCase):
    """A separate allowlist regression; historical 94-link test is unchanged."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gde-contour-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixtures = Path(__file__).parent / 'real-fixtures'
        config, self.manifest = external_fixture.AuthenticPinnedExternals.configure(self, '0.5.0')
        dep = copy.deepcopy(config.dependencies[0])
        self.assertNotIn('OpenCV.Point_Array', dep['types'])
        dep['types'].append('OpenCV.Point_Array')
        self.config = replace(config, dependencies=(dep,))
        self.site = self.root / 'site'

    def contour(self):
        for path in (self.site / 'api').glob('*.html'):
            for match in SECTION.finditer(path.read_text()):
                if match[3] == 'Contour':
                    return path, match[4]
        self.fail('authentic Contour section missing')

    def test_actual_source_native_owner_and_exact_destination(self):
        spec = read_json(self.root / 'dependency/input.json')
        rebuilt = inventory(spec, self.root / 'dependency/source', self.root / 'dependency/native')
        self.assertEqual(rebuilt, self.manifest)
        owner = rebuilt['types']['opencv.point_array']
        self.assertEqual((owner['page'], owner['anchor']), (POINT_PAGE, POINT_ANCHOR))
        self.assertEqual((owner['qualified_name'], owner['source_line']), ('OpenCV.Point_Array', 81))
        source = (self.root / 'consumer/src/opencv-geometry.ads').read_text().splitlines()
        self.assertEqual(source[75].strip(), 'subtype Contour is OpenCV.Point_Array;')
        result = enhance(self.config, self.site)
        self.assertEqual(result['linked_external_types'], 95)
        self.assertEqual(TYPE_LINK.findall(self.contour()[1]),
                         [(POINT_URL, 'opencv.point_array', 'OpenCV.Point_Array')])
        self.assertEqual(verify(self.config, self.site)['linked_external_types'], 95)

    def test_omitted_approved_identity_remains_absent(self):
        dep = copy.deepcopy(self.config.dependencies[0])
        dep['types'].remove('OpenCV.Point_Array')
        self.assertNotIn('OpenCV.Point_Array', dep['types'])
        enhance(replace(self.config, dependencies=(dep,)), self.site)
        self.assertNotIn('type-reference', self.contour()[1])

    def test_wrong_existing_external_anchor_rejected(self):
        owner = self.manifest['types']['opencv.point_array']
        wrong = self.manifest['types']['opencv.rect']['anchor']
        self.assertNotEqual(owner['anchor'], wrong)
        owner['anchor'] = wrong
        path = self.root / 'dependency/types.json'
        path.write_text(sorted_json(self.manifest))
        dep = {**self.config.dependencies[0], 'manifest_sha256': digest(path.read_bytes())}
        with self.assertRaisesRegex(ValueError, 'identity evidence'):
            destinations(replace(self.config, dependencies=(dep,)))

    def test_dependency_revision_substitution_rejected(self):
        dep = {**self.config.dependencies[0], 'revision': OLD}
        self.assertNotEqual(dep['revision'], NEW)
        with self.assertRaisesRegex(ValueError, 'revision mismatch'):
            destinations(replace(self.config, dependencies=(dep,)))

    def test_native_revision_substitution_rejected(self):
        path = self.root / 'dependency/native/api' / POINT_PAGE
        before = path.read_bytes()
        path.write_bytes(before + b'<!-- substituted native revision -->')
        self.assertNotEqual(before, path.read_bytes())
        with self.assertRaisesRegex(ValueError, 'native artifact changed'):
            destinations(self.config)

    def test_dependency_source_substitution_rejected(self):
        path = self.root / 'dependency/source/src/opencv.ads'
        before = path.read_text()
        self.assertIn('type Point_Array is array', before)
        path.write_text(before.replace('type Point_Array is array', 'type Other_Array is array'))
        self.assertNotEqual(before, path.read_text())
        with self.assertRaisesRegex(ValueError, 'pinned source mismatch'):
            destinations(self.config)

    def test_changed_consumer_type_identity_invalidates_publication(self):
        enhance(self.config, self.site)
        path = self.root / 'consumer/src/opencv-geometry.ads'
        before = path.read_text()
        self.assertEqual(before.count('subtype Contour is OpenCV.Point_Array;'), 1)
        path.write_text(before.replace('subtype Contour is OpenCV.Point_Array;',
                                       'subtype Contour is OpenCV.Rect;'))
        self.assertNotEqual(before, path.read_text())
        with self.assertRaisesRegex(ValueError, 'source differs'):
            verify(self.config, self.site)

    def test_forged_output_manifest_cannot_authorize_wrong_valid_link(self):
        enhance(self.config, self.site)
        page, _ = self.contour()
        wrong = destinations(self.config)['opencv.rect']
        before = page.read_text()
        self.assertEqual(before.count(POINT_URL), 1)
        page.write_text(before.replace(POINT_URL, wrong))
        self.assertNotEqual(before, page.read_text())
        manifest_path = self.site / 'api/presentation.json'
        data = json.loads(manifest_path.read_text())
        data['output_sha256'][page.relative_to(self.site).as_posix()] = digest(page.read_bytes())
        manifest_path.write_text(sorted_json(data))
        with self.assertRaisesRegex(ValueError, 'does not match source/manifest'):
            verify(self.config, self.site)


if __name__ == '__main__':
    unittest.main()