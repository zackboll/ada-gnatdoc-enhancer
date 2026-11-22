"""Schema-2 authority, lexical correspondence and publication mutation controls."""
from dataclasses import replace
import json
import re
import shutil
import unittest
from types import SimpleNamespace

from ada_gnatdoc_enhancer.body_destinations import reconcile
from ada_gnatdoc_enhancer.body_inventory import parse_unit
from ada_gnatdoc_enhancer.body_sources import MODE, body_evidence, inventory
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.source_view import enhance_page
from ada_gnatdoc_enhancer.util import digest, sorted_json
from _helper import Fixture
from test_source_view import Text


class Correspondence(unittest.TestCase):
    def reconcile(self, specs, implementations, *, prefix='', body_prefix=''):
        spec = parse_unit(prefix + 'package P is\n' + specs + '\nend P;', body=False)
        body = parse_unit(body_prefix + 'package body P is\n' + implementations + '\nend P;', body=True)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(body)
        native = [SimpleNamespace(declaration=SimpleNamespace(kind=h.kind, name=h.name, source_line=h.line),
                                  section=SimpleNamespace(anchor=str(i)))
                  for i, h in enumerate(spec.headers) if h.public]
        return list(reconcile(spec, native, spec, body, {}).values())

    def test_overloads_and_multiline_profiles_reverse_order(self):
        specs = '''function Read (Value : Integer) return Integer;
function Read (Value : Float) return Float;
function Read (Value, Other : Integer) return Integer;
procedure Read (Value : out Integer);
function Read (Value : Integer) return Float;
procedure Read (Value : in out Float);'''
        bodies = '''procedure Read (Value : in out Float) is begin null; end Read;
function Read (Value : Integer) return Float is begin return 0.0; end Read;
procedure Read (Value : out Integer) is begin Value := 1; end Read;
function Read
  (Value : in Standard.Integer; -- comment: is separate;
   Other : Integer) return Standard.Integer is begin return Value; end Read;
function Read (Value : Float) return Float is begin return Value; end Read;
function Read (Value : Integer) return Integer is begin return Value; end Read;'''
        self.assertEqual(self.reconcile(specs, bodies), [(n, None) for n in (9, 8, 5, 4, 3, 2)])

    def test_full_profile_names_modes_defaults_and_shadowing(self):
        spec = 'type T is new Integer;\nprocedure Poke (Value : in T := 1);'
        accepted = 'procedure Poke (Value : P.T := 1) is begin null; end;'
        self.assertEqual(self.reconcile(spec, accepted), [(2, None)])
        for body in (accepted.replace('Value', 'Other'), accepted.replace(' := 1', ' := 2'),
                     accepted.replace(' := 1', ''), accepted.replace(': P.T', ': in out P.T'),
                     'type T is new Float;\n' + accepted.replace('P.T', 'T'),
                     'package P renames Something;\n' + accepted):
            with self.subTest(body=body):
                self.assertIsNone(self.reconcile(spec, body)[0][0])
        self.assertIsNone(self.reconcile(spec.replace(':= 1', ':= Constant_Name'), accepted)[0][0])
        self.assertIsNone(self.reconcile('procedure Poke (Value : P.T);\ntype T is new Integer;',
                                         accepted)[0][0])

    def test_unsupported_forms_and_nested_helpers_are_not_targets(self):
        specs = '''procedure Ab is abstract;
procedure Do_Nothing is null;
procedure Alias renames Target;
procedure External; pragma Import (C, External);
procedure Local;
function Expression return Integer is (1);
procedure Instantiate is new Other;
procedure Subunit;
procedure Target (X : Integer);
procedure No_Implementation;
procedure Ambiguous (X : Integer);'''
        bodies = '''-- procedure Local is begin null; end Local;
Fake : constant String := "procedure Local is begin null; end Local;";
procedure Helper is
   procedure Local is begin null; end Local;
begin
   declare
      procedure Local is begin null; end Local;
   begin null; end;
end Helper;
procedure Subunit is separate;
procedure Target (X : Float); -- unrelated forward declaration
procedure Target (X : Float) is begin null; end Target;
procedure Target (X : Integer) is begin null; end Target;
procedure Ambiguous (X : Integer) is begin null; end Ambiguous;
procedure Ambiguous (X : Local_Unknown);'''
        result = self.reconcile(specs, bodies)
        self.assertEqual(result[8], (14, None))
        self.assertEqual([reason for _, reason in result], [
            'specification-abstract', 'specification-null', 'specification-renaming',
            'foreign-or-unsupported-convention', 'no-conformant-direct-body',
            'specification-expression', 'specification-instance', 'implementation-separate',
            None, 'no-conformant-direct-body', 'ambiguous-body-candidates'])

    def test_duplicate_bodies_and_same_profile_forward_do_not_win_by_order(self):
        full = 'procedure Run (Value : Integer) is begin null; end Run;'
        for other in (full, 'procedure Run (Value : Integer);'):
            self.assertEqual(self.reconcile('procedure Run (Value : Integer);', full+'\n'+other),
                             [(None, 'ambiguous-body-candidates')])
        self.assertEqual(self.reconcile('procedure Run (Value : Integer);\nprivate\n'
                                        'procedure Run (Value : Unresolved);', full),
                         [(None, 'ambiguous-specification-candidates')])

    def test_contract_aspects_do_not_mask_an_import(self):
        spec = 'procedure Run (Value : Integer) with Pre => Value > 0'
        body = 'procedure Run (Value : Integer) is begin null; end;'
        self.assertEqual(self.reconcile(spec+';', body), [(2, None)])
        self.assertEqual(self.reconcile(spec+', Import;', body), [(None, 'specification-aspects')])

    def test_unknown_or_multiunit_scope_not_recovered(self):
        for raw in ('separate (Parent) package body P is end P;',
                    'package body Other is package body P is end P; end Other; package body P is end;',
                    'package body P is procedure F is end F; end P;',
                    'package body P is begin select delay 1.0; end select; end P;',
                    'package body P is procedure F is begin null; end Wrong; end P;'):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_unit(raw, body=True))


class BodyPublication(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.root, self.site = self.fx.root, self.fx.site
        self.path = self.root/'src/implementation.adb'  # intentionally not named like the spec
        self.payload = ('\t-- <script onload="evil"> &amp; {{ /tmp/secret\r\n'
                        'package body OpenCV.Core is\r\n'
                        '   function Convert\r\n'
                        '     (Source : in Mat) return Mat is\r\n'
                        '   begin\r\n'
                        '      return Source;\r\n'
                        '   end Convert;\r\n'
                        'end OpenCV.Core;').encode()
        self.path.write_bytes(self.payload)
        source = packages(self.fx.config)
        specs, bodies, _ = inventory(self.fx.config, source)
        self.data = dict(schema_version=2, mode=MODE, files=hashes(self.site), sources=specs,
                         bodies=body_evidence(source, bodies))
        self.config = self.pin(self.data)

    def pin(self, data):
        raw = sorted_json(data).encode()
        (self.root/'native.json').write_bytes(raw)
        return replace(self.fx.config, source_view=dict(schema_version=2, mode=MODE,
                       native_manifest='native.json', native_manifest_sha256=digest(raw)))

    def test_complete_pages_exact_links_restoration_and_idempotence(self):
        pristine = hashes(self.site)
        second = self.root/'second'; shutil.copytree(self.site, second)
        source = packages(self.config)
        self.assertEqual(inventory(self.config, source),
                         inventory(self.config, dict(reversed(list(source.items())))))
        result = enhance(self.config, self.site)
        self.assertEqual(result['body_pages'], 1)
        self.assertEqual(result['body_operation_links'], 1)
        identity = json.loads((self.site/'api/presentation.json').read_bytes())['source_view']
        body = identity['bodies'][0]
        parsed = Text((self.site/body['page']).read_text())
        self.assertEqual(parsed.text.encode(), self.payload)
        self.assertEqual(parsed.lines, ['L'+str(i) for i in range(1, 9)])
        self.assertEqual(body['sha256'], digest(self.payload))
        self.assertNotIn(b'<script', (self.site/body['page']).read_bytes())
        spec = next(f for f in identity['files'] if f['package'] == 'OpenCV.Core')
        link = next(e for e in spec['declarations'] if e['name'].endswith('.Convert'))
        self.assertEqual(link['body_line'], 3)
        self.assertIn('href="implementation.adb.html#L3"', (self.site/spec['page']).read_text())
        self.assertIn(f'href="opencv-core.ads.html#L{link["line"]}"', (self.site/body['page']).read_text())
        native = next(p for p in (second/'api').glob('*.html') if '<h1>OpenCV.Core</h1>' in p.read_text())
        pkg = source['opencv.core']; raw = native.read_bytes().decode()
        linked = enhance_page(raw, pkg, spec['declarations'], spec['source'], schema=2)
        self.assertEqual(enhance_page(linked, pkg, spec['declarations'], spec['source'], schema=2,
                                      restore=True).encode(), native.read_bytes())
        self.assertEqual(hashes(second), pristine)
        enhance(self.config, second)
        self.assertEqual(hashes(self.site), hashes(second))
        verify(self.config, self.site); enhance(self.config, self.site)
        self.assertEqual(hashes(self.site), hashes(second))
        self.assertEqual(self.path.read_bytes(), self.payload)

    def test_unrelated_private_and_subunit_files_not_published(self):
        (self.root/'src/private.ads').write_text('private package Hidden is end Hidden;')
        (self.root/'src/private.adb').write_text('package body Hidden is end Hidden;')
        (self.root/'src/unselected.adb').write_text('package body Dependency is end Dependency;')
        (self.root/'src/subunit.adb').write_text('separate (OpenCV.Core) procedure Inner is begin null; end;')
        self.assertEqual(enhance(self.config, self.site)['body_pages'], 1)

    def test_replaced_wrong_missing_duplicate_case_colliding_and_symlink_bodies(self):
        for other in (b'package body Wrong is end Wrong;', self.payload + b'\r\n-- change',
                      self.payload + b'\r\nprocedure Second is begin null; end;'):
            self.path.write_bytes(other)
            with self.assertRaises(EnhancementError): enhance(self.config, self.site)
        self.path.unlink()
        with self.assertRaises(EnhancementError): enhance(self.config, self.site)
        self.path.write_bytes(self.payload)
        for name, raw in (('duplicate.adb', self.payload), ('Implementation.adb', self.payload),
                          ('broken.adb', b'package body OpenCV.Core is (')):
            extra = self.path.with_name(name); extra.write_bytes(raw)
            with self.assertRaises(EnhancementError): enhance(self.config, self.site)
            extra.unlink()
        extra = self.path.with_name('link.adb'); extra.symlink_to(self.path)
        with self.assertRaises(EnhancementError): enhance(self.config, self.site)
        extra.unlink()
        folder = self.root/'foreign'; folder.mkdir(); self.path.rename(folder/self.path.name)
        with self.assertRaisesRegex(EnhancementError, 'directory ownership conflict'):
            inventory(replace(self.config, sources=('src', 'foreign')), packages(self.config))

    def test_evidence_contract_and_forged_ownership(self):
        config_file = self.root/'project.toml'; text = config_file.read_text()
        def loaded(options):
            config_file.write_text(text + '\n[source_view]\n' + '\n'.join(
                f'{k} = {json.dumps(v)}' for k, v in options.items()))
            return load(self.root, config_file.name)
        self.assertEqual(loaded(self.config.source_view).source_view, self.config.source_view)
        for change in ({'schema_version': 1}, {'mode': 'public-specifications'}, {'unknown': 1}):
            with self.assertRaises(EnhancementError): loaded(self.config.source_view | change)
        for field, forged in (('bodies', {}), ('unknown', {}), ('mode', 'public-specifications'),
                              ('bodies', {'src/implementation.adb': dict(package='OpenCV.Core.Sparse',
                                                                       sha256=digest(self.payload))}),
                              *[('bodies', {p: next(iter(self.data['bodies'].values()))}) for p in (
                                  'src/../src/implementation.adb', 'src/implementation%2eadb',
                                  'src/implementation&#46;adb', 'src//implementation.adb')]):
            with self.subTest(field=field, forged=forged):
                config = self.pin(self.data | {field: forged})
                with self.assertRaises(EnhancementError): enhance(config, self.site)

    def test_native_bytes_are_not_normalized_before_pinning(self):
        target = self.site/'api/index.html'
        raw = target.read_bytes().replace(b'<iframe', b'\r\n<iframe', 1)
        target.write_bytes(raw)
        with self.assertRaisesRegex(EnhancementError, 'independently pinned'):
            enhance(self.config, self.site)
        self.config = self.pin(self.data | {'files': self.data['files'] | {'api/index.html': digest(raw)}})
        enhance(self.config, self.site); verify(self.config, self.site)
        original = json.loads((self.site/'api/presentation.json').read_bytes())['original_api_html']
        self.assertEqual(original['api/index.html'].encode(), raw)

    def test_resealed_pages_wrong_existing_lines_source_script_and_resources(self):
        enhance(self.config, self.site)
        mp = self.site/'api/presentation.json'; original = mp.read_bytes(); data = json.loads(original)
        body = data['source_view']['bodies'][0]['page']
        api = next(n for n in data['original_api_html'] if '<h1>OpenCV.Core</h1>' in data['original_api_html'][n])
        raw = (self.site/body).read_bytes(); native = (self.site/api).read_bytes()
        for name, baseline, payload in (
                (api, native, native.replace(b'implementation.adb.html#L3', b'implementation.adb.html#L4')),
                (body, raw, raw.replace(b'id="L3"', b'id="L4"', 1)),
                (body, raw, raw.replace(b'id="L3"', b'id="TEMP"').replace(
                    b'id="L4"', b'id="L3"').replace(b'id="TEMP"', b'id="L4"')),
                (body, raw, raw.replace(b'return</span>', b'raise</span>', 1)),
                (body, raw, raw.replace(b'</nav>', b'<a href="https://evil.invalid/">x</a></nav>')),
                (body, raw, raw.replace(b'</head>', b'<script src="extra.js"></script></head>')),
                (body, raw, raw.replace(b'</head>', b'<link rel="stylesheet" href="extra.css"></head>')),
                (body, raw, raw.replace(b'<pre ', b'<pre onclick="alert(1)" ')),
                (body, raw, re.sub(rb'(\.ads\.html#L)\d+', rb'\g<1>999', raw, count=1))):
            self.assertNotEqual(payload, baseline)
            (self.site/name).write_bytes(payload)
            resealed = data | {'output_sha256': data['output_sha256'] | {name: digest(payload)}}
            mp.write_text(sorted_json(resealed))
            with self.assertRaises(EnhancementError): verify(self.config, self.site)
            (self.site/name).write_bytes(baseline)
        data['source_view']['bodies'][0]['package'] = 'OpenCV.Core.Sparse'
        mp.write_text(sorted_json(data))
        with self.assertRaises(EnhancementError): verify(self.config, self.site)
        mp.write_bytes(original)
        extra = (self.site/body).with_name('extra.adb.html'); extra.write_bytes(raw)
        with self.assertRaises(EnhancementError): verify(self.config, self.site)
        forged = json.loads(original)
        forged['original_api_html'][extra.relative_to(self.site).as_posix()] = raw.decode()
        mp.write_text(sorted_json(forged))
        with self.assertRaisesRegex(EnhancementError, 'original HTML inventory'):
            verify(self.config, self.site)
        mp.write_bytes(original)
        extra.unlink(); (self.site/body).unlink()
        with self.assertRaises(EnhancementError): verify(self.config, self.site)