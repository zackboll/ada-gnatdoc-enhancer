"""Separate native/instance/summary authority, positive and negative contexts."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.generic_instances import ANCHOR
from ada_gnatdoc_enhancer.instance_references import targets, resolve, metadata
from ada_gnatdoc_enhancer.inventory import _one, packages
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.symbols import public_symbols
from ada_gnatdoc_enhancer.syntax import type_positions
from ada_gnatdoc_enhancer.theme import asset

FIXTURE = Path(__file__).parent/'real-fixtures/generic-core'


class InstanceReferences(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)/'root'; shutil.copytree(FIXTURE,self.root)
        self.config = replace(load(self.root,'enhancer.toml'),instance_references=True,
                              symbol_bookmarks=True,default_package='OpenCV.Core')
        self.source = packages(self.config); self.native = snapshot(self.config,self.root/'pristine')
        self.targets = targets(self.config,self.source,self.native)

    def resolving(self, signature='function Get (Image : Mat) return UInt8_Vec2.Vector;',
                  context='with OpenCV.Core.UInt8_Vec2;', body_prefix='', body_suffix=''):
        code = context+'\npackage OpenCV.Core.Accessor is\n'+body_prefix+'\n'+signature+'\n'+body_suffix+'\nend OpenCV.Core.Accessor;'
        p = self.root/'accessor.ads';p.write_text(code);pkg = _one(p)
        source = dict(self.source);source[pkg.name.lower()] = pkg
        marks = type_positions(signature)
        return [resolve(name,signature,a,b,pkg,source,self.targets) for a,b,name in marks
                if name.lower().endswith(('.vector','.matrix','.component_index'))]

    def test_inventory_is_separate(self):
        self.assertEqual(len(self.targets),5)
        native = verified_types(self.native,self.source)
        symbols = dict(public_symbols(self.config,self.native))
        for identity,target in self.targets.items():
            self.assertNotIn(identity,native)
            self.assertNotIn(identity,set(n.lower() for n in symbols))
            self.assertEqual(target.href,target.page+'#'+ANCHOR)
            self.assertNotIn('<h4',target.summary)

    def test_disabled_inventory_and_metadata(self):
        self.assertEqual(targets(replace(self.config,instance_references=False),self.source,self.native),{})
        self.assertEqual(metadata({}),'')

    def test_short_exact_import(self):
        result, = self.resolving();self.assertEqual(result.identity,'opencv.core.uint8_vec2.vector')

    def test_full_exact_import(self):
        result, = self.resolving('function Get return OpenCV.Core.UInt8_Vec2.Vector;')
        self.assertEqual(result.identity,'opencv.core.uint8_vec2.vector')

    def test_array_component_after_range(self):
        result, = self.resolving('type Buffer is array (Natural range <>) of UInt8_Vec2.Vector;')
        self.assertEqual(result.identity,'opencv.core.uint8_vec2.vector')

    def test_matrix_argument(self):
        result, = self.resolving('function Copy (Value : OpenCV.Core.Float32_Matx3x3.Matrix) return Mat;',
                                'with OpenCV.Core.Float32_Matx3x3;')
        self.assertEqual(result.identity,'opencv.core.float32_matx3x3.matrix')

    def test_missing_import(self):self.assertEqual(self.resolving(context=''),[None])
    def test_private_import(self):self.assertEqual(self.resolving(context='private with OpenCV.Core.UInt8_Vec2;'),[None])
    def test_limited_import(self):self.assertEqual(self.resolving(context='limited with OpenCV.Core.UInt8_Vec2;'),[None])
    def test_wrong_owner_import(self):self.assertEqual(self.resolving(context='with Other.UInt8_Vec2;'),[None])
    def test_alias(self):self.assertEqual(self.resolving(body_prefix='package Alias renames OpenCV.Core.UInt8_Vec2;'),[None])
    def test_local_object(self):self.assertEqual(self.resolving(body_prefix='UInt8_Vec2 : Integer;'),[None])
    def test_comma_object(self):self.assertEqual(self.resolving(body_prefix='Other, UInt8_Vec2 : Integer;'),[None])
    def test_parameter_shadow(self):self.assertEqual(self.resolving('function Get (UInt8_Vec2 : Integer) return UInt8_Vec2.Vector;'),[None])
    def test_nested_scope(self):self.assertEqual(self.resolving(body_prefix='package Nested is end Nested;'),[None])
    def test_private_declaration(self):self.assertEqual(self.resolving(body_prefix='private'),[None])
    def test_generic_formal(self):self.assertEqual(self.resolving(context='generic type T is private;'),[None])
    def test_unapproved_member(self):self.assertEqual(self.resolving('function Get return UInt8_Vec2.Component_Index;'),[None])

    def test_default_and_comment_not_eligible(self):
        for signature in ['function Get (X : Integer := (for all I : UInt8_Vec2.Vector => True)) return Integer;',
                          'function Get return Integer; -- return UInt8_Vec2.Vector',
                          'function Get (S : String := "return UInt8_Vec2.Vector") return Integer;']:
            with self.subTest(signature=signature):self.assertFalse(any(self.resolving(signature)))

    def test_wrong_qualification_hash_and_atomic_failure(self):
        site = self.root/'site';shutil.copytree(self.root/'pristine',site);before = hashes(site)
        setting = dict(self.config.generic_instances,sha256='0'*64)
        with self.assertRaises(ValueError):enhance(replace(self.config,generic_instances=setting),site)
        self.assertEqual(before,hashes(site))

    def test_source_actual_mutation_observed(self):
        p = self.source['opencv.core.uint8_vec2'].path;old = p.read_text()
        changed = old.replace('Length => 2','Length => 3');self.assertNotEqual(changed,old);p.write_text(changed)
        with self.assertRaises(ValueError):targets(self.config,packages(self.config),self.native)

    def test_missing_summary_proof(self):
        with self.assertRaises(ValueError):targets(self.config,self.source,self.native,{})

    def test_new_router_only_when_enabled(self):
        site = self.root/'site';shutil.copytree(self.root/'pristine',site)
        enhance(self.config,site);verify(self.config,site);before = hashes(site)
        self.assertIn('instance-reference-navigation',(site/'api/index.html').read_text())
        self.assertEqual((site/'api/gnatdoc-navigation.js').read_bytes(),
                         asset('gnatdoc-instance-navigation.js'))
        enhance(self.config,site);self.assertEqual(before,hashes(site))


class InstanceReferenceConfiguration(unittest.TestCase):
    def test_strict_opt_in(self):
        tmp = tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)/'root';shutil.copytree(FIXTURE,root);p = root/'enhancer.toml';old = p.read_text()
        for value in ['true','"true"','1']:
            p.write_text(old+'\nincoming_references = '+value+'\n')
            with self.subTest(value=value),self.assertRaises(ValueError):load(root,'enhancer.toml')
        p.write_text(old+'\nincoming_references = false\n');self.assertFalse(load(root,'enhancer.toml').instance_references)
        p.write_text(old+'\nincoming_references = true\n[navigation]\nmode = "packages"\nsymbol_bookmarks = true\ndefault_package = "OpenCV.Core"\n')
        self.assertTrue(load(root,'enhancer.toml').instance_references)