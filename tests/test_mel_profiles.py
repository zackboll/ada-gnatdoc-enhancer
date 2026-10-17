"""GNATDOC-004: pinned MEL excerpts, explicitly synthetic wrappers/mutations."""
from __future__ import annotations

import html
import json
import tempfile
import unittest
from pathlib import Path

import test_declaration_profiles as harness
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import SECTION, snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.profiles import reconcile, tokens
from ada_gnatdoc_enhancer.qualification import check_snapshot, identities, preserve_native
from ada_gnatdoc_enhancer.util import digest

ROOT=Path(__file__).resolve().parent
ITEMS={x['name']:x for x in json.loads((ROOT/'real-fixtures/mel-excerpts.json').read_text())}


def native(item):
    return html.unescape(SECTION.fullmatch(item['native_excerpt'])[4])


class RenamingProfiles(unittest.TestCase):
    def setUp(self):
        self.source=ITEMS['Add_Job_Intervals']['source_signature']
        self.rendered=native(ITEMS['Add_Job_Intervals'])
        self.target=ITEMS['Add_RX_Job_Intervals']['source_signature']

    def match(self,source=None,rendered=None,targets=None):
        return reconcile(self.source if source is None else source,
                         self.rendered if rendered is None else rendered,
                         (self.target,) if targets is None else targets)

    def test_authentic_renaming(self):
        result=self.match()
        self.assertEqual(result.rule,'subprogram-renaming-profile')
        self.assertEqual(result.target_name,'add_rx_job_intervals')
        self.assertEqual(result.omitted_source_tokens,('renames','add_rx_job_intervals',';'))

    def test_type_changed(self):
        self.assertIsNone(self.match(rendered=self.rendered.replace('RX_Job_Interval_List','Integer')))

    def test_mode_changed(self):
        self.assertIsNone(self.match(rendered=self.rendered.replace('in out','in')))

    def test_name_changed(self):
        self.assertIsNone(self.match(rendered=self.rendered.replace('Intervals :','Other :')))

    def test_default_changed(self):
        self.assertIsNone(reconcile('procedure P (X : Integer := 1) renames Q;',
                                    'procedure P (X : Integer := 2)',('procedure Q (X : Integer := 1);',)))

    def test_return_changed(self):
        self.assertIsNone(reconcile('function P return Integer renames Q;',
                                    'function P return Float',('function Q return Integer;',)))

    def test_function_with_defaults_and_quoted_delimiters(self):
        profile='function P (S : String := "renames Q; --"; X : Integer := F ((1))) return A.T'
        target=profile.replace('function P','function Q')+';'
        self.assertEqual(reconcile(profile+' renames Q;',profile,(target,)).rule,'subprogram-renaming-profile')

    def test_missing_target(self):
        self.assertIsNone(self.match(targets=()))

    def test_ambiguous_target(self):
        self.assertIsNone(self.match(targets=(self.target,self.target)))

    def test_distinguishable_target_overload_still_unsupported(self):
        self.assertIsNone(self.match(targets=(self.target,self.target.replace('in out','in'))))

    def test_incompatible_target(self):
        self.assertIsNone(self.match(targets=(self.target.replace('in out','in'),)))

    def test_target_default_changed(self):
        self.assertIsNone(reconcile('procedure P (X : Integer := 1) renames Q;',
                                    'procedure P (X : Integer := 1)',('procedure Q (X : Integer := 2);',)))

    def test_target_return_changed(self):
        self.assertIsNone(reconcile('function P return Integer renames Q;',
                                    'function P return Integer',('function Q return Float;',)))

    def test_cycles(self):
        self.assertIsNone(self.match(targets=(self.target.rstrip().removesuffix(';')+' renames Add_Job_Intervals;',)))

    def test_self_cycle(self):
        self.assertIsNone(self.match(source=self.source.replace('renames Add_RX_Job_Intervals','renames Add_Job_Intervals')))

    def test_chain_unsupported(self):
        self.assertIsNone(self.match(targets=(self.target.rstrip().removesuffix(';')+' renames Other;',)))

    def test_cross_package_unsupported(self):
        self.assertIsNone(self.match(source=self.source.replace('renames Add_RX','renames Other.Add_RX')))

    def test_malformed_clause(self):
        for tail in ('renames ;','renames Q X;','renames Q','renames Q ();','renames Q with Pre => True;',
                     'renames Q; procedure Other;','renames "Q";','renames Q\'Access;'):
            with self.subTest(tail=tail):
                self.assertIsNone(reconcile('procedure P '+tail,'procedure P',('procedure Q;',)))

    def test_comment_not_clause(self):
        source=self.source.replace('renames Add_RX_Job_Intervals;','-- renames Add_RX_Job_Intervals;\n;')
        self.assertEqual(self.match(source=source).rule,'exact')
        self.assertIsNone(self.match(source=source,rendered='procedure Add_Job_Intervals'))

    def test_string_not_clause(self):
        self.assertIsNone(reconcile('procedure P (S : String := "renames Q;");','procedure P',('procedure Q;',)))

    def test_unrelated_same_name_native(self):
        self.assertIsNone(self.match(rendered='procedure Add_Job_Intervals (Object : Integer)'))


class RecordProfiles(unittest.TestCase):
    def setUp(self):
        self.source=ITEMS['Complex_I16']['source_signature']
        self.rendered=native(ITEMS['Complex_I16'])

    def test_authentic_i16(self):
        result=reconcile(self.source,self.rendered)
        self.assertEqual(result.rule,'record-convention-aspect')
        self.assertEqual(result.omitted_source_tokens,('with','convention','=>','c'))

    def test_authentic_i8(self):
        item=ITEMS['Complex_I8']
        self.assertEqual(reconcile(item['source_signature'],native(item)).rule,'record-convention-aspect')

    def test_intervening_comments_owned(self):
        self.assertIn('--  C-compatible',self.source)
        self.assertEqual(tokens(self.source)[-7:],('end','record','with','convention','=>','c',';'))

    def test_ada_convention_rejected(self):
        self.assertIsNone(reconcile(self.source.replace('Convention => C','Convention => Ada'),self.rendered))

    def test_changed_field_type(self):
        self.assertIsNone(reconcile(self.source,self.rendered.replace('Integer_16','Integer_8',1)))

    def test_changed_field_order(self):
        self.assertIsNone(reconcile(self.source,self.rendered.replace('Real :','Temp :').replace('Imag :','Real :').replace('Temp :','Imag :')))

    def test_missing_field(self):
        self.assertIsNone(reconcile(self.source,self.rendered.replace('   Imag : Interfaces.Integer_16;\n','')))

    def test_additional_field(self):
        self.assertIsNone(reconcile(self.source,self.rendered.replace('end record','   Other : Integer;\nend record')))

    def test_changed_constraints(self):
        source='type T is record X : String (1 .. 2); end record with Convention => C;'
        self.assertIsNone(reconcile(source,'type T is record X : String (1 .. 3); end record;'))

    def test_pack_unsupported(self):
        self.assertIsNone(reconcile(self.source.replace('Convention => C','Pack'),self.rendered))

    def test_multiple_aspects_unsupported(self):
        self.assertIsNone(reconcile(self.source.replace('Convention => C','Convention => C, Pack'),self.rendered))

    def test_missing_end_record(self):
        self.assertIsNone(reconcile(self.source.replace('end record',''),self.rendered))

    def test_malformed_aspect(self):
        for tail in ('with Convention => ;','with Convention => C + 1;','with Convention C;',
                     'with Convention => "C";','with Convention => (C);'):
            with self.subTest(tail=tail):
                self.assertIsNone(reconcile(self.source.replace('with Convention => C;',tail),self.rendered))

    def test_trailing_declaration(self):
        self.assertIsNone(reconcile(self.source+'\ntype Other is new Integer;',self.rendered))

    def test_same_name_different_structure(self):
        self.assertIsNone(reconcile(self.source.replace('Imag :','Other :'),self.rendered))

    def test_comment_not_aspect(self):
        source=self.source.replace('with Convention => C;','-- with Convention => C;\n;')
        self.assertEqual(reconcile(source,self.rendered).rule,'exact')
        self.assertIsNone(reconcile(source,self.rendered.replace('Integer_16','Integer_8')))

    def test_string_not_aspect(self):
        self.assertIsNone(reconcile('type T is record S : String := "end record with Convention => C;"; end record;',
                                    'type T is record S : String; end record;'))

    def test_ambiguous_structure(self):
        for middle in ('X : Integer; end record; type Other is record Y : Integer;',
                       'X : Integer; X : Integer;', 'case K is when others => X : Integer; end case;'):
            self.assertIsNone(reconcile('type T is record '+middle+' end record with Convention => C;',
                                        'type T is record '+middle+' end record;'))


class MelIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gnatdoc004-profile-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)

    def stage(self,name='Add_Job_Intervals'):
        item=dict(ITEMS[name])
        if name=='Add_Job_Intervals':
            item['source_signature']=ITEMS['Add_RX_Job_Intervals']['source_signature']+'\n'+item['source_signature']
            item['native_excerpt']=ITEMS['Add_RX_Job_Intervals']['native_excerpt']+item['native_excerpt']
        return harness.NativeProfileIntegration.stage(self,item)

    def test_provenance(self):
        record=json.loads((ROOT.parent/'docs/evidence/gnatdoc004/provenance.json').read_text())
        self.assertEqual(record['authentic_excerpts'],list(ITEMS.values()))
        for item in ITEMS.values():
            self.assertEqual(digest(item['source_signature'].encode()),item['source_declaration_sha256'])
            self.assertEqual(digest(item['native_excerpt'].encode()),item['native_excerpt_sha256'])
            self.assertEqual(digest(native(item).encode()),item['native_signature_sha256'])

    def test_inventory_keeps_complete_record(self):
        self.stage('Complex_I16')
        decl=next(iter(packages(self.config).values())).declarations[0]
        self.assertIn('with Convention => C;',decl.signature)

    def test_unique_renamed_anchor_and_source_ownership(self):
        result=self.stage();match=result.profile_matches[0]
        self.assertEqual(match['source_target'],'AMS.MEL.RF.C2.add_rx_job_intervals')
        self.assertEqual(match['anchor'],SECTION.fullmatch(ITEMS['Add_Job_Intervals']['native_excerpt'])[2])
        self.assertIn('not visibly rendered',match['omitted_text_ownership'])

    def test_duplicate_anchor(self):
        self.stage();self.page.write_text(self.page.read_text()+ITEMS['Add_Job_Intervals']['native_excerpt'])
        with self.assertRaisesRegex(ValueError,'duplicate native'):snapshot(self.config,self.site)

    def test_ambiguous_native_renaming(self):
        self.stage();excerpt=ITEMS['Add_Job_Intervals']['native_excerpt']
        anchor=SECTION.fullmatch(excerpt)[2]
        self.page.write_text(self.page.read_text()+excerpt.replace(anchor,'1'*64))
        with self.assertRaisesRegex(ValueError,'ambiguous'):snapshot(self.config,self.site)

    def test_ambiguous_native_record(self):
        self.stage('Complex_I8');excerpt=ITEMS['Complex_I8']['native_excerpt']
        anchor=SECTION.fullmatch(excerpt)[2]
        self.page.write_text(self.page.read_text()+excerpt.replace(anchor,'1'*64))
        with self.assertRaisesRegex(ValueError,'ambiguous'):snapshot(self.config,self.site)

    def test_missing_own_anchor(self):
        self.stage();self.page.write_text(self.page.read_text().replace(ITEMS['Add_Job_Intervals']['native_excerpt'],''))
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_missing_source_target(self):
        self.stage();self.source.write_text(self.source.read_text().replace(ITEMS['Add_RX_Job_Intervals']['source_signature'],''))
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_ambiguous_source_target(self):
        self.stage();self.source.write_text(self.source.read_text().replace('\nend ', '\n'+ITEMS['Add_RX_Job_Intervals']['source_signature']+'\nend '))
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_nested_target_scope_unsupported(self):
        self.stage();self.source.write_text(self.source.read_text().replace('package AMS.MEL.RF.C2 is','package AMS.MEL.RF.C2 is\npackage Nested is\nprocedure Hidden;\nend Nested;'))
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_generic_package_unsupported(self):
        self.stage();self.source.write_text('generic\n'+self.source.read_text())
        with self.assertRaisesRegex(ValueError,'unmatched'):snapshot(self.config,self.site)

    def test_no_target_hyperlink_and_immutable_native(self):
        self.stage();before=identities(self.site);owned=self.source.read_bytes()
        result=enhance(self.config,self.site)
        self.assertEqual(result['linked_types'],0)
        self.assertEqual(preserve_native(before,self.site)['status'],'preserved')
        self.assertNotIn('href="#',self.page.read_text())
        self.assertEqual(self.source.read_bytes(),owned)
        self.assertEqual(verify(self.config,self.site)['mode'],'verified')

    def test_record_preservation_and_idempotence(self):
        self.stage('Complex_I16');before=identities(self.site)
        enhance(self.config,self.site);state=self.page.read_bytes();enhance(self.config,self.site)
        self.assertEqual(state,self.page.read_bytes())
        self.assertEqual(preserve_native(before,self.site)['status'],'preserved')

    def test_wrong_source_pin(self):
        self.stage('Complex_I8')
        with self.assertRaisesRegex(ValueError,'pinned source mismatch'):
            check_snapshot(self.root,{'src/unit.ads':'0'*64})

    def test_record_source_mutation_after_enhancement(self):
        self.stage('Complex_I8');enhance(self.config,self.site)
        self.source.write_text(self.source.read_text().replace('Convention => C','Convention => Ada'))
        with self.assertRaisesRegex(ValueError,'source'):verify(self.config,self.site)

    def test_renaming_source_mutation_after_enhancement(self):
        self.stage();enhance(self.config,self.site)
        self.source.write_text(self.source.read_text().replace('renames Add_RX_Job_Intervals','renames Missing'))
        with self.assertRaisesRegex(ValueError,'source'):verify(self.config,self.site)