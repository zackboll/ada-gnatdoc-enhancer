"""Authentic excerpts are immutable evidence; mutations below are synthetic."""
from __future__ import annotations

import html
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.native_html import SECTION, snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.profiles import reconcile, tokens
from ada_gnatdoc_enhancer.qualification import check_snapshot
from ada_gnatdoc_enhancer.util import digest

ROOT=Path(__file__).resolve().parent
ITEMS={x['name']:x for x in json.loads((ROOT/'real-fixtures/excerpts.json').read_text())}


def native(item):
    return html.unescape(SECTION.fullmatch(item['native_excerpt'])[4])


class ExpressionProfiles(unittest.TestCase):
    def setUp(self):
        self.item=ITEMS['Make_Scalar']
        self.source=self.item['source_signature'];self.native=native(self.item)

    def test_authentic_make_scalar(self):
        self.assertEqual(reconcile(self.source,self.native).rule,'expression-function-profile')

    def test_altered_parameter_type(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('Long_Float','Float',1)))

    def test_altered_default(self):
        self.assertIsNone(reconcile(self.source,self.native.replace(':= 0.0',':= 1.0',1)))

    def test_altered_return_type(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('return Scalar','return Float')))

    def test_altered_parameter_name(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('Component_0','Other')))

    def test_altered_parameter_mode(self):
        self.assertIsNone(reconcile(self.source,self.native.replace(': Long_Float',': in Long_Float',1)))

    def test_swapped_overload(self):
        other=self.source.replace('Long_Float','Float')
        self.assertIsNone(reconcile(other,self.native))

    def test_nested_body(self):
        source='function F (X : Integer := G (1, (2))) return P.T is (G ((X + 1), H (X)));'
        rendered='function F (X : Integer := G (1, (2))) return P.T'
        self.assertIsNotNone(reconcile(source,rendered))

    def test_comments_strings_characters(self):
        profile='function F (S : String := "is (; -- ""quoted"""; C : Character := \';\') return String'
        source=profile+' -- is (;\n is (G ("is ); --", \')\', \'(\')); -- ; is'
        self.assertIsNotNone(reconcile(source,profile))
        self.assertIsNone(reconcile(source,profile.replace('is (;','is (x;')))

    def test_string_with_pre_is_not_aspect(self):
        self.assertIsNone(reconcile('function F (S : String := " with Pre bad") return String;',
                                    'function F (S : String := "'))

    def test_unsupported_bodies(self):
        for tail in ('is X;', 'is (X) with Pre => True;', 'is (declare X : Integer := 1; begin X);',
                     'is ();', 'is (X; Y);', 'is ((X);', 'is ("unterminated);', 'is (…);'):
            with self.subTest(tail=tail):
                self.assertIsNone(reconcile('function F return Integer '+tail,'function F return Integer'))

    def test_unsupported_profile(self):
        self.assertIsNone(reconcile('function F (X : access Integer) return Integer is (X.all);',
                                    'function F (X : access Integer) return Integer'))

    def test_qualified_types_modes_and_multiple_names(self):
        profile='not overriding function F (X, Y : in P.T; Z : in out Q.T) return R.T'
        self.assertIsNotNone(reconcile(profile+' is (G (X, Y, Z));',profile))

    def test_body_semicolon_cannot_hide_trailing_declaration(self):
        self.assertIsNone(reconcile('function F return Integer is (1); procedure P;',
                                    'function F return Integer'))

    def test_first_is_not_used(self):
        source='function F (S : String := "is") return String is (S);'
        self.assertIsNone(reconcile(source,'function F (S : String := "is")'))

    def test_unbalanced_lexical_input(self):
        for text in ('(',')','"bad'):
            with self.assertRaises(ValueError):tokens(text)


class EnumerationProfiles(unittest.TestCase):
    def setUp(self):
        self.item=ITEMS['Color_Conversion'];self.source=self.item['source_signature']
        self.native=native(self.item)

    def test_authentic_color_conversion(self):
        result=reconcile(self.source,self.native)
        self.assertEqual(result.rule,'enumeration-first-eight-last')
        self.assertEqual(result.hidden_literals,77)

    def test_authentic_cannot_comply(self):
        item=ITEMS['Cannot_Comply']
        self.assertEqual(reconcile(item['source_signature'],native(item)).hidden_literals,38)

    def test_altered_first(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('BGR_To_Gray','Other',1)))

    def test_altered_last(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('Premultiplied_RGBA_To_RGBA','Other')))

    def test_reordered_visible(self):
        text=self.native.replace('BGR_To_Gray','TEMP').replace('RGB_To_Gray','BGR_To_Gray').replace('TEMP','RGB_To_Gray')
        self.assertIsNone(reconcile(self.source,text))

    def test_malformed_ellipsis(self):
        for replacement in ('...','..','……','… omitted',''):
            with self.subTest(replacement=replacement):
                self.assertIsNone(reconcile(self.source,self.native.replace('…',replacement)))

    def test_wrong_prefix_length(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('   Gray_To_RGBA,\n','')))

    def test_wrong_identity(self):
        self.assertIsNone(reconcile(self.source,self.native.replace('Color_Conversion','Other')))

    def test_small_enum_not_abbreviated(self):
        self.assertIsNone(reconcile('type T is (A,B,C,D,E,F,G,H,I,J);',
                                    'type T is (A,B,C,D,E,F,G,H,…,J);'))

    def test_malformed_source(self):
        for source in ('type T is (A,,B);','type T is (A,A);','type T is (A, …, B);',
                       'type T is (A_,B,C,D,E,F,G,H,I,J,K);',
                       'type T is (A__B,B,C,D,E,F,G,H,I,J,K);'):
            self.assertIsNone(reconcile(source,'type T is (A,B,…,Z);'))

    def test_truncated_non_enum(self):
        self.assertIsNone(reconcile('procedure P (A : Integer; B : Float);','procedure P (A : Integer; …)'))

    def test_character_enumeration(self):
        source="type T is ('A','B','C','D','E','F','G','H','I','J','K');"
        rendered="type T is ('A','B','C','D','E','F','G','H',…,'K');"
        self.assertEqual(reconcile(source,rendered).hidden_literals,2)

    def test_duplicate_hidden_literal_rejected(self):
        self.assertIsNone(reconcile(self.source.replace('BGR_To_BGRA','BGR_To_Gray'),self.native))

    def test_unrelated_record_aspect_still_rejected(self):
        item=ITEMS['Complex_I8']
        self.assertIsNone(reconcile(item['source_signature'].replace('Convention => C','Pack'),native(item)))

    def test_exact_aspect_omission_is_top_level_only(self):
        self.assertIsNotNone(reconcile('function F (S : String := " with Pre text") return Integer with Pre => True;',
                                       'function F (S : String := " with Pre text") return Integer'))
        self.assertIsNone(reconcile('function F (X : Integer := G (with Pre => True)) return Integer;',
                                    'function F (X : Integer := G ('))


class NativeProfileIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gnatdoc003-profile-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def test_authentic_source_excerpt_provenance(self):
        record=json.loads((ROOT.parent/'docs/evidence/gnatdoc003/provenance.json').read_text())
        for item in record['authentic_excerpts']:
            self.assertEqual(digest(item['source_signature'].encode()),item['source_excerpt_sha256'])
            self.assertEqual(digest(item['native_excerpt'].encode()),item['native_excerpt_sha256'])
            self.assertEqual(item['source_signature'],ITEMS[item['name']]['source_signature'])

    def stage(self,item):
        # Reduced test harness, NOT an acquired full native site. Only the
        # declaration excerpt and its observed filename/anchor are authentic.
        (self.root/'src').mkdir();(self.root/'site/api').mkdir(parents=True)
        self.source=self.root/'src/unit.ads'
        self.source.write_text('package '+item['package']+' is\n'+item['source_signature']+'\nend '+item['package']+';\n')
        self.page=self.root/'site'/item['native_path']
        # GNATdoc 26.0.0 document prologue; enhancement requires this exact layout.
        prologue='<!DOCTYPE html>\n<html class=main>\n<link rel=stylesheet href=gnatdoc.css>'
        self.page.write_text(prologue+'<body class=content><h1>'+item['package']+'</h1>'+item['native_excerpt']+'</body></html>')
        (self.root/'site/api/index.html').write_text(prologue+'<body class=main><a href='+self.page.name+' target=document-content>'+item['package']+'</a><iframe name=document-content></iframe></body></html>')
        shutil.copyfile(ROOT/'fixtures/core/_site/api/gnatdoc.css',self.root/'site/api/gnatdoc.css')
        (self.root/'project.toml').write_text('schema_version = 1\nproject = "profiles"\n[gnatdoc]\nversion = "26.0.0"\n[sources]\ndirectories = ["src"]\n[navigation]\nmode = "none"\n')
        self.config=load(self.root,'project.toml');self.site=self.root/'site'
        return snapshot(self.config,self.site)

    def test_expression_native_ambiguity(self):
        self.stage(ITEMS['Make_Scalar'])
        text=self.page.read_text();excerpt=ITEMS['Make_Scalar']['native_excerpt']
        self.page.write_text(text.replace('</body>',excerpt.replace('d3250a','d3250b')+'</body>'))
        with self.assertRaisesRegex(ValueError,'ambiguous'):snapshot(self.config,self.site)

    def test_inventory_nested_body_with_quoted_delimiters(self):
        item=dict(ITEMS['Make_Scalar'])
        item['source_signature']=item['source_signature'].split('   is (')[0]+'''   is (G ((Component_0), "is ); --", ';'));
-- is ( ;
'''
        result=self.stage(item)
        self.assertEqual(len(result.profile_matches),1)

    def test_swapped_overload_native_rejected(self):
        self.stage(ITEMS['Make_Scalar'])
        self.page.write_text(self.page.read_text().replace('Long_Float','Float'))
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_enum_duplicate_anchor(self):
        self.stage(ITEMS['Color_Conversion'])
        self.page.write_text(self.page.read_text().replace('</body>',ITEMS['Color_Conversion']['native_excerpt']+'</body>'))
        with self.assertRaisesRegex(ValueError,'duplicate native'):snapshot(self.config,self.site)

    def test_enum_ambiguous_native(self):
        self.stage(ITEMS['Color_Conversion'])
        excerpt=ITEMS['Color_Conversion']['native_excerpt'].replace('78e3e0','78e3e1')
        self.page.write_text(self.page.read_text().replace('</body>',excerpt+'</body>'))
        with self.assertRaisesRegex(ValueError,'ambiguous'):snapshot(self.config,self.site)

    def test_ambiguous_source_profile(self):
        self.stage(ITEMS['Make_Scalar'])
        self.source.write_text(self.source.read_text().replace('\nend ', '\n'+ITEMS['Make_Scalar']['source_signature']+'\nend '))
        with self.assertRaisesRegex(ValueError,'share native anchor'):snapshot(self.config,self.site)

    def test_missing_anchor_never_fabricated(self):
        self.stage(ITEMS['Color_Conversion']);self.page.write_text('<h1>OpenCV.Image_Processing</h1>')
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_native_and_source_immutable(self):
        result=self.stage(ITEMS['Color_Conversion'])
        before=self.page.read_bytes();owned=self.source.read_bytes()
        self.assertEqual(len(result.profile_matches),1)
        self.assertEqual(self.page.read_bytes(),before);self.assertEqual(self.source.read_bytes(),owned)

    def test_no_fabricated_links_and_rendered_text_preserved(self):
        self.stage(ITEMS['Color_Conversion'])
        from ada_gnatdoc_enhancer.qualification import identities, preserve_native
        before=identities(self.site)
        result=enhance(self.config,self.site)
        self.assertEqual(result['linked_types'],0)
        self.assertEqual(preserve_native(before,self.site)['status'],'preserved')
        self.assertEqual(verify(self.config,self.site)['mode'],'verified')

    def test_expression_body_source_mutation_rejected(self):
        self.stage(ITEMS['Make_Scalar']);enhance(self.config,self.site)
        self.source.write_text(self.source.read_text().replace('Component_0 => Component_0','Component_0 => 1.0'))
        with self.assertRaisesRegex(ValueError,'source'):verify(self.config,self.site)

    def test_hidden_source_mutation_rejected_by_pin(self):
        self.stage(ITEMS['Color_Conversion'])
        pin={'src/unit.ads':digest(self.source.read_bytes())}
        self.source.write_text(self.source.read_text().replace('BGR_To_BGRA','Hidden_Changed'))
        # Visible projection alone cannot prove hidden text. The independent
        # acquisition pin MUST reject it even though rendered text still matches.
        snapshot(self.config,self.site)
        with self.assertRaisesRegex(ValueError,'pinned source mismatch'):check_snapshot(self.root,pin)

    def test_hidden_mutation_rejected_after_enhancement(self):
        self.stage(ITEMS['Color_Conversion']);enhance(self.config,self.site)
        self.source.write_text(self.source.read_text().replace('BGR_To_BGRA','Hidden_Changed'))
        with self.assertRaisesRegex(ValueError,'source'):verify(self.config,self.site)