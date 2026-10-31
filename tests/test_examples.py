"""Opt-in presentation, conservative resolution and output-side tamper resistance."""
from __future__ import annotations

from dataclasses import replace
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ada_gnatdoc_enhancer.authored import markdown, render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.examples import Resolver, STYLESHEET, code, landing
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json

FIXTURES = Path(__file__).parent / 'authored-fixtures'


class Text(HTMLParser):
    def __init__(self, markup):
        super().__init__(); self.parts = []; self.feed(markup); self.close()

    def handle_data(self, value):
        self.parts.append(value)


class Examples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load(FIXTURES/'core', 'project.toml')
        cls.native = snapshot(cls.config, FIXTURES/'core'/'native')
        cls.resolver = Resolver(cls.config, cls.native)

    def test_shared_lexer_text_and_classes(self):
        text = '''procedure Begin_Keyword is
   S : String := "begin ""OpenCV.Core.Mat"" <script>&";
   C : Character := '<';
   N : Float := 16#F.F#E+1 + 1.5E-2;
begin
   -- Mat and begin are inert <a href="evil">
   Inspect (S'Access, S'Length, S'First);
end Begin_Keyword;
'''
        result = code(text, self.resolver)
        self.assertEqual(''.join(Text(result).parts), text)
        for kind in ('keyword', 'string', 'character', 'number', 'attribute', 'comment', 'operator'):
            self.assertIn('class="ada-' + kind + '"', result)
        self.assertIn('Begin_Keyword', result)
        self.assertNotIn('>Begin</span>_Keyword', result)
        self.assertNotIn('<a ', result)
        self.assertNotIn('<script>', result)

    def test_multiline_qualified_and_visible_unqualified_types(self):
        text = 'use OpenCV.Core;\nImage : constant\n Mat;\nOther : OpenCV . Core . Mat;\n'
        result = code(text, self.resolver)
        self.assertEqual(''.join(Text(result).parts), text)
        self.assertEqual(result.count('<a '), 2)
        target = self.resolver.symbols['opencv.core.mat'][0]
        self.assertIn('../api/' + target.href, result)
        self.assertIn('api/' + target.href, code(text, self.resolver, landing=True))

    def test_no_inferred_visibility_or_object_prefix(self):
        for text in ('Image : Mat;', 'Copy := Image.Clone (1);',
                     'use Missing.Owner; use OpenCV.Core; Image : Mat;',
                     '-- X : OpenCV.Core.Mat;\nS := "X : OpenCV.Core.Mat;";',
                     'Call (OpenCV.Core.Mat => 1);'):
            with self.subTest(text=text):
                self.assertNotIn('<a ', code(text, self.resolver))

    def test_shadowed_local_formal_subprogram_loop_enum_and_prefix(self):
        for local in ('Mat : Integer;', 'procedure Mat (X : Integer);',
                      'procedure P (Mat : Integer);', 'type Mat is null record;',
                      'for Mat in 1 .. 2 loop', 'type E is (Mat, Other);',
                      'package OpenCV renames Local;'):
            reference = 'X : OpenCV.Core.Mat;' if 'package' in local else 'use OpenCV.Core; X : Mat;'
            self.assertNotIn('<a ', code(local + '\n' + reference, self.resolver), local)

    def test_ambiguous_overloads_never_pick_first(self):
        for name in ('Create', 'Clone'):
            self.assertGreater(len(self.resolver.symbols['opencv.core.' + name.lower()]), 1)
            for prefix in ('', 'OpenCV.Core.'):
                self.assertNotIn('<a ', code('use OpenCV.Core; X := ' + prefix + name + '\n (X);', self.resolver))
        self.assertNotIn('<a ', code('OpenCV.Core.Float32_Access.Get (Image, 0, 0);', self.resolver))

    def test_private_missing_unsupported_and_multiple_use_namespaces(self):
        for text in ('X : OpenCV.Core.Nonexistent;', 'X : OpenCV.Internal.C_API.Mat;',
                     'use OpenCV.Core; use OpenCV; X : Mat;',
                     'task Mat; use OpenCV.Core; X : Mat;',
                     'protected type Mat is end Mat; use OpenCV.Core; X : Mat;'):
            self.assertNotIn('<a ', code(text, self.resolver))
        resolver = Resolver(self.config, self.native)
        resolver.public['opencv.core'] = 'type Unrelated is null record;'
        self.assertNotIn('<a ', code('X : OpenCV.Core.Mat;', resolver))

    def test_use_clause_scope_and_inherited_names_fail_closed(self):
        for text in ('X : Mat; use OpenCV.Core;',
                     'declare use OpenCV.Core; begin null; end; X : Mat;',
                     'use OpenCV.Core; type Derived is new Foreign; X : Mat;',
                     'use OpenCV.Core; use all type Foreign; X : Mat;',
                     'package Local is use OpenCV.Core; end Local; X : Mat;'):
            self.assertNotIn('<a ', code(text, self.resolver))

    def test_source_native_missing_and_swapped_ownership_rejected(self):
        pages = dict(self.native.pages); owner = 'opencv.core'; page = pages[owner]
        for bad in (replace(page, package='Swapped.Owner'), replace(page, sections=[])):
            pages[owner] = bad
            with self.assertRaises(EnhancementError):
                Resolver(self.config, replace(self.native, pages=pages))

    def test_same_named_cross_package_symbols_do_not_authorize_bare_names(self):
        resolver = Resolver(self.config, self.native)
        target = resolver.symbols['opencv.core.mat'][0]
        resolver.owners.add('other.owner')
        resolver.symbols['other.owner.mat'] = [replace(target, package='Other.Owner')]
        self.assertNotIn('<a ', code('use Other.Owner; use OpenCV.Core; X : Mat;', resolver))

    def test_unique_callable_multiline_source_native_evidence(self):
        targets = [d for group in self.resolver.symbols.values() for d in group
                   if d.total == 1 and d.declaration.kind in ('function', 'procedure') and
                   d.package.lower() in self.resolver.supported]
        self.assertTrue(targets)
        d = targets[0]; name = d.package + '.' + d.declaration.name
        result = code(name + '\n (Argument);', self.resolver)
        self.assertIn('href="../api/' + d.href + '"', result)
        self.assertEqual(''.join(Text(result).parts), name + '\n (Argument);')
        self.assertNotIn('<a ', code('use ' + d.package + '; X\'' + d.declaration.name + ' (X);', self.resolver))

    def test_non_ada_fences_unchanged(self):
        for language in ('sh', 'shell', 'text', ''):
            text = '# Title\n\n```' + language + '\nbegin < &\n```\n'
            self.assertEqual(markdown(text, [language])[0], markdown(text, [language], example_renderer=code)[0])

    def test_fence_decoded_text_exact(self):
        text = '\tX : String := "<>&";\n\n-- Comment\n'
        result = markdown('# Title\n\n```ada\n' + text + '```\n', ['ada'], example_renderer=code)[0]
        inner = result.split('<code class="language-ada">')[1].split('</code>')[0]
        self.assertEqual(''.join(Text(inner).parts), text)
        self.assertIn('<span class="ada-example-end"></span>', inner)

    def test_explicit_disabled_options_preserve_output_bytes(self):
        before = render(self.config, self.native)
        self.assertEqual(before, render(replace(self.config, ada_example_highlighting=False,
                                                ada_example_api_links=False,
                                                ada_landing_example_highlighting=False), self.native))

    def test_landing_exact_and_unrelated_bytes(self):
        text = 'begin\n null;\nend;\n'
        home = '<head></head><pre>alr with core</pre><pre>' + text.rstrip('\n') + '</pre><footer>unchanged</footer>'
        result = landing(home, text)
        self.assertTrue(result.startswith('<head></head><pre>alr with core</pre>'))
        self.assertTrue(result.endswith('</pre><footer>unchanged</footer>'))
        self.assertEqual(''.join(Text(result.split('tabindex="0">')[1].split('</pre>')[0]).parts), text.rstrip('\n'))

    def test_landing_missing_duplicate_nested_and_attributes(self):
        for home in ('<pre>other</pre>', '<pre>begin</pre><pre>begin</pre>',
                     '<pre><code>begin</code></pre>', '<pre class="anything">begin</pre>',
                     '<pre>be<!-- comment -->gin</pre>', '<pre>begin<br></pre>',
                     '<pre>begin<?instruction?></pre>', '<pre>begin<!DOCTYPE html></pre>',
                     '<pre>begin', '<pre><pre>begin</pre></pre>'):
            with self.subTest(home=home), self.assertRaises(EnhancementError):
                landing(home, 'begin\n')

    def test_landing_entities_preserve_decoded_source(self):
        result = landing('<pre>X := &quot;&lt;&amp;&gt;&quot;;</pre>', 'X := "<&>";\n')
        self.assertEqual(''.join(Text(result).parts), 'X := "<&>";')

    def test_strict_configuration_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'source').mkdir(); (root/'manifest').write_text('{}')
            prefix = 'schema_version = 1\nproject = "test"\n[sources]\ndirectories = ["source"]\n[guides]\n'
            base = 'mode = "authored-markdown"\nmanifest = "manifest"\nsha256 = "' + 'a'*64 + '"\n'
            for key in ('ada_example_highlighting', 'ada_example_api_links', 'ada_landing_example_highlighting'):
                for value in ('1', '"true"', '[]', '{}'):
                    (root/'project.toml').write_text(prefix + base + key + ' = ' + value)
                    with self.assertRaises(EnhancementError): load(root, 'project.toml')
            for mode in ('none', 'html', 'markdown', 'authored-html'):
                (root/'project.toml').write_text(prefix + base.replace('authored-markdown', mode) + 'ada_example_highlighting = false')
                with self.assertRaises(EnhancementError): load(root, 'project.toml')
            (root/'project.toml').write_text(prefix + base + 'ada_example_api_links = true')
            with self.assertRaises(EnhancementError): load(root, 'project.toml')
            (root/'project.toml').write_text(prefix + base + 'ada_example_highlighting = true\nada_example_api_links = true\nada_landing_example_highlighting = true')
            self.assertTrue(load(root, 'project.toml').ada_example_api_links)

    def test_authentic_opt_in_changed_file_allowlist_and_determinism(self):
        for name in ('core', 'imgproc', 'geometry'):
            config = load(FIXTURES/name, 'project.toml'); native = snapshot(config, FIXTURES/name/'native')
            baseline = render(config, native)
            config = replace(config, ada_example_highlighting=True, ada_example_api_links=True,
                             ada_landing_example_highlighting=True)
            enabled = render(config, native)
            self.assertEqual(enabled, render(config, native))
            self.assertEqual(set(enabled) - set(baseline), {STYLESHEET})
            self.assertEqual(enabled['guides/gnatdoc-guides.css'], baseline['guides/gnatdoc-guides.css'])
            for path in baseline:
                if path.endswith('.html'):
                    self.assertEqual(''.join(Text(enabled[path].decode()).parts), ''.join(Text(baseline[path].decode()).parts))
            if name == 'core':
                self.assertEqual(len(native.pages), 195)
                self.assertEqual(len([p for p in enabled if p.startswith('guides/') and p.endswith('.html')]), 5)

    def test_landing_only_does_not_change_guides(self):
        before = render(self.config, self.native)
        after = render(replace(self.config, ada_landing_example_highlighting=True), self.native)
        self.assertEqual({p for p in before if before[p] != after[p]}, {'index.html'})

    def test_landing_missing_identity_rejected(self):
        from unittest.mock import patch
        from ada_gnatdoc_enhancer.authored import manifest
        data = manifest(self.config, self.native); data['landing_example'] = None
        with patch('ada_gnatdoc_enhancer.authored.manifest', return_value=data), self.assertRaises(EnhancementError):
            render(replace(self.config, ada_landing_example_highlighting=True), self.native)

    def test_guide_only_does_not_change_home(self):
        before = render(self.config, self.native)
        after = render(replace(self.config, ada_example_highlighting=True), self.native)
        self.assertEqual(before['index.html'], after['index.html'])

    def test_search_records_do_not_change_with_token_data_boundaries(self):
        from ada_gnatdoc_enhancer.search import records
        before = render(self.config, self.native)
        opted = replace(self.config, ada_example_highlighting=True, ada_example_api_links=True,
                        ada_landing_example_highlighting=True)
        after = render(opted, self.native)
        self.assertEqual(records(self.config, self.native, before), records(opted, self.native, after))

    def test_modified_actual_link_existing_anchor_swapped_owner_external_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'authority'; shutil.copytree(FIXTURES/'core', root)
            config = replace(load(root, 'project.toml'), ada_example_highlighting=True,
                             ada_example_api_links=True, ada_landing_example_highlighting=True)
            site = root/'native'; enhance(config, site)
            page = site/'index.html'; good = page.read_text()
            import re
            match = re.search(r'<a class="ada-api-reference" href="([^"]+)"', good)
            self.assertIsNotNone(match)
            targets = [d for group in self.resolver.symbols.values() for d in group]
            same = next(d for d in targets if d.package == 'OpenCV.Core' and 'api/' + d.href != match[1])
            other = next(d for d in targets if d.package != 'OpenCV.Core')
            metadata = site/'api/presentation.json'; original = metadata.read_bytes()
            for href in ('api/' + same.href, 'api/' + other.href, 'https://evil.invalid/api#anchor',
                         'api/missing.html#anchor', 'javascript:alert(1)'):
                page.write_text(good.replace(match[1], href))
                data = json.loads(original); data['output_sha256']['index.html'] = digest(page.read_bytes())
                metadata.write_text(sorted_json(data))
                with self.subTest(href=href), self.assertRaises(EnhancementError): verify(config, site)
            page.write_text(good); metadata.write_bytes(original); verify(config, site)

    def test_publication_tampering_rehashed_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'authority'; shutil.copytree(FIXTURES/'geometry', root)
            config = replace(load(root, 'project.toml'), ada_example_highlighting=True,
                             ada_example_api_links=True, ada_landing_example_highlighting=True)
            site = root/'native'; enhance(config, site); verify(config, site)
            before = hashes(site); enhance(config, site); self.assertEqual(before, hashes(site))
            path = site/'index.html'; good = path.read_bytes()
            metadata = site/'api/presentation.json'; original = metadata.read_bytes()
            for injection in (b'<a href="https://evil.invalid/">', b'<a href="api/index.html#existing">',
                              b'<span onclick="bad()">', b'<script>bad()</script>'):
                path.write_bytes(good.replace(b'<span class="ada-keyword">', injection, 1))
                data = json.loads(original); data['output_sha256']['index.html'] = digest(path.read_bytes())
                metadata.write_text(sorted_json(data))
                with self.assertRaises(EnhancementError): verify(config, site)
            path.write_bytes(good); metadata.write_bytes(original); verify(config, site)