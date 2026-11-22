"""Source views: byte fidelity, independent identity and resealing attacks."""
from dataclasses import replace
from html.parser import HTMLParser
import importlib.util
import json
import re
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.source_view import build, owned, render
from ada_gnatdoc_enhancer.source_lexer import Token, tokenize
from ada_gnatdoc_enhancer.theme import asset
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.util import digest, sorted_json
from _helper import Fixture


def enable(config, site):
    raw = sorted_json(dict(schema_version=1, sources={
        p.path.relative_to(config.root).as_posix(): digest(p.path.read_bytes())
        for p in packages(config).values()}, files={
        n: d for n, d in hashes(site).items() if n.endswith('.html') or n == 'api/gnatdoc.css'})).encode()
    (config.root/'native-source.json').write_bytes(raw)
    return replace(config, source_view=dict(schema_version=1, mode='public-specifications',
        native_manifest='native-source.json', native_manifest_sha256=digest(raw)))


class Text(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.code = False; self.text = ''; self.lines = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        if tag == 'code': self.code = True
        if tag == 'span' and dict(attrs).get('class') == 'source-line':
            self.lines.append(dict(attrs)['id'])

    def handle_endtag(self, tag):
        if tag == 'code': self.code = False

    def handle_data(self, data):
        if self.code: self.text += data


class SourceView(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        self.config = enable(self.fx.config, self.fx.site)

    def test_strict_opt_in_contract(self):
        self.assertFalse(self.fx.config.source_view)
        p = self.fx.root/'project.toml'; old = p.read_text()
        opts = self.config.source_view
        p.write_text(old + '\n[source_view]\n' + '\n'.join(
            k + ' = ' + json.dumps(v) for k, v in opts.items()))
        self.assertEqual(load(self.fx.root, p.name).source_view, opts)
        for change in ({'schema_version': True}, {'schema_version': 2}, {'mode': 'bodies'},
                       {'url': 'https://example.com'}, {'native_manifest': '../native-source.json'},
                       {'native_manifest': '/tmp/native.json'}, {'native_manifest_sha256': '0'*64}):
            with self.subTest(change=change):
                p.write_text(old + '\n[source_view]\n' + '\n'.join(
                    k + ' = ' + json.dumps(v) for k, v in (opts | change).items()))
                with self.assertRaises(EnhancementError): load(self.fx.root, p.name)
        p.write_text(old + '\n[source_view]\nschema_version = 1\nmode = "public-specifications"')
        with self.assertRaises(EnhancementError): load(self.fx.root, p.name)

    def test_utf8_whitespace_endings_and_escaping(self):
        for ending in ('\n', '\r\n'):
            for final in ('', ending):
                raw = ('\t-- café λ <script>alert("x")</script> &amp; {{ /tmp/x' + ending +
                       'package Example is' + ending + 'end Example;' + final).encode()
                value, count = render(self.config, 'src/example.ads', raw)
                parsed = Text(value.decode())
                self.assertEqual(parsed.text.encode(), raw)
                self.assertEqual(parsed.lines, ['L1', 'L2', 'L3'])
                self.assertEqual(count, 3)
                self.assertNotIn(b'<script>', value)
        for raw in (b'\xff', b'a\rb', b'a\x00b'):
            with self.assertRaises(EnhancementError): render(self.config, 'src/x.ads', raw)

    def test_deterministic_idempotent_inventory(self):
        second = self.fx.root/'second'; shutil.copytree(self.fx.site, second)
        native = snapshot(self.config, self.fx.site)
        values, links, identity, _ = build(self.config, native, packages(self.config))
        result = enhance(self.config, self.fx.site); enhance(self.config, second)
        self.assertEqual(hashes(self.fx.site), hashes(second))
        before = hashes(self.fx.site); verify(self.config, self.fx.site); enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))
        self.assertEqual(result['source_pages'], len(identity['files']))
        self.assertEqual(result['source_links'], sum(map(len, links.values())))
        for name, value in values.items(): self.assertEqual((self.fx.site/name).read_bytes(), value)
        with self.assertRaises(EnhancementError): verify(self.fx.config, self.fx.site)

    def test_lexical_categories_and_exact_source_in_both_modes(self):
        source = ('\tPaCkAgE Café_λ is  \n\n'
                  '-- <script onload="x"> &amp; {{ }} /tmp/x \' "\n'
                  'S : String := "<script>"" & </script>";\n'
                  "C : Character := 'λ'; Q := Character'('A');\n"
                  "N := 16#CA_FE.F#E+2 + 1_000; A := S'Length;\n"
                  'end Café_λ;  ')
        for highlight in (False, True):
            for ending in ('\n', '\r\n'):
                for final in ('', ending):
                    text = source.replace('\n', ending) + final
                    config = replace(self.config, highlight=highlight)
                    raw = text.encode()
                    value, count = render(config, 'src/example.ads', raw)
                    parsed = Text(value.decode())
                    self.assertEqual(parsed.text, text)
                    self.assertEqual(count, 7)
                    self.assertEqual(parsed.lines, ['L'+str(i) for i in range(1, 8)])
                    self.assertEqual(''.join(t.text for t in tokenize(text)), text)
                    classes = set(re.findall(rb'class="ada-([a-z]+)"', value))
                    self.assertEqual(classes, {b'keyword', b'comment', b'string', b'character',
                                              b'number', b'attribute', b'operator'} if highlight else set())
                    self.assertNotIn(b'<script', value)
                    self.assertNotIn(b'ada-identifier', value)
                    if highlight:
                        for kind, token in (('keyword', 'PaCkAgE'), ('character', '&#x27;λ&#x27;'),
                                            ('attribute', '&#x27;Length'), ('number', '16#CA_FE.F#E+2')):
                            self.assertIn(f'<span class="ada-{kind}">{token}</span>'.encode(), value)
        for raw, count in ((b'', 0), (b'\n', 1), (b'\r\n\n', 2),
                           ('-- Unicode separators \u2028\u2029\v\f\n'.encode(), 1)):
            value, actual = render(self.config, 'src/empty.ads', raw)
            self.assertEqual(Text(value.decode()).text.encode(), raw)
            self.assertEqual(actual, count)

    def test_invalid_lexer_partitions_fail_closed(self):
        for tokens in ([Token('keyword', 'package', 1, 8)],
                       [Token('keyword', 'package', 0, 7), Token('plain', 'e', 6, 7)],
                       [Token('keyword', 'PACKAGE', 0, 7)], [],
                       [Token('keyword" onclick="x', 'package', 0, 7)]):
            with self.subTest(tokens=tokens), patch(
                    'ada_gnatdoc_enhancer.source_view.tokenize', return_value=tokens):
                with self.assertRaises(EnhancementError):
                    render(replace(self.config, highlight=True), 'src/x.ads', b'package')

    def test_palette_does_not_override_native_api_theme(self):
        # API pages also load source CSS for View source links. Palette variables
        # and page colors must therefore be scoped to source-view bodies only.
        css = asset('gnatdoc-source.css').decode()
        self.assertNotIn(':root', css)
        self.assertNotRegex(css, r'(?:^|\n)html\s*\{')
        self.assertIn('.source-view { color: var(--text); background: var(--page); }', css)
        self.assertIn('.source-code .source-line:target > span { color: inherit; }', css)

    def test_large_source_linear_pass_and_traversal_order(self):
        text = ('\t-- λ <>& {{ }}\r\nN := 16#CA_FE#;  \r\n' * 10000).encode()
        with patch('ada_gnatdoc_enhancer.source_view.tokenize', wraps=tokenize) as lexer:
            value, count = render(replace(self.config, highlight=True), 'src/large.ads', text)
        self.assertEqual(lexer.call_count, 1)
        self.assertEqual(count, 20000)
        self.assertEqual(Text(value.decode()).text.encode(), text)
        native = snapshot(self.config, self.fx.site); source = packages(self.config)
        before = {p.path: p.path.read_bytes() for p in source.values()}
        self.assertEqual(build(self.config, native, source), build(
            self.config, native, dict(reversed(list(source.items())))))
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_resealed_token_markup_and_resource_attacks(self):
        enhance(self.config, self.fx.site)
        path = next(p for p in (self.fx.site/'api/source').rglob('*.html')
                    if b'class="ada-keyword"' in p.read_bytes())
        original = path.read_bytes()
        token = re.search(rb'<span class="ada-keyword">[^<]+</span>', original)[0]
        line = original[original.index(b'<span class="source-line" id="L1">'):
                        original.index(b'<span class="source-line" id="L2">')]
        second = original[original.index(b'<span class="source-line" id="L2">'):
                          original.index(b'<span class="source-line" id="L3">')]
        mutations = [
            token.replace(b'</span>', b''),
            b'<span class="ada-comment">' + token + b'</span>',
            token.replace(b'ada-keyword', b'ada-string'),
            token.replace(b'>', b' onclick="alert(1)">', 1),
            token.replace(b'>', b' style="display:none">', 1),
            token.replace(b'</span>', b'X</span>'),
            b'<a href="https://evil.invalid/">' + token + b'</a>',
            b'<script>alert(1)</script>' + token,
            b'<img src="https://evil.invalid/x" onerror="alert(1)">' + token,
        ]
        for mutation in mutations:
            self.reseal(path, original.replace(token, mutation, 1))
            with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        for raw in (original.replace(line, b'', 1), original.replace(line, line+line, 1),
                    original.replace(line+second, second+line, 1),
                    original.replace(b'</head>', b'<link rel="stylesheet" href="extra.css"></head>'),
                    original.replace(b'</head>', b'<script src="extra.js"></script></head>')):
            self.reseal(path, raw)
            with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        path.write_bytes(original)
        for name in ('extra.css', 'extra.js'):
            extra = self.fx.site/'api'/name; self.reseal(extra, b'/* unauthorized */')
            with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
            extra.unlink()

    def reseal(self, path, raw):
        path.write_bytes(raw)
        mp = self.fx.site/'api/presentation.json'; data = json.loads(mp.read_text())
        data['output_sha256'][path.relative_to(self.fx.site).as_posix()] = digest(raw)
        mp.write_text(sorted_json(data))

    def test_modified_missing_duplicate_reordered_anchors_resealed(self):
        enhance(self.config, self.fx.site)
        path = next((self.fx.site/'api/source').rglob('*.html')); original = path.read_bytes()
        for raw in (original + b' ', original.replace(b'id="L1"', b'id="L2"', 1),
                    original.replace(b'id="L1"', b'id="L99"', 1),
                    original.replace(b'id="L1"', b'id="TEMP"', 1).replace(
                        b'id="L2"', b'id="L1"', 1).replace(b'id="TEMP"', b'id="L2"', 1),
                    original.replace(b'package', b'PACKAGE', 1)):
            with self.subTest(raw=raw[:30]):
                self.reseal(path, raw)
                with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        path.unlink()
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_forged_source_ownership_hash_line_and_destination(self):
        enhance(self.config, self.fx.site)
        mp = self.fx.site/'api/presentation.json'; original = mp.read_bytes()
        for field, value in [('source','../secret.ads'), ('source','/etc/passwd'),
                             ('source','src/private.ads'), ('sha256','0'*64),
                             ('page','api/source/other.ads.html')]:
            data = json.loads(original); data['source_view']['files'][0][field] = value
            mp.write_text(sorted_json(data))
            with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        data = json.loads(original); data['source_view']['files'][0]['declarations'][0]['line'] += 1
        mp.write_text(sorted_json(data))
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)
        mp.write_bytes(original)
        import re
        # Package links legitimately target L1. Directory iteration order must
        # not decide whether this negative control actually mutates a link.
        destination = rb'\.html#L(?:[2-9][0-9]*|1[0-9]+)"'
        page = next(p for p in sorted((self.fx.site/'api').glob('*.html'))
                    if re.search(destination, p.read_bytes()))
        raw = re.sub(destination, b'.html#L1"', page.read_bytes(), count=1)
        self.assertNotEqual(page.read_bytes(), raw)
        self.reseal(page, raw)
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_original_manifest_cannot_swap_native_overload_anchors(self):
        enhance(self.config, self.fx.site)
        mp = self.fx.site/'api/presentation.json'; data = json.loads(mp.read_text())
        originals = data['original_api_html']
        import re
        for name, text in originals.items():
            anchors = re.findall(r'<h4 id="?([a-f0-9]{64})', text)
            if len(anchors) >= 2:
                originals[name] = text.replace(anchors[0], 'PLACEHOLDER').replace(
                    anchors[1], anchors[0]).replace('PLACEHOLDER', anchors[1])
                break
        else: self.fail('fixture lacks distinct anchors')
        mp.write_text(sorted_json(data))
        with self.assertRaisesRegex(EnhancementError, 'independently pinned'):
            verify(self.config, self.fx.site)

    def test_resealed_unrelated_links_and_swapped_lines_rejected(self):
        import re
        enhance(self.config, self.fx.site)
        page = next(p for p in (self.fx.site/'api').glob('*.html')
                    if p.read_text().count('View source') >= 3)
        original = page.read_bytes()
        hrefs = re.findall(rb'href="(source/[^\"]+)"', original)
        self.assertGreaterEqual(len(hrefs), 3)
        for raw in (original.replace(hrefs[1], hrefs[2], 1),
                    original.replace(hrefs[1], b'source/src/hidden.ads.html#L1', 1),
                    original.replace(hrefs[1], b'PLACEHOLDER', 1).replace(
                        hrefs[2], hrefs[1], 1).replace(b'PLACEHOLDER', hrefs[2], 1)):
            self.reseal(page, raw)
            with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_source_hash_resealed_in_publication_is_not_authority(self):
        enhance(self.config, self.fx.site)
        path = next((self.fx.root/'src').glob('*.ads'))
        path.write_bytes(path.read_bytes() + b'\n-- malicious substitution\n')
        mp = self.fx.site/'api/presentation.json'; data = json.loads(mp.read_text())
        data['source_sha256'][path.relative_to(self.fx.root).as_posix()] = digest(path.read_bytes())
        for record in data['source_view']['files']:
            if record['source'] == path.relative_to(self.fx.root).as_posix():
                record['sha256'] = digest(path.read_bytes())
                page, _ = render(self.config, record['source'], path.read_bytes())
                (self.fx.site/record['page']).write_bytes(page)
                data['output_sha256'][record['page']] = digest(page)
        mp.write_text(sorted_json(data))
        with self.assertRaisesRegex(EnhancementError, 'independently pinned'):
            verify(self.config, self.fx.site)

    def test_complete_private_section_is_deliberately_visible(self):
        path = next((self.fx.root/'src').glob('*.ads'))
        text = path.read_text()
        # A standalone renderer must not redact any text, even markup-like text
        # or strings which publication checks reject outside exact source views.
        raw = (text + '\nprivate\n-- <script> &amp; javascript: /tmp/x {{ }}\n').encode()
        page, _ = render(self.config, path.name, raw)
        self.assertEqual(Text(page.decode()).text.encode(), raw)

    def test_pipeline_line_endings_hostile_comments_and_no_final_newline(self):
        for ending in (b'\n', b'\r\n'):
            for final in (False, True):
                fx = Fixture()
                try:
                    path = next((fx.root/'src').glob('*.ads'))
                    raw = (b'-- <script>alert("x")</script> &amp; javascript: {{ /tmp/x\n' +
                           path.read_bytes().rstrip(b'\r\n')).replace(b'\n', ending)
                    if final: raw += ending
                    path.write_bytes(raw)
                    config = enable(fx.config, fx.site)
                    enhance(config, fx.site); verify(config, fx.site)
                    page = fx.site/'api/source'/path.relative_to(fx.root).as_posix()
                    page = Path(str(page)+'.html')
                    self.assertEqual(Text(page.read_text()).text.encode(), raw)
                finally: fx.cleanup()

    def test_traversal_missing_substitution_and_symlinks_fail_atomically(self):
        for name in ('../x.ads', '/etc/passwd', 'src/../../x', 'src/x%2eads'):
            with self.assertRaises(EnhancementError): owned(self.fx.root, name)
        path = next((self.fx.root/'src').glob('*.ads')); raw = path.read_bytes()
        before = hashes(self.fx.site)
        path.unlink()
        with self.assertRaises(EnhancementError): enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site)); path.write_bytes(raw)
        external = self.fx.root/'replacement.ads'; external.write_bytes(raw)
        path.unlink(); path.symlink_to(external)
        with self.assertRaises(EnhancementError): enhance(self.config, self.fx.site)
        path.unlink(); path.write_bytes(raw)
        (self.fx.root/'src/escape').symlink_to(self.fx.root, target_is_directory=True)
        with self.assertRaises(EnhancementError): enhance(self.config, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))

    def test_substituted_source_rejected_after_publication(self):
        enhance(self.config, self.fx.site)
        path = next((self.fx.root/'src').glob('*.ads'))
        path.write_bytes(path.read_bytes() + b'\n-- substituted\n')
        with self.assertRaises(EnhancementError): verify(self.config, self.fx.site)

    def test_private_units_bodies_and_duplicate_ownership(self):
        (self.fx.root/'src/hidden.ads').write_text('private package Hidden is end Hidden;')
        (self.fx.root/'src/body.adb').write_text('package body Hidden is end Hidden;')
        self.assertNotIn('hidden', packages(self.config))
        enhance(self.config, self.fx.site)
        self.assertFalse(list((self.fx.site/'api/source').rglob('*hidden*')))
        with self.assertRaises(EnhancementError):
            packages(replace(self.config, sources=('src', 'src')))


class RealSourceLines(unittest.TestCase):
    def test_mel_actual_token_not_leading_documentation(self):
        root = Path(__file__).parent/'real-fixtures/search-mel/authority'
        pkg = packages(load(root.resolve(), 'docs/gnatdoc-enhance.toml'))['ams.mel.ir.image']
        declarations = {d.name: d for d in pkg.declarations}
        self.assertEqual(declarations['Navigation_Report'].source_line, 663)
        self.assertEqual(declarations['Submit_Navigation_Report'].source_line, 775)
        self.assertEqual(declarations['Navigation_Report'].line, 622)


class SourceCompatibility(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)
        spec = importlib.util.spec_from_file_location('source_view_qualification',
            Path(__file__).resolve().parents[1]/'scripts/qualify_source_view.py')
        self.audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.audit)
        self.old = self.fx.root/'old'; self.new = self.fx.root/'new'
        for root in (self.old, self.new):
            (root/'api/source/src').mkdir(parents=True)
            (root/'api/gnatdoc-source.css').write_bytes(b'/* source CSS */')
            (root/'api/gnatdoc-search.js').write_bytes(b'/* unchanged search */')
            (root/'api/source/src/x.ads.html').write_bytes(b'<code>package X;</code>')
            (root/'api/presentation.json').write_text(sorted_json(dict(
                source_view={'schema_version': 1, 'files': []}, output_sha256=hashes(root))))

    def seal(self):
        path = self.new/'api/presentation.json'; data = json.loads(path.read_text())
        data['output_sha256'] = {n: sha for n, sha in hashes(self.new).items()
                                 if n != 'api/presentation.json'}
        path.write_text(sorted_json(data))

    def test_classified_css_and_token_only_deltas(self):
        (self.new/'api/gnatdoc-source.css').write_bytes(b'/* new palette */')
        self.seal(); self.audit.compare_source_outputs(self.old, self.new, False)
        (self.new/'api/source/src/x.ads.html').write_bytes(
            b'<code><span class="ada-keyword">package</span> X;</code>')
        self.seal(); self.audit.compare_source_outputs(self.old, self.new, True)
        with self.assertRaises(EnhancementError):
            self.audit.compare_source_outputs(self.old, self.new, False)

    def test_rehashed_unrelated_and_concealed_text_deltas_rejected(self):
        for name, raw in (
                ('api/gnatdoc-search.js', b'/* changed search */'),
                ('api/source/src/x.ads.html', b'<code><span class="ada-keyword">PACKAGE</span> X;</code>'),
                ('api/source/src/x.ads.html', b'<code><span class="ada-keyword" onclick="x">package</span> X;</code>'),
                ('api/extra.css', b'/* extra */')):
            path = self.new/name; before = path.read_bytes() if path.exists() else None
            path.write_bytes(raw); self.seal()
            with self.assertRaises(EnhancementError):
                self.audit.compare_source_outputs(self.old, self.new, True)
            if before is None: path.unlink()
            else: path.write_bytes(before)