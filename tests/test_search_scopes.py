"""Adversarial source scopes; native anchors and expected records are separate."""
from dataclasses import replace
import html
import json
from pathlib import Path
import unittest

from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import public_declarations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.search import INDEX, records
from ada_gnatdoc_enhancer.util import digest, sorted_json
from _helper import Fixture


SOURCE = '''package OpenCV.Core is
   type Mat is tagged limited private;
   type Float32_Value is digits 6;
   function Convert (Source : Mat) return Mat;
   procedure Before;
   package Nested is
      type Hidden is private;
      procedure Before;
   private
      type Hidden is null record;
   end Nested;
   procedure Between;
   package Other is
      package Deeper is
         procedure Nested_Only;
      end Deeper;
   end Other;
   generic
      type Formal is private;
      with function Formal_Call return Formal is <>;
      with package Formal_Package is new Template (<>);
   package Template is
      type Template_Only is private;
   end Template;
   generic
      type Another_Formal is private;
   procedure Generic_Call (X : Another_Formal);
   package Instance is new Template (Integer);
   procedure Instantiated_Call is new Generic_Call (Integer);
   package Alias renames Nested;
   protected Lock is
      procedure Protected_Only;
   private
      Secret : Integer;
   end Lock;
   protected type Typed_Lock is
      function Protected_Function return Boolean;
   end Typed_Lock;
   task Worker is
      entry Task_Only;
   end Worker;
   task type Worker_Type;
   -- procedure Comment_Only; package Fake is private
   Message : constant String := "private; procedure String_Only; end;";
   procedure After;
   procedure Overloaded (X : Integer);
   procedure Overloaded (X : Boolean);
   function Result return Integer;
   function Result return Boolean;
   type Public_View is limited private;
private type Public_View is null record;
   procedure Private_Only;
end OpenCV.Core;
'''

# Explicit independently specified native signatures: no extraction from SOURCE.
PUBLIC = ['procedure Before;', 'procedure Between;', 'procedure After;',
          'procedure Overloaded (X : Integer);', 'procedure Overloaded (X : Boolean);',
          'function Result return Integer;', 'function Result return Boolean;',
          'type Public_View is limited private;']
NEGATIVE = ['procedure Nested_Only;', 'procedure Protected_Only;',
            'procedure Private_Only;', 'procedure String_Only;',
            'procedure Comment_Only;', 'type Formal is private;',
            'type Template_Only is private;', 'procedure Invented;']


class ScopeInventory(unittest.TestCase):
    def test_minimal_sibling_boundaries_and_source_order(self):
        declarations = public_declarations(SOURCE)
        self.assertEqual([d.name for d in declarations],
                         ['Mat', 'Float32_Value', 'Convert', 'Before', 'Between', 'After',
                          'Overloaded', 'Overloaded', 'Result', 'Result', 'Public_View'])
        self.assertEqual([d.line for d in declarations], sorted(d.line for d in declarations))
        self.assertEqual([d.signature for d in declarations if d.name == 'Overloaded'], PUBLIC[3:5])

    def test_private_boundaries_are_not_private_type_keywords(self):
        for boundary in ('private\n', 'private ', 'private -- boundary\n'):
            source = ('package Example is type View is tagged limited private; '
                      'type Extension is new Base with private; procedure Public; ' +
                      boundary + 'type View is null record; procedure Hidden; end Example;')
            self.assertEqual([d.name for d in public_declarations(source)],
                             ['View', 'Extension', 'Public'])

    def test_library_generic_formals_and_body_units(self):
        self.assertEqual([d.name for d in public_declarations(
            'generic type Formal is private; with procedure Op;\n'
            'package Example is type Public is private; end Example;')], ['Public'])
        for source in ('package body Example is procedure Hidden; end Example;',
                       'package Example is new Template (Integer);',
                       'package Example renames Other;'):
            self.assertEqual(public_declarations(source), [])

    def test_ambiguous_boundaries_fail_closed(self):
        for scope in ('package Nested is procedure Hidden; end Wrong;',
                      'protected Lock is procedure Hidden;',
                      'declare procedure Hidden; begin null; end;'):
            self.assertEqual(public_declarations('package Example is procedure Before; ' +
                             scope + ' procedure After; end Example;'), [])

    def test_nested_body_does_not_promote_local_declarations(self):
        source = '''package Example is
            procedure Before;
            package body Nested is
                procedure Local is begin null; end Local;
            begin null; end Nested;
            procedure After;
            end Example;'''
        self.assertEqual([d.name for d in public_declarations(source)], ['Before', 'After'])

    def test_quoted_operator_does_not_suppress_identifier_siblings(self):
        self.assertEqual([d.name for d in public_declarations('package Example is '
            'procedure Before; function "+" (X : Integer) return Integer; '
            'procedure After; end Example;')], ['Before', 'After'])
        self.assertEqual([d.name for d in public_declarations('package Example is '
            'function -- "not an operator"\n Real_Name return Integer; end Example;')], ['Real_Name'])

    def test_first_declaration_preserves_existing_offset_based_guide_authority(self):
        from ada_gnatdoc_enhancer.inventory import _one
        from ada_gnatdoc_enhancer.source_references import direct_lines
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'example.ads'
            path.write_text('package Example is\n type First is range 0 .. 1;\nend Example;')
            package = _one(path)
            self.assertEqual(package.declarations[0].line, 1)
            self.assertIn(package.declarations[0].line, direct_lines(package))


class ScopeSearch(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.config = replace(self.fx.config, search=True)
        (self.fx.root/'src/opencv-core.ads').write_text(SOURCE)
        self.page = next(p for p in (self.fx.site/'api').glob('*.html')
                         if '<h1>OpenCV.Core</h1>' in p.read_text())
        text = self.page.read_text()
        sections = ''
        self.anchors = {}
        for i, signature in enumerate(PUBLIC + NEGATIVE, 1):
            name = signature.split()[1].rstrip(';')
            anchor = f'{i:064x}'
            self.anchors[signature] = anchor
            sections += ('<h4 id=' + anchor + '>' + name + '</h4>\n'
                     '<pre class=ada-code-snippet><code>' + html.escape(signature) + '</code></pre>')
        self.page.write_text(text.replace('</body>', sections + '</body>'))

    def test_complete_public_records_without_private_or_invented_anchors(self):
        values = records(self.config, snapshot(self.config, self.fx.site), {})
        by_href = {r['href']: r for r in values}
        for signature in PUBLIC:
            href = self.page.name + '#' + self.anchors[signature]
            self.assertIn(href, by_href)
            self.assertEqual(by_href[href]['name'], 'OpenCV.Core.' + signature.split()[1].rstrip(';'))
            self.assertIn(signature, by_href[href]['text'])
        for signature in NEGATIVE:
            self.assertNotIn(self.page.name + '#' + self.anchors[signature], by_href)
        overloaded = [r for r in values if r['name'] == 'OpenCV.Core.Overloaded']
        self.assertEqual([r['label'] for r in overloaded],
                         ['OpenCV.Core.Overloaded (overload 1/2)', 'OpenCV.Core.Overloaded (overload 2/2)'])
        self.assertEqual(len(by_href), len(values))

    def test_missing_or_swapped_native_evidence_cannot_be_invented(self):
        original = self.page.read_text()
        for text in (original.replace(self.anchors[PUBLIC[0]], 'not-an-anchor'),
                     original.replace('procedure Before;', 'procedure Different;')):
            self.page.write_text(text)
            with self.assertRaises(EnhancementError): snapshot(self.config, self.fx.site)

    def test_self_consistent_private_record_digest_shell_and_manifest_rejected(self):
        enhance(self.config, self.fx.site)
        path = self.fx.site/INDEX; original = path.read_bytes()
        shell_path = self.fx.site/'api/index.html'; shell = shell_path.read_text()
        manifest_path = self.fx.site/'api/presentation.json'
        manifest_original = manifest_path.read_text()
        for signature in NEGATIVE:
            data = json.loads(original)
            name = 'OpenCV.Core.' + signature.split()[1].rstrip(';')
            href = self.page.name + '#' + self.anchors[signature]
            data['records'].append(dict(kind='operation', name=name, label=name, href=href, text=signature))
            value = sorted_json(data).encode(); path.write_bytes(value)
            forged_shell = shell.replace(digest(original), digest(value)).replace(
                'data-count="' + str(len(data['records'])-1) + '"',
                'data-count="' + str(len(data['records'])) + '"').replace(
                    '</div>', '<a href="' + href + '" data-search-name="' + name +
                    '" data-search-kind="operation"></a></div>', 1)
            shell_path.write_text(forged_shell)
            manifest = json.loads(manifest_original)
            manifest['output_sha256'][INDEX] = digest(value)
            manifest['output_sha256']['api/index.html'] = digest(forged_shell.encode())
            manifest_path.write_text(sorted_json(manifest))
            with self.subTest(signature=signature), self.assertRaises(EnhancementError):
                verify(self.config, self.fx.site)