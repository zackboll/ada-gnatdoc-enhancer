"""Negative-first GNATDOC-010R document-contract and browser regressions."""
import html
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.metadata import check_document, check_native_input, package_title
from ada_gnatdoc_enhancer.pipeline import enhance
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json

TESTS = Path(__file__).resolve().parent
GOOD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>T — P</title></head><body><h1>T</h1></body></html>')
UNSAFE = ('\t', '\r', '\n', '\x00', '\x1f', '\x7f', '\u202e', '\u2066',
          '\u200b', '\ufeff', '\u00a0', '\u2028', '\u2029')


class MalformedTitles(unittest.TestCase):
    def test_second_unclosed_title(self):
        with self.assertRaises(EnhancementError):
            check_document(GOOD.replace('</head>', '<title></head>'), 'author.html')

    def test_nested_title(self):
        with self.assertRaises(EnhancementError):
            check_document(GOOD.replace('<title>T — P', '<title><title>T — P'), 'author.html')

    def test_unmatched_title_closure(self):
        with self.assertRaises(EnhancementError):
            check_document(GOOD.replace('</head>', '</title></head>'), 'author.html')

    def test_malformed_head_order(self):
        for text in (GOOD.replace('<head>', '').replace('</head>', '<head></head>'),
                     GOOD.replace('</head>', ''),
                     GOOD.replace('<head>', '</head><head>'),
                     GOOD.replace('<html lang="en"><head>', '<head><html lang="en">'),
                     GOOD.replace('<head>', '<head/>')):
            with self.subTest(text=text), self.assertRaises(EnhancementError):
                check_document(text, 'api/p.html', generated=True)

    def test_implicit_authored_head_kept(self):
        text = GOOD.replace('<head>', '').replace('</head>', '')
        self.assertEqual(check_document(text, 'author.html'), 'T — P')

    def test_title_comment_not_misread_as_browser_text(self):
        with self.assertRaises(EnhancementError):
            check_document(GOOD.replace('T — P', 'T<!-- hidden --> — P'), 'author.html')

    def test_metadata_after_root_closure(self):
        text = '<html lang="en"></html><meta charset="utf-8"><title>T</title>'
        with self.assertRaises(EnhancementError):
            check_document(text, 'author.html')


class TitleSafety(unittest.TestCase):
    def test_decoded_controls_and_separators(self):
        for value in UNSAFE:
            for encoded in (value, '&#' + str(ord(value)) + ';'):
                with self.subTest(value=repr(encoded)), self.assertRaisesRegex(
                        EnhancementError, 'unsafe document title'):
                    check_document(GOOD.replace('T — P', 'T' + encoded + 'P'), 'author.html')

    def test_composed_title_boundary(self):
        title = package_title('A' * 300, 'B' * 300)
        self.assertEqual(len(title), 603)
        self.assertEqual(check_document(GOOD.replace('T — P', title), 'author.html'), title)
        with self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
            check_document(GOOD.replace('T — P', title + 'X'), 'author.html')

    def test_legitimate_author_title_not_rewritten(self):
        title = 'Документация & <Ada> — 日本語'
        self.assertEqual(check_document(GOOD.replace('T — P', html.escape(title)), 'author.html'), title)

    def stage(self, name, authored=False):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)/name
        shutil.copytree(TESTS/('authored-fixtures' if authored else 'fixtures')/name, root)
        return root, load(root, 'project.toml'), root/('native' if authored else '_site')

    def test_html_portal_and_guide_safety(self):
        for relative in ('docs/index.html', 'docs/guides/architecture.html'):
            root, config, site = self.stage('mel')
            path = root/relative
            path.write_text(path.read_text().replace('</title>', '\u202e</title>'))
            before = hashes(site)
            with self.subTest(path=relative), self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
                enhance(config, site)
            self.assertEqual(hashes(site), before)

    def test_authored_html_safety(self):
        root, config, site = self.stage('mel', True)
        data = json.loads((root/'authored.json').read_text())
        path = root/data['guides'][0]['source']
        path.write_text(path.read_text().replace('</title>', '&#8238;</title>'))
        data['inputs'] = {p: digest((root/p).read_bytes()) for p in data['inputs']}
        payload = sorted_json(data).encode(); (root/'authored.json').write_bytes(payload)
        before = hashes(site)
        with self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
            enhance(replace(config, guide_sha256=digest(payload)), site)
        self.assertEqual(hashes(site), before)

    def test_authored_markdown_safety(self):
        root, config, site = self.stage('imgproc', True)
        data = json.loads((root/'authored.json').read_text())
        data['title_suffix'] += '\u200b'
        payload = sorted_json(data).encode(); (root/'authored.json').write_bytes(payload)
        before = hashes(site)
        with self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
            enhance(replace(config, guide_sha256=digest(payload)), site)
        self.assertEqual(hashes(site), before)

    def test_generated_unsafe_title_rejected_independently(self):
        with self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
            check_document(GOOD.replace('T — P', 'T\u202e — P'), 'api/p.html', generated=True)

    def test_markdown_mode_portal_safety(self):
        from test_page_metadata import MarkdownGuides
        fixture = MarkdownGuides(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        path = fixture.root/'docs/index.html'
        path.write_text(path.read_text().replace('</title>', '\u2066</title>'))
        with self.assertRaisesRegex(EnhancementError, 'unsafe document title'):
            enhance(fixture.config, fixture.site)

    def test_markdown_mode_unsafe_component(self):
        from test_page_metadata import MarkdownGuides
        fixture = MarkdownGuides(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        path = fixture.root/'docs/site-map.json'
        data = json.loads(path.read_text())
        data['guides'][0]['label'] += '\u200b'
        path.write_text(json.dumps(data))
        source = fixture.root/'docs/guides/getting-started.md'
        source.write_text(source.read_text().replace('# Getting started', '# Getting started\u200b'))
        with self.assertRaisesRegex(EnhancementError, 'untrusted'):
            enhance(fixture.config, fixture.site)


class MetadataInventory(unittest.TestCase):
    def test_generated_extra_meta_in_head_and_body(self):
        for closing in ('</head>', '</body>'):
            with self.subTest(closing=closing), self.assertRaisesRegex(EnhancementError, 'metadata'):
                check_document(GOOD.replace(closing, '<meta name="robots" content="noindex">' + closing),
                               'api/p.html', generated=True)

    def test_malformed_charset_attributes(self):
        for attributes in ('charset="utf-8" charset="utf-8"', 'charset="utf-8" name="x"', 'charset'):
            with self.subTest(attributes=attributes), self.assertRaises(EnhancementError):
                check_document(GOOD.replace('charset="utf-8"', attributes), 'api/p.html', generated=True)

    def test_native_extra_metadata_rejected(self):
        original = ('<!DOCTYPE html>\n<html class=main>\n<link rel=stylesheet href=gnatdoc.css>'
                    '<body class=content><h1>P</h1>')
        with self.assertRaisesRegex(EnhancementError, 'metadata'):
            check_native_input(original + '<meta name="robots" content="noindex">', 'api/p.html')

    def test_authored_metadata_preserved(self):
        text = GOOD.replace('</head>', '<meta name="description" content="Author owned"></head>')
        self.assertEqual(check_document(text, 'author.html'), 'T — P')

    def test_viewport_disabled_policy(self):
        text = GOOD.replace('</head>', '<meta name="viewport" content="width=device-width, initial-scale=1"></head>')
        with self.assertRaisesRegex(EnhancementError, 'metadata'):
            check_document(text, 'api/p.html', generated=True, viewport=False)

    def test_viewport_enabled_policy(self):
        text = GOOD.replace('</head>', '<meta name="viewport" content="width=device-width, initial-scale=1"></head>')
        self.assertEqual(check_document(text, 'api/p.html', generated=True, viewport=True), 'T — P')
        for bad in (GOOD, text.replace('width=device-width', 'width=500'),
                    text.replace('</head>', '<meta name="viewport" content="width=device-width, initial-scale=1"></head>')):
            with self.subTest(text=bad), self.assertRaises(EnhancementError):
                check_document(bad, 'api/p.html', generated=True, viewport=True)


class BrowserMetadataAssertion(unittest.TestCase):
    def helper(self):
        from ada_gnatdoc_enhancer.browser_metadata import assert_document_metadata
        return assert_document_metadata

    def test_browser_rejects_charset_language_and_title_mismatch(self):
        assertion = self.helper()
        class Document:
            def __init__(self, state): self.state = state
            def wait_for_function(self, expression, *, arg):
                if self.state != arg: raise AssertionError('document metadata mismatch')
        assertion(Document(['T', 'en', 'UTF-8']), 'T', 'en')
        for state in (['Wrong', 'en', 'UTF-8'], ['T', 'fr', 'UTF-8'], ['T', 'en', 'windows-1252']):
            with self.subTest(state=state), self.assertRaises(AssertionError):
                assertion(Document(state), 'T', 'en')