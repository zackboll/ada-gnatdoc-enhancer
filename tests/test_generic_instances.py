"""Authentic pinned Core source/native regression, not synthetic expansion."""
from __future__ import annotations

import copy
import html
import json
import re
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.generic_instances import (
    ANCHOR, CLASS, ELEMENTS, MEMBERS, ancestor_visibility, discover, native_instance,
    qualification, render, summaries,
)
from ada_gnatdoc_enhancer.inventory import _one, packages
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.pipeline import MANIFEST, enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native
from ada_gnatdoc_enhancer.util import digest, sorted_json
from ada_gnatdoc_enhancer.validation import Page

FIXTURE = Path(__file__).resolve().parent/'real-fixtures/generic-core'
UINT = 'opencv.core.uint8_vec2'
FLOAT16 = 'opencv.core.float16_vec3'
MATRIX = 'opencv.core.float32_matx3x3'


class GenericInstances(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = tempfile.TemporaryDirectory()
        cls.base = Path(cls.prepared.name)
        shutil.copytree(FIXTURE, cls.base/'root')
        shutil.copytree(FIXTURE/'pristine', cls.base/'site')
        cls.result = enhance(load(cls.base/'root', 'enhancer.toml'), cls.base/'site')

    @classmethod
    def tearDownClass(cls):
        cls.prepared.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'root'
        shutil.copytree(self.base/'root', self.root)
        self.site = Path(self.temp.name)/'site'
        shutil.copytree(self.base/'site', self.site)
        self.config = load(self.root, 'enhancer.toml')
        self.source = packages(self.config)
        self.native = snapshot(self.config, self.root/'pristine')
        self.record = json.loads((self.root/'qualification.json').read_text())
        self.expected = self.record['instances']

    def changed_source(self, key, before, after):
        p = self.source[key]
        self.assertIn(before, p.source)
        p.path.write_text(p.source.replace(before, after, 1))
        self.source[key] = _one(p.path)

    def rejected_instantiation(self, before, after):
        self.changed_source(UINT, before, after)
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def output_path(self, key=UINT):
        return self.site/'api'/self.native.pages[key].path.name

    def rejected_output(self, mutation, key=UINT):
        path = self.output_path(key); text = path.read_text()
        changed = mutation(text)
        self.assertNotEqual(text, changed)
        path.write_text(changed)
        with self.assertRaises(ValueError): verify(self.config, self.site)

    def test_provenance_hashes_and_pin(self):
        provenance = json.loads((self.root/'provenance.json').read_text())
        self.assertEqual(provenance['revision'], 'c5545eee815431568495c6c76af83df56cf5c3dd')
        for name, item in provenance['files'].items():
            self.assertEqual(digest((self.root/name).read_bytes()), item['sha256'], name)
        self.assertEqual(hashes(self.root/'pristine'), self.record['native_sha256'])

    def test_all_five_authentic_families(self):
        found, unsupported = discover(self.source, self.expected)
        self.assertEqual(found, self.expected); self.assertEqual(unsupported, [])
        self.assertEqual({v['element_type'] for v in found.values()},
                         {'UInt8_Value','Float16_Value','Float32_Value','Float64_Value'})
        self.assertEqual(self.result['qualified_generic_instances'], 5)
        self.assertEqual(self.result['generic_summary_links'], 22)
        self.assertEqual(self.result['native_instance_member_declarations'], 0)

    def test_separate_type_accounting(self):
        disabled = replace(self.config, generic_instances={})
        raw = Path(self.temp.name)/'disabled'; shutil.copytree(self.root/'pristine', raw)
        counts = enhance(disabled, raw)
        self.assertEqual(counts['linked_local_types'], self.result['linked_local_types'])
        self.assertNotIn('qualified_generic_instances', counts)
        self.assertFalse(any(CLASS in p.read_text() for p in (raw/'api').glob('*.html')))

    def test_authentic_introductions_and_no_native_members(self):
        for key in self.expected:
            page = self.native.pages[key]
            self.assertEqual(page.original, native_instance(self.source[key]))
            self.assertEqual(page.sections, [])
            self.assertEqual(Page(page.original).ids, [])
            self.assertEqual(self.output_path(key).read_text().count(CLASS), 1)
            self.assertNotIn('<h4', self.output_path(key).read_text())

    def test_meanings_and_actual_ownership(self):
        half = self.output_path(FLOAT16).read_text()
        self.assertIn('OpenCV.Core.Float16_Value', half)
        self.assertIn('binary16 encodings', half); self.assertIn('numerical interpretation', half)
        self.assertIn('Natural range 0 .. 2', half)
        matrix = self.output_path(MATRIX).read_text()
        self.assertIn('3 × 3 array of Float32_Value', html.unescape(matrix))
        self.assertIn('3 &#215; 3 array', matrix)
        self.assertIn('Float32_Matx3x3_Conversions', matrix)
        self.assertIn('does not imply shared native storage', matrix)

    def test_independent_reconstruction_and_native_preservation(self):
        verify(self.config, self.site)
        before = identities(self.root/'pristine')
        result = preserve_native(before, self.site, config=self.config, pristine=self.root/'pristine')
        self.assertEqual(result['status'], 'preserved')
        with self.assertRaises(ValueError): preserve_native(before, self.site)

    def test_byte_idempotence(self):
        before = hashes(self.site); enhance(self.config, self.site)
        self.assertEqual(hashes(self.site), before)

    def test_two_copy_determinism(self):
        second = Path(self.temp.name)/'second'; shutil.copytree(self.root/'pristine', second)
        enhance(self.config, second)
        self.assertEqual(hashes(second), hashes(self.site))

    def test_missing_expected_instance(self):
        del self.source[UINT]
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_additional_supported_instance(self):
        extra = copy.deepcopy(self.source[UINT]); extra.name = 'OpenCV.Core.Extra'
        extra.source = extra.source.replace('OpenCV.Core.UInt8_Vec2', extra.name)
        self.source[extra.name.lower()] = extra
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_unknown_template(self):
        self.rejected_instantiation('OpenCV.Core.Vectors (', 'OpenCV.Core.Unknown (')

    def test_named_association_order_is_not_semantic(self):
        self.changed_source(UINT, 'Element_Type => UInt8_Value, Length => 2',
                            'Length => 2, Element_Type => UInt8_Value')
        self.assertEqual(discover(self.source,self.expected)[0],self.expected)

    def test_missing_template_source(self):
        del self.source['opencv.core.vectors']
        with self.assertRaises(ValueError): discover(self.source,self.expected)

    def test_nested_instance_context(self):
        self.rejected_instantiation('package OpenCV.Core.UInt8_Vec2 is new',
                                    'package Wrapper is package OpenCV.Core.UInt8_Vec2 is new')

    def test_private_actual_owner(self):
        self.changed_source('opencv', 'subtype UInt8_Value is Interfaces.Unsigned_8;', '')
        with self.assertRaises(ValueError): discover(self.source,self.expected)

    def test_template_renaming(self):
        self.rejected_instantiation('OpenCV.Core.Vectors (Element_Type',
                                    'Alias (Element_Type')

    def test_disabled_type_links_still_require_genuine_summary_targets(self):
        config=replace(self.config,type_links=False)
        site=Path(self.temp.name)/'no-type-links';shutil.copytree(self.root/'pristine',site)
        counts=enhance(config,site)
        self.assertEqual(counts['linked_local_types'],0)
        self.assertEqual(counts['generic_summary_links'],22)
        verify(config,site)

    def test_config_requires_explicit_hash_and_rejects_unknown_keys(self):
        path=self.root/'enhancer.toml';original=path.read_text()
        for changed in (re.sub(r'sha256 = .*','',original), original+'enabled = true\n'):
            with self.subTest(config=changed):
                path.write_text(changed)
                with self.assertRaises(ValueError):load(self.root,'enhancer.toml')
        path.write_text(original)

    def test_missing_actual_anchor(self):
        targets=verified_types(self.native,self.source)
        del targets['opencv.uint8_value']
        with self.assertRaises(ValueError):render(self.expected[UINT],self.source,self.native,targets)

    def test_ambiguous_actual_owner_declaration(self):
        p=self.source['opencv'].path
        p.write_text(p.read_text().replace('package OpenCV is',
                                          'package OpenCV is\n subtype UInt8_Value is Natural;'))
        with self.assertRaises(ValueError):packages(self.config)

    def test_altered_generic_formal(self):
        self.changed_source('opencv.core.vectors', 'Length : Positive;', 'Length : Natural;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_altered_member_definition(self):
        self.changed_source('opencv.core.vectors', '0 .. Length - 1', '1 .. Length')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_template_extra_declaration(self):
        self.changed_source('opencv.core.vectors', 'end OpenCV.Core.Vectors;',
                            'subtype Other is Integer; end OpenCV.Core.Vectors;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_missing_formal(self):
        self.rejected_instantiation(', Length => 2', '')

    def test_unknown_formal(self):
        self.rejected_instantiation('Length => 2', 'Length => 2, Extra => 3')

    def test_duplicate_association(self):
        self.rejected_instantiation('Length => 2', 'Length => 2, Length => 2')

    def test_duplicate_element_association(self):
        self.rejected_instantiation('Length => 2', 'Length => 2, Element_Type => UInt8_Value')

    def test_positional_association(self):
        self.rejected_instantiation('Element_Type => UInt8_Value, Length => 2', 'UInt8_Value, 2')

    def test_unsupported_dimensions(self):
        for value in ('0','-2','N','Standard.Positive','2 + 0','2.0','16#2#','2_0','OpenCV.N'):
            with self.subTest(dimension=value):
                source = copy.deepcopy(self.source)
                self.source = source
                original = self.source[UINT].source
                self.rejected_instantiation('Length => 2', 'Length => '+value)
                self.source[UINT].path.write_text(original); self.source[UINT] = _one(self.source[UINT].path)

    def test_incorrect_positive_length(self):
        self.rejected_instantiation('Length => 2', 'Length => 3')

    def test_incorrect_matrix_dimensions(self):
        self.changed_source(MATRIX, 'Row_Count    => 3', 'Row_Count    => 4')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_changed_element(self):
        self.rejected_instantiation('UInt8_Value', 'Int8_Value')

    def test_qualified_actual_unsupported(self):
        self.rejected_instantiation('UInt8_Value', 'OpenCV.UInt8_Value')

    def test_changed_actual_declaration(self):
        self.changed_source('opencv', 'subtype UInt8_Value is Interfaces.Unsigned_8;',
                            'subtype UInt8_Value is Interfaces.Unsigned_16;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_private_shadowing(self):
        self.changed_source('opencv.core', 'end OpenCV.Core;',
                            'type UInt8_Value is range 0 .. 255; end OpenCV.Core;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_object_list_shadowing(self):
        self.changed_source('opencv.core', 'package OpenCV.Core is',
                            'package OpenCV.Core is\n Other, UInt8_Value : Natural;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_duplicate_generic_formal_declaration(self):
        self.changed_source('opencv.core.vectors', 'Length : Positive;', 'Length : Positive; Length : Positive;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_swapped_template_package_target(self):
        a = self.native.pages['opencv.core.vectors'].path.name
        b = self.native.pages['opencv.core.fixed_matrices'].path.name
        self.rejected_output(lambda t:t.replace('href="'+a+'"', 'href="'+b+'"'))

    def test_presentation_fragment_cannot_satisfy_template_member(self):
        p = self.native.pages['opencv.core.vectors']
        p.original = re.sub(r'<h4 id=[^>]+>Vector</h4>', '<section id="Vector">Vector</section>', p.original)
        p.sections = [s for s in p.sections if s.name != 'Vector']
        with self.assertRaises(ValueError): verified_types(self.native, self.source)

    def test_member_anchor_removed_from_pristine(self):
        p = self.root/'pristine/api'/self.native.pages['opencv.core.vectors'].path.name
        p.write_text(re.sub(r'<h4 id=[^>]+>Vector</h4>', '<h4>Vector</h4>', p.read_text()))
        with self.assertRaises(ValueError):snapshot(self.config,self.root/'pristine')

    def test_unexpected_summary_in_pristine(self):
        p = self.root/'pristine/api'/self.native.pages[UINT].path.name
        p.write_text(p.read_text()+'<section class="generic-instance-summary" id="'+ANCHOR+'">forged</section>')
        before = hashes(self.root/'pristine')
        with self.assertRaises(ValueError):enhance(self.config,self.root/'pristine')
        self.assertEqual(hashes(self.root/'pristine'),before)

    def test_public_shadowing(self):
        self.changed_source('opencv.core', 'package OpenCV.Core is',
                            'package OpenCV.Core is\n subtype UInt8_Value is Natural;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_nested_shadowing_and_renaming(self):
        self.changed_source('opencv.core', 'package OpenCV.Core is',
                            'package OpenCV.Core is\n package Alias renames OpenCV;')
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_missing_ancestor(self):
        del self.source['opencv.core']
        with self.assertRaises(ValueError): discover(self.source, self.expected)

    def test_context_and_trailing_consumption(self):
        for prefix, suffix in [('use OpenCV;\n',''),('private ','') ,('generic\n',''),
                               ('with Other;\n',''),('','\npackage Other is end Other;'),
                               ('','\npragma Pure;'),('','\n"ignored string"')]:
            with self.subTest(prefix=prefix,suffix=suffix):
                src = copy.deepcopy(self.source)
                src[UINT].source = prefix + src[UINT].source + suffix
                with self.assertRaises(ValueError): discover(src, self.expected)

    def test_missing_member_anchor(self):
        targets = verified_types(self.native, self.source)
        del targets['opencv.core.vectors.vector']
        with self.assertRaises(ValueError): render(self.expected[UINT], self.source, self.native, targets)

    def test_wrong_existing_native_anchor(self):
        self.rejected_output(lambda t:t.replace('#'+verified_types(self.native,self.source)['opencv.core.vectors.vector'][1],
                                                '#'+verified_types(self.native,self.source)['opencv.core.vectors.component_index'][1]))

    def test_swapped_member_destinations(self):
        targets = verified_types(self.native, self.source)
        a = '#'+targets['opencv.core.vectors.vector'][1]; b = '#'+targets['opencv.core.vectors.component_index'][1]
        self.rejected_output(lambda t:t.replace(a,'TEMP').replace(b,a).replace('TEMP',b))

    def test_missing_conversion_package(self):
        del self.native.pages['opencv.core.float32_matx3x3_conversions']
        with self.assertRaises(ValueError): render(self.expected[MATRIX], self.source, self.native,
                                                   verified_types(self.native,self.source))

    def test_changed_native_input_hash(self):
        self.native.pages[UINT].original += ' '
        with self.assertRaises(ValueError): qualification(self.config, self.source, self.native)

    def test_changed_source_after_enhancement(self):
        p = self.source[UINT].path; p.write_text(p.read_text()+'\n-- changed\n')
        with self.assertRaises(ValueError): verify(self.config, self.site)

    def test_changed_qualification_hash(self):
        p = self.root/'qualification.json'; p.write_text(p.read_text()+'\n')
        with self.assertRaises(ValueError): verify(self.config, self.site)

    def test_changed_source_hash(self):
        self.changed_source(UINT, 'Length => 2', 'Length => 3')
        with self.assertRaises(ValueError): qualification(self.config, self.source, self.native)

    def test_unexpected_native_member_section(self):
        self.rejected_output(lambda t:t+'<h4 id="Vector">Vector</h4>')

    def test_modified_native_introduction(self):
        self.rejected_output(lambda t:t.replace('CV_8UC2','CV_8UC3'))

    def test_missing_summary(self):
        self.rejected_output(lambda t:re.sub(r'<section class="generic-instance-summary".*?</section>', '',t,flags=re.S))

    def test_duplicate_summary(self):
        self.rejected_output(lambda t:t+re.search(r'<section class="generic-instance-summary".*?</section>',t,re.S)[0])

    def test_modified_summary_argument(self):
        self.rejected_output(lambda t:t.replace('<td>2</td>','<td>3</td>'))

    def test_missing_member_link(self):
        self.rejected_output(lambda t:re.sub(r'<a href="[^\"]+">Vector</a>', 'Vector', t))

    def test_presentation_anchor_cannot_be_native_declaration(self):
        self.rejected_output(lambda t:t.replace('id="'+ANCHOR+'"','id="Vector"'))
        self.assertNotIn(UINT+'.vector', verified_types(self.native,self.source))

    def test_output_manifest_cannot_authorize_tampered_summary(self):
        path = self.output_path(); path.write_text(path.read_text().replace('<td>2</td>','<td>9</td>'))
        m = self.site/MANIFEST; data = json.loads(m.read_text())
        data['output_sha256']['api/'+path.name] = digest(path.read_bytes()); m.write_text(sorted_json(data))
        with self.assertRaises(ValueError): verify(self.config,self.site)

    def test_output_manifest_cannot_redefine_native_input(self):
        m = self.site/MANIFEST; data = json.loads(m.read_text())
        path = 'api/'+self.native.pages[UINT].path.name
        data['original_api_html'][path] = data['original_api_html'][path].replace('CV_8UC2','CV_8UC3')
        m.write_text(sorted_json(data))
        with self.assertRaises(ValueError): verify(self.config,self.site)

    def test_unexpected_resources(self):
        for name in ('extra.html','evil.js','extra.css'):
            with self.subTest(name=name):
                path = self.site/'api'/name; path.write_text('unexpected')
                try:
                    with self.assertRaises(ValueError): verify(self.config,self.site)
                finally:path.unlink()

    def test_broken_and_malformed_fragments(self):
        for fragment in ('missing','%ZZ','instance-members-summary'):
            with self.subTest(fragment=fragment):
                original = self.output_path().read_text()
                try:
                    self.rejected_output(lambda t:re.sub(r'#[a-f0-9]{64}', '#'+fragment,t,count=1))
                finally:self.output_path().write_text(original)

    def test_script_injection(self):
        self.rejected_output(lambda t:t+'<script>alert(1)</script>')

    def test_symlinked_output(self):
        p = self.output_path(); original = Path(self.temp.name)/'original';p.rename(original);p.symlink_to(original)
        with self.assertRaises(ValueError):verify(self.config,self.site)

    def test_native_preservation_rejects_modified_summary(self):
        p = self.output_path();p.write_text(p.read_text().replace('<td>2</td>','<td>5</td>'))
        with self.assertRaises(ValueError):preserve_native(identities(self.root/'pristine'),self.site,
                                                         config=self.config,pristine=self.root/'pristine')

    def test_failed_enhancement_is_atomic(self):
        site = Path(self.temp.name)/'raw';shutil.copytree(self.root/'pristine',site)
        p = site/'api'/self.native.pages[UINT].path.name;p.write_text(p.read_text()+'tamper')
        before = hashes(site)
        with self.assertRaises(ValueError):enhance(self.config,site)
        self.assertEqual(hashes(site),before)


if __name__ == '__main__': unittest.main()