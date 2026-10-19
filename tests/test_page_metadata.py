"""GNATDOC-010 HTML document metadata: titles, language and charset.

Positive cases use the authentic GNATdoc 26.0.0 Geometry pages, the authentic
authored fixtures and the synthetic profiles. Every adversarial mutation runs
through the enhancer's own enhance/verify path unless it names a helper.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.metadata import (Document, check_document, check_native_input,
                                           guide_title, index_title, label, native_document,
                                           package_title, strip_native_document)
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import MANIFEST, document_titles, enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native
from ada_gnatdoc_enhancer.theme import NATIVE_LINK
from ada_gnatdoc_enhancer.util import digest, sorted_json
from ada_gnatdoc_enhancer.validation import validate_files

TESTS = Path(__file__).resolve().parent
REAL = TESTS/'real-fixtures/geometry'
SPEC = json.loads((REAL/'input.json').read_text())
PROLOGUE = '<!DOCTYPE html>\n<html class=main>\n' + NATIVE_LINK
TITLE = re.compile(r'<title>(.*?)</title>', re.S)


def geometry(base: Path, configuration: str = SPEC['configuration']) -> tuple[Path, object, Path]:
    """Stage the authentic Geometry inputs exactly as the qualification runner does."""
    root = base/'geometry'
    shutil.copytree(REAL/'source', root)
    for name in SPEC['public_sources']:
        target = root/'qualification-public'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root/name, target)
    (root/'qualification.toml').write_text(configuration)
    shutil.copytree(REAL/'pristine', root/'_site')
    return root, load(root, 'qualification.toml'), root/'_site'


def pages(site: Path) -> dict[str, str]:
    return {p.relative_to(site).as_posix(): p.read_text(encoding='utf-8')
            for p in sorted(site.rglob('*.html'))}


class TitleComponents(unittest.TestCase):
    def test_titles_from_verified_identities(self):
        self.assertEqual(package_title('OpenCV.Features.ORB', 'OpenCV Features Ada'),
                         'OpenCV.Features.ORB — OpenCV Features Ada')
        self.assertEqual(index_title('OpenCV Features Ada'), 'API Reference — OpenCV Features Ada')
        self.assertEqual(guide_title('ORB feature extraction', 'OpenCV Features Ada'),
                         'ORB feature extraction — OpenCV Features Ada')
        self.assertEqual(label('Ada — Документация & <tools>', 'project'), 'Ada — Документация & <tools>')

    def test_untrusted_components_rejected(self):
        for value in ('', ' leading', 'trailing ', 'two\nlines', 'tab\there', 'nul\x00',
                      'bidi‮override', 'zero​width', 'no break', 'x' * 301, None, 3):
            with self.subTest(value=value), self.assertRaisesRegex(EnhancementError, 'untrusted'):
                package_title('OpenCV.Core', value)


class NativeLayout(unittest.TestCase):
    def test_authentic_and_synthetic_gnatdoc_pages_are_accepted(self):
        for path in sorted((REAL/'pristine/api').glob('*.html')):
            check_native_input(path.read_text(), path.name)
        for path in sorted((TESTS/'fixtures/core/_site/api').glob('*.html')):
            check_native_input(path.read_text(), path.name)

    def test_titled_conflicting_and_unknown_layouts_are_rejected(self):
        page = PROLOGUE + '<body class=content><h1>P</h1>'
        for variant, reason in (
                (page.replace('<html class=main>', '<html class=main lang="en">'), 'layout'),
                (page.replace(NATIVE_LINK, '<head><title>P</title></head>' + NATIVE_LINK), 'layout'),
                (page.replace(NATIVE_LINK, '<title>P</title>' + NATIVE_LINK), 'layout'),
                (page + '<title>Conflict</title>', 'metadata'),
                (page + '<meta charset="latin1">', 'metadata'),
                (page + '<head></head>', 'metadata'),
                (page + '<html>', 'metadata'),
                (page + '<body class=content>', 'metadata'),
                (page.replace('<!DOCTYPE html>\n', ''), 'layout'),
                (page.replace('<html class=main>', '<html class=main id=x>'), 'layout'),
                (page.replace('<body class=content>', '<body>'), 'layout'),
                (page.replace('<body class=content>', '<body class=other>'), 'layout'),
                (page.replace(NATIVE_LINK, NATIVE_LINK + '<script src=x.js></script>'), 'layout')):
            with self.subTest(variant=variant[:90]), self.assertRaisesRegex(EnhancementError, reason):
                check_native_input(variant, 'api/page.html')

    def test_bounded_insertion_and_exact_removal(self):
        original = PROLOGUE + '<body class=content><h1>A &amp; B</h1>'
        result = native_document(original, NATIVE_LINK, 'A <B> & "C" — P', 'api/p.html')
        self.assertEqual(result, '<!DOCTYPE html>\n<html class=main lang="en">\n<head><meta charset="utf-8">'
                         '<title>A &lt;B&gt; &amp; &quot;C&quot; — P</title>' + NATIVE_LINK +
                         '</head><body class=content><h1>A &amp; B</h1>')
        self.assertEqual(Document(result).titles, ['A <B> & "C" — P'])
        self.assertEqual(strip_native_document(result, 'A <B> & "C" — P', 'api/p.html'), original)
        with self.assertRaisesRegex(EnhancementError, 'unexpected enhanced document head'):
            native_document(original.replace(NATIVE_LINK, NATIVE_LINK + '<link rel=stylesheet href=x.css>'),
                            NATIVE_LINK, 'T', 'api/p.html')
        for mutated in (result.replace('</title>', '</title><title>X</title>'),
                        result.replace(' lang="en"', ''),
                        result.replace('</head>', ''),
                        result.replace('<title>A', '<title>Z')):
            with self.subTest(mutated=mutated[:120]), self.assertRaises(EnhancementError):
                strip_native_document(mutated, 'A <B> & "C" — P', 'api/p.html')


class DocumentContract(unittest.TestCase):
    GOOD = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>T — P</title>'
            '</head><body><h1>T</h1></body></html>')

    def test_valid_explicit_and_implicit_heads(self):
        self.assertEqual(check_document(self.GOOD, 'g.html', title='T — P', generated=True), 'T — P')
        implicit = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<title>Landing</title>\n<body><h1>L</h1>'
        self.assertEqual(check_document(implicit, 'index.html'), 'Landing')

    def test_metadata_mutations_rejected(self):
        for mutated, reason in (
                (self.GOOD.replace('<title>T — P</title>', ''), 'missing or duplicate document title'),
                (self.GOOD.replace('T — P', ''), 'empty or malformed document title'),
                (self.GOOD.replace('T — P', '   '), 'empty or malformed document title'),
                (self.GOOD.replace('</title>', '</title><title>Two</title>'), 'duplicate document title'),
                (self.GOOD.replace('<h1>', '<title>Late</title><h1>'), 'duplicate document title'),
                (self.GOOD.replace('<title>T — P</title></head><body>', '</head><body><title>T — P</title>'),
                 'outside the head'),
                (self.GOOD.replace(' lang="en"', ''), 'document language'),
                (self.GOOD.replace('lang="en"', 'lang="en" lang="fr"'), 'document language'),
                (self.GOOD.replace('lang="en"', 'lang="en us"'), 'document language'),
                (self.GOOD.replace('<head>', '<head></head><head>'), 'duplicate document head'),
                (self.GOOD + '<html lang="en">', 'document root'),
                (self.GOOD.replace('<meta charset="utf-8">', ''), 'charset'),
                (self.GOOD.replace('utf-8', 'iso-8859-1'), 'charset'),
                (self.GOOD.replace('</head>', '<meta charset="utf-8"></head>'), 'charset'),
                (self.GOOD.replace('<meta charset="utf-8">', '').replace('<h1>', '<meta charset="utf-8"><h1>'),
                 'outside the head')):
            with self.subTest(reason=reason, mutated=mutated[:100]):
                with self.assertRaisesRegex(EnhancementError, reason):
                    check_document(mutated, 'g.html')

    def test_generated_pages_need_exact_identity_head_and_english(self):
        with self.assertRaisesRegex(EnhancementError, 'verified identity'):
            check_document(self.GOOD, 'api/p.html', title='Other — P', generated=True)
        with self.assertRaisesRegex(EnhancementError, 'lang="en"'):
            check_document(self.GOOD.replace('lang="en"', 'lang="fr"'), 'api/p.html', generated=True)
        implicit = self.GOOD.replace('<head>', '').replace('</head>', '')
        with self.assertRaisesRegex(EnhancementError, 'head'):
            check_document(implicit, 'api/p.html', generated=True)


class AuthenticGeometry(unittest.TestCase):
    """Complete authentic GNATdoc 26.0.0 Geometry site through enhance/verify."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='gnatdoc010-')
        cls.root, cls.config, cls.site = geometry(Path(cls.temp.name))
        cls.before = identities(cls.site)
        enhance(cls.config, cls.site)
        cls.hashes = hashes(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def copy(self):
        temp = tempfile.TemporaryDirectory(prefix='gnatdoc010-mutation-')
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)/'geometry'
        shutil.copytree(self.root, root)
        return root, load(root, 'qualification.toml'), root/'_site'

    def test_every_api_page_has_verified_metadata(self):
        titles = {'api/index.html': 'API Reference — opencv_geometry_ada'}
        for path in (REAL/'pristine/api').glob('*.html'):
            heading = re.search(r'<h1>([^<]+)</h1>', path.read_text())
            if heading:
                titles['api/' + path.name] = heading[1] + ' — opencv_geometry_ada'
        published = pages(self.site)
        self.assertEqual(set(published), set(titles))
        for name, text in published.items():
            with self.subTest(page=name):
                self.assertEqual(TITLE.findall(text), [html.escape(titles[name])])
                self.assertEqual(check_document(text, name, title=titles[name], generated=True), titles[name])
                self.assertTrue(text.startswith('<!DOCTYPE html>\n<html class=main lang="en">\n<head>'
                                                '<meta charset="utf-8"><title>'))
                self.assertEqual(text.count(NATIVE_LINK), 1)
                self.assertEqual(text.count('<head>') + text.count('</head>'), 2)
        self.assertEqual((self.site/'api/gnatdoc.css').read_bytes(), (REAL/'pristine/api/gnatdoc.css').read_bytes())

    def test_titles_come_from_source_reconciled_packages_not_filenames(self):
        published = pages(self.site)
        for name, text in published.items():
            self.assertNotIn(Path(name).stem, Document(text).titles[0])

    def test_native_identities_are_preserved_and_metadata_accounted(self):
        for config in (self.config, None):
            with self.subTest(config=bool(config)):
                result = preserve_native(self.before, self.site, config=config)
                self.assertEqual((result['packages'], result['declarations'], result['status']),
                                 (2, 130, 'preserved'))
        after = identities(self.site)
        for name, old in self.before.items():
            self.assertEqual(after[name]['visible_text_sha256'] if name != 'api/index.html' else 0,
                             old['visible_text_sha256'] if name != 'api/index.html' else 0)
            self.assertEqual(after[name]['declarations'], old['declarations'])
            self.assertEqual(after[name]['signatures'], old['signatures'])

    def test_preservation_rejects_unauthorized_or_inconsistent_titles(self):
        target = next(p for p in self.site.glob('api/[0-9a-f]*.html'))
        other = next(p for p in self.site.glob('api/[0-9a-f]*.html') if p != target)
        cases = {
            'wrong package': lambda t: t.replace('<title>' + Document(t).titles[0].split(' — ')[0],
                                                 '<title>' + Document(other.read_text()).titles[0].split(' — ')[0], 1),
            'other project': lambda t: t.replace(' — opencv_geometry_ada</title>', ' — Invented</title>', 1),
            'duplicate title': lambda t: t.replace('</title>', '</title><title>X</title>', 1),
            'missing lang': lambda t: t.replace(' lang="en"', '', 1),
            'wrong lang': lambda t: t.replace('lang="en"', 'lang="fr"', 1),
            'second charset': lambda t: t.replace('</head>', '<meta charset="utf-8"></head>', 1)}
        for label_, mutate in cases.items():
            with self.subTest(case=label_):
                root, config, site = self.copy()
                page = site/target.relative_to(self.site)
                page.write_text(mutate(page.read_text()))
                with self.assertRaises(ValueError):
                    preserve_native(self.before, site, config=config)
        root, config, site = self.copy()
        with self.assertRaisesRegex(ValueError, 'another project'):
            preserve_native(self.before, site, config=replace(config, project='Other project'))

    def test_verification_rejects_every_metadata_and_native_mutation(self):
        page_name = next(p.relative_to(self.site).as_posix() for p in self.site.glob('api/[0-9a-f]*.html')
                         if 'Subdiv2D</h1>' not in p.read_text())
        other_title = Document((self.site/next(p.relative_to(self.site).as_posix() for p in
                                self.site.glob('api/[0-9a-f]*.html')
                                if p.relative_to(self.site).as_posix() != page_name)).read_text()).titles[0]
        anchor = re.search(r'<h4 id=([0-9a-f]{64})>', (self.site/page_name).read_text())[1]

        def edit(path, transform):
            def apply(site, root):
                target = site/path
                target.write_text(transform(target.read_text()))
            return apply

        title = lambda t: Document(t).titles[0]
        mutations = {
            'missing generated title': edit(page_name, lambda t: t.replace('<title>' + html.escape(title(t)) + '</title>', '')),
            'empty title': edit(page_name, lambda t: t.replace(html.escape(title(t)) + '</title>', '</title>')),
            'duplicate title': edit(page_name, lambda t: t.replace('</title>', '</title><title>Copy</title>', 1)),
            'wrong package title': edit(page_name, lambda t: t.replace(html.escape(title(t)), html.escape(other_title), 1)),
            'conflicting index title': edit('api/index.html', lambda t: t.replace('API Reference — ', 'Home — ', 1)),
            'missing language': edit(page_name, lambda t: t.replace(' lang="en"', '', 1)),
            'wrong language': edit(page_name, lambda t: t.replace('lang="en"', 'lang="fr"', 1)),
            'conflicting charset': edit(page_name, lambda t: t.replace('</head>', '<meta charset="iso-8859-1"></head>', 1)),
            'duplicate head': edit(page_name, lambda t: t.replace('<head>', '<head></head><head>', 1)),
            'changed native h1': edit(page_name, lambda t: t.replace('<h1>', '<h1>X', 1)),
            'changed native h4': edit(page_name, lambda t: t.replace('<h4 id=' + anchor + '>', '<h4 id=' + anchor + '>X', 1)),
            'changed native anchor': edit(page_name, lambda t: t.replace(anchor, '0' * 64)),
            'modified declaration code': edit(page_name, lambda t: t.replace('<code>', '<code>-- injected\n', 1)),
            'extra executable script': edit(page_name, lambda t: t.replace('</head>', '<script src="gnatdoc-navigation.js" defer></script></head>', 1)),
            'injected external URL': edit(page_name, lambda t: t + '<a href="https://example.com/">x</a>'),
            'changed output after enhancement': edit(page_name, lambda t: t.replace('</h1>', '</h1> ', 1)),
        }

        def css(site, root):
            (site/'api/gnatdoc.css').write_bytes((site/'api/gnatdoc.css').read_bytes() + b'/* x */')

        def manifest_output(site, root):
            data = json.loads((site/MANIFEST).read_text())
            data['output_sha256'][page_name] = '0' * 64
            (site/MANIFEST).write_text(sorted_json(data))

        def manifest_original(site, root):
            data = json.loads((site/MANIFEST).read_text())
            data['original_api_html'][page_name] = data['original_api_html'][page_name].replace(
                '<html class=main>', '<html class=main lang="en">', 1)
            (site/MANIFEST).write_text(sorted_json(data))

        def manifest_rehashed(site, root):
            # Even an output hash recomputed for a re-titled page is not authority.
            target = site/page_name
            target.write_text(target.read_text().replace(html.escape(title(target.read_text())), 'Forged', 1))
            data = json.loads((site/MANIFEST).read_text())
            data['output_sha256'][page_name] = digest(target.read_bytes())
            (site/MANIFEST).write_text(sorted_json(data))

        def source(site, root):
            path = root/'qualification-public'/SPEC['public_sources'][0]
            path.write_text(path.read_text() + '\n-- modified after enhancement\n')

        mutations.update({'changed native CSS': css, 'tampered manifest output': manifest_output,
                          'tampered manifest original': manifest_original,
                          'forged title with rehashed manifest': manifest_rehashed,
                          'modified source after enhancement': source})
        state = lambda root: (hashes(root/'_site'), hashes(root/'qualification-public'))
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                root, config, site = self.copy()
                verify(config, site)
                before = state(root)
                mutate(site, root)
                self.assertNotEqual(state(root), before)
                with self.assertRaises((EnhancementError, ValueError)):
                    verify(config, site)

    def test_independent_validation_names_each_metadata_defect(self):
        root, config, site = self.copy()
        expected = set(self.hashes)
        titles = document_titles(config, snapshot(config, REAL/'pristine'))
        validate_files(site, config, expected, titles=titles)
        page = next(p for p in site.glob('api/[0-9a-f]*.html'))
        good = page.read_text()
        for mutated, reason in (
                (TITLE.sub('', good, 1), 'missing or duplicate document title'),
                (good.replace('</title>', '</title><title>X</title>', 1), 'duplicate document title'),
                (good.replace(' lang="en"', '', 1), 'document language'),
                (good.replace('lang="en"', 'lang="fr"', 1), 'lang="en"'),
                (good.replace('<meta charset="utf-8">', '', 1), 'charset'),
                (TITLE.sub('<title>' + html.escape(titles['api/index.html']) + '</title>', good, 1),
                 'verified identity')):
            with self.subTest(reason=reason):
                page.write_text(mutated)
                with self.assertRaisesRegex(EnhancementError, reason):
                    validate_files(site, config, expected, titles=titles)
        page.write_text(good)

    def test_titled_conflicting_or_renamed_native_input_rejected(self):
        for name, mutate, reason in (
                ('titled native page', lambda t: t.replace(NATIVE_LINK, '<title>Native</title>' + NATIVE_LINK, 1), 'layout'),
                ('native language', lambda t: t.replace('<html class=main>', '<html class=main lang="en">', 1), 'layout'),
                ('native metadata in body', lambda t: t + '<meta charset="utf-8">', 'already has document metadata'),
                ('heading case differs from source', lambda t: t.replace('<h1>OpenCV.Geometry</h1>', '<h1>OPENCV.Geometry</h1>', 1),
                 'differs from its Ada source name')):
            with self.subTest(case=name):
                temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
                root, config, site = geometry(Path(temp.name))
                page = next(p for p in site.glob('api/[0-9a-f]*.html') if '<h1>OpenCV.Geometry</h1>' in p.read_text())
                page.write_text(mutate(page.read_text()))
                before = hashes(site)
                with self.assertRaisesRegex(EnhancementError, reason):
                    enhance(config, site)
                self.assertEqual(hashes(site), before)

    def test_deterministic_idempotent_and_independently_reconstructed(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root, config, site = geometry(Path(temp.name))
        enhance(config, site)
        self.assertEqual(hashes(site), self.hashes)
        enhance(config, site)
        self.assertEqual(hashes(site), self.hashes)
        self.assertEqual(verify(config, site)['mode'], 'verified')

    def test_metadata_is_the_only_change_without_presentation_features(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        plain = SPEC['configuration'].replace('[navigation]\nmode = "operations"\ncategories = "docs/api-categories.json"\n',
                                              '[navigation]\nmode = "none"\n[presentation]\ntheme = false\n'
                                              'syntax_highlighting = false\ntype_links = false\n')
        root, config, site = geometry(Path(temp.name), plain)
        self.assertFalse(config.theme or config.highlight or config.type_links or config.navigation != 'none')
        native = snapshot(config, site)
        enhance(config, site)
        titles = document_titles(config, native)
        for name, text in pages(site).items():
            with self.subTest(page=name):
                original = (REAL/'pristine'/name).read_text()
                self.assertEqual(strip_native_document(text, titles[name], name), original)
                self.assertNotIn('gnatdoc-theme.css', text)
                self.assertNotIn('viewport', text)
                self.assertNotIn('<script', text)
        verify(config, site)

    def test_html_unsafe_project_is_escaped_and_untrusted_project_rejected(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        unsafe = 'Ada <Docs> & "Tools"'
        root, config, site = geometry(Path(temp.name), SPEC['configuration'].replace(
            'project = "opencv_geometry_ada"', 'project = ' + json.dumps(unsafe)))
        enhance(config, site)
        verify(config, site)
        index = (site/'api/index.html').read_text()
        self.assertIn('<title>API Reference — Ada &lt;Docs&gt; &amp; &quot;Tools&quot;</title>', index)
        self.assertNotIn('<Docs>', index)
        self.assertEqual(Document(index).titles, ['API Reference — ' + unsafe])
        for bad in ('Line\\nbreak', 'Bidi\\u202eName', ' padded'):
            with self.subTest(project=bad):
                temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
                root, config, site = geometry(Path(temp.name), SPEC['configuration'].replace(
                    'project = "opencv_geometry_ada"', 'project = "' + bad + '"'))
                before = hashes(site)
                with self.assertRaisesRegex(EnhancementError, 'untrusted project name'):
                    enhance(config, site)
                self.assertEqual(hashes(site), before)


MARKDOWN_HOME = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Synthetic portal</title>'
                 '<link rel="stylesheet" href="assets/gnatdoc-guides.css"></head><body><header>{{navigation}}'
                 '</header><main id="main"><h1>Synthetic portal</h1>{{package-directory}}</main></body></html>\n')
OLD_GUIDE_HEAD = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
                  '<meta name="viewport" content="width=device-width, initial-scale=1">'
                  '<link rel="stylesheet" href="../assets/gnatdoc-guides.css"></head><body>')


class MarkdownGuides(unittest.TestCase):
    """The source-owned Markdown guide mode used by OpenCV Features."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gnatdoc010-guides-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'core'
        shutil.copytree(TESTS/'fixtures/core', self.root)
        guides = [{'id': 'getting-started', 'label': 'Getting started', 'path': 'guides/getting-started.html'},
                  {'id': 'safe-names', 'label': 'Using <Mat> & "views"', 'path': 'guides/safe-names.html'}]
        docs = self.root/'docs'; (docs/'guides').mkdir(parents=True)
        (docs/'site-map.json').write_text(json.dumps({'schema_version': 1, 'home': 'index.html',
            'stylesheet': 'assets/gnatdoc-guides.css', 'guides': guides}))
        (docs/'index.html').write_text(MARKDOWN_HOME)
        (docs/'guides/getting-started.md').write_text(
            '# Getting started\n\nSee [OpenCV.Core](api:OpenCV.Core).\n\n```sh\nalr build\n```\n')
        (docs/'guides/safe-names.md').write_text('# Using <Mat> & "views"\n\nText.\n')
        with (self.root/'project.toml').open('a') as stream:
            stream.write('[guides]\nmode = "markdown"\nmanifest = "docs/site-map.json"\n')
        self.config = load(self.root, 'project.toml')
        self.site = self.root/'_site'

    def test_guide_titles_from_labels_with_preserved_bodies(self):
        native = snapshot(self.config, self.site)
        enhance(self.config, self.site)
        verify(self.config, self.site)
        titles = document_titles(self.config, native)
        for guide, label_ in (('guides/getting-started.html', 'Getting started'),
                              ('guides/safe-names.html', 'Using <Mat> & "views"')):
            with self.subTest(guide=guide):
                text = (self.site/guide).read_text()
                expected = label_ + ' — Core synthetic conformance'
                self.assertEqual(titles[guide], expected)
                self.assertEqual(Document(text).titles, [expected])
                self.assertEqual(text.count('<title>'), 1)
                self.assertNotIn('<Mat>', text)
                old = text.replace('<title>' + html.escape(expected) + '</title>', '', 1)
                self.assertTrue(old.startswith(OLD_GUIDE_HEAD), old[:300])
                self.assertIn('<main id="main"><h1>' + html.escape(label_) + '</h1>', old)
        self.assertIn('href="../api/', (self.site/'guides/getting-started.html').read_text())
        home = (self.site/'index.html').read_text()
        self.assertEqual(Document(home).titles, ['Synthetic portal'])
        for name, text in pages(self.site).items():
            check_document(text, name)

    def test_heading_must_match_its_manifest_label(self):
        (self.root/'docs/guides/getting-started.md').write_text('# Start here\n\nText.\n')
        with self.assertRaisesRegex(EnhancementError, 'differs from its site-map label'):
            enhance(self.config, self.site)

    def test_author_home_metadata_is_required_not_invented(self):
        for home, reason in ((MARKDOWN_HOME.replace('<title>Synthetic portal</title>', ''), 'missing or duplicate'),
                             (MARKDOWN_HOME.replace('</title>', '</title><title>Two</title>'), 'duplicate document title'),
                             (MARKDOWN_HOME.replace(' lang="en"', ''), 'document language'),
                             (MARKDOWN_HOME.replace('<meta charset="utf-8">', ''), 'charset')):
            with self.subTest(reason=reason):
                (self.root/'docs/index.html').write_text(home)
                before = hashes(self.site)
                with self.assertRaisesRegex(EnhancementError, reason):
                    enhance(self.config, self.site)
                self.assertEqual(hashes(self.site), before)

    def test_removed_guide_title_rejected_by_verification(self):
        enhance(self.config, self.site)
        page = self.site/'guides/getting-started.html'
        page.write_text(TITLE.sub('', page.read_text(), 1))
        with self.assertRaises(EnhancementError):
            verify(self.config, self.site)


class AuthoredAndPortalModes(unittest.TestCase):
    def stage(self, name):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)/name
        shutil.copytree(TESTS/'authored-fixtures'/name, root)
        return root, load(root, 'project.toml'), root/'native'

    def test_authored_markdown_titles_are_kept_once_and_api_pages_titled(self):
        root, config, site = self.stage('imgproc')
        data = json.loads((root/'authored.json').read_text())
        enhance(config, site); verify(config, site)
        for entry in data['guides']:
            text = (site/entry['path']).read_text()
            self.assertEqual(Document(text).titles, [entry['label'] + ' — ' + data['title_suffix']])
        self.assertEqual((site/'index.html').read_bytes(), (root/data['home']['source']).read_bytes())
        for name, text in pages(site).items():
            check_document(text, name, generated=name.startswith('api/'))

    def test_authored_html_titles_respected_and_missing_title_rejected(self):
        root, config, site = self.stage('mel')
        enhance(config, site); verify(config, site)
        reference = {p.relative_to(root/'reference').as_posix(): p.read_bytes()
                     for p in (root/'reference').rglob('*.html')}
        for name, value in reference.items():
            self.assertEqual((site/name).read_bytes(), value)
        root, config, site = self.stage('mel')
        data = json.loads((root/'authored.json').read_text())
        source = root/data['guides'][0]['source']
        source.write_text(TITLE.sub('', source.read_text(), 1))
        data['inputs'] = {p: digest((root/p).read_bytes()) for p in data['inputs']}
        payload = sorted_json(data).encode(); (root/'authored.json').write_bytes(payload)
        config = replace(config, guide_sha256=digest(payload))
        before = hashes(site)
        with self.assertRaisesRegex(EnhancementError, 'missing or duplicate document title'):
            enhance(config, site)
        self.assertEqual(hashes(site), before)

    def test_html_mode_requires_author_titles(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)/'mel'; shutil.copytree(TESTS/'fixtures/mel', root)
        config = load(root, 'project.toml')
        guide = root/'docs/guides/architecture.html'
        guide.write_text(TITLE.sub('', guide.read_text(), 1))
        with self.assertRaisesRegex(EnhancementError, 'missing or duplicate document title'):
            enhance(config, root/'_site')

    def test_default_profile_without_guides_titles_only_api_pages(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root = Path(temp.name)/'core'; shutil.copytree(TESTS/'fixtures/core', root)
        config = load(root, 'project.toml'); site = root/'_site'
        self.assertEqual(config.guides, 'none')
        enhance(config, site); verify(config, site)
        titles = document_titles(config, snapshot(config, TESTS/'fixtures/core/_site'))
        self.assertEqual(set(pages(site)), set(titles))
        for name, text in pages(site).items():
            self.assertEqual(check_document(text, name, title=titles[name], generated=True), titles[name])


if __name__ == '__main__':
    unittest.main()
