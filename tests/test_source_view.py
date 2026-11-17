"""Source views: byte fidelity, independent identity and resealing attacks."""
from dataclasses import replace
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import unittest

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.source_view import build, owned, render
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
        if tag == 'span': self.lines.append(dict(attrs)['id'])

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