"""Serialized title boundaries must not depend on HTMLParser RCDATA callbacks."""
import unittest

from ada_gnatdoc_enhancer import metadata
from ada_gnatdoc_enhancer.errors import EnhancementError

PREFIX = '<!doctype html><html lang="en"><head><meta charset="utf-8">'
SUFFIX = '</head><body>Body</body></html>'


class SerializedTitles(unittest.TestCase):
    def boundary(self, serialized):
        return metadata.serialized_title(serialized, 0, 'test title')

    def test_raw_boundary_accepts_escaped_unicode_and_preserves_serialization(self):
        raw = 'Документация &amp; &lt;Ada&gt; — 日本語'
        serialized = '<title>' + raw + '</title>'
        content, decoded, closing = self.boundary(serialized)
        self.assertEqual(content, raw)
        self.assertEqual(decoded, 'Документация & <Ada> — 日本語')
        self.assertEqual(serialized[closing:], '</title>')
        self.assertEqual(metadata.check_document(PREFIX + serialized + SUFFIX, 'author.html'), decoded)

    def test_raw_boundary_rejects_literal_markup_without_tokenizing_it(self):
        for raw in ('<title>Nested', 'T<!-- comment -->', 'T<b>bold</b>', 'T<', 'T</ title>',
                    'T<?instruction?>', 'T<![CDATA[x]]>', 'T</title extra>', 'T</title/>'):
            with self.subTest(raw=raw), self.assertRaises(EnhancementError):
                self.boundary('<title>' + raw + '</title>')

    def test_raw_boundary_rejects_unfinished_closure(self):
        for serialized in ('<title>T', '<title>T</title', '<title>T</title ', '<title>T</title!>'):
            with self.subTest(serialized=serialized), self.assertRaises(EnhancementError):
                self.boundary(serialized)

    def test_escaped_markup_looking_text_is_not_markup(self):
        for raw, decoded in (('&lt;title&gt;T', '<title>T'),
                             ('T&lt;!-- comment --&gt;', 'T<!-- comment -->'),
                             ('&#60;Ada&#62;', '<Ada>'), ('&amp;lt;Ada&amp;gt;', '&lt;Ada&gt;')):
            with self.subTest(raw=raw):
                self.assertEqual(self.boundary('<title>' + raw + '</title>')[1], decoded)
                implicit = '<html lang="en"><meta charset="utf-8"><title>' + raw + '</title><body>B'
                self.assertEqual(metadata.check_document(implicit, 'implicit.html'), decoded)

    def test_actual_document_rejects_raw_markup_and_malformed_closures(self):
        for title in ('<title>T<title>N</title>', '<title>T<!--comment--></title>',
                      '<title>T<b>B</b></title>', '<title>T</title extra>', '<title>T</title/>'):
            with self.subTest(title=title), self.assertRaises(EnhancementError):
                metadata.check_document(PREFIX + title + SUFFIX, 'author.html')

    def test_numeric_controls_cannot_disappear_in_rcdata(self):
        for raw in ('&#0;', '&#x0;', '&#13;', '&#x202e;', '&#x200b;', '&#x110000;'):
            with self.subTest(raw=raw), self.assertRaises(EnhancementError):
                metadata.check_document(PREFIX + '<title>T' + raw + 'P</title>' + SUFFIX, 'author.html')

    def test_offsets_and_case_are_not_guessed_from_decoded_text(self):
        text = '<!-- <title>not a document title</title> -->\n' + PREFIX
        title = '<TITLE >A &lt;B&gt;</TiTlE >'
        self.assertEqual(metadata.check_document(text + title + SUFFIX, 'author.html'), 'A <B>')
        start = len(text)
        raw, decoded, closing = metadata.serialized_title(text + title + SUFFIX, start, 'author')
        self.assertEqual((raw, decoded), ('A &lt;B&gt;', 'A <B>'))
        self.assertTrue((text + title + SUFFIX)[closing:].startswith('</TiTlE >'))