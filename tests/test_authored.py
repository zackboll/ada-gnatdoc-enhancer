"""Authentic pinned inputs; all mutations below are synthetic adversarial cases.

Text ownership is not evidence of example compilation. Executed original
integration gates are recorded separately under docs/evidence/gnatdoc007.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ada_gnatdoc_enhancer.authored import api_destinations, manifest, markdown, render, safe_uri
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json
from ada_gnatdoc_enhancer.validation import Page

FIXTURES = Path(__file__).parent/'authored-fixtures'


class Authored(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = {n: snapshot(load(FIXTURES/n, 'project.toml'), FIXTURES/n/'native')
                      for n in ('core', 'imgproc', 'geometry', 'mel')}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'project'
        shutil.copytree(FIXTURES/'imgproc', self.root)
        self.config = load(self.root, 'project.toml')
        self.data = json.loads((self.root/'authored.json').read_text())

    def authorize_synthetic(self):
        """Explicitly reauthorize a synthetic policy to exercise deeper checks."""
        self.data['inputs'] = {p: digest((self.root/p).read_bytes()) for p in self.data['inputs']}
        payload = sorted_json(self.data).encode(); (self.root/'authored.json').write_bytes(payload)
        self.config = replace(self.config, guide_sha256=digest(payload))

    def reject(self):
        with self.assertRaises((EnhancementError, ValueError, TypeError)):
            render(self.config, self.native['imgproc'])

    def test_authentic_all_21_guides_landing_and_styles_byte_parity(self):
        for name in self.native:
            with self.subTest(consumer=name):
                root = FIXTURES/name; config = load(root, 'project.toml')
                expected = render(config, self.native[name])
                reference = {p.relative_to(root/'reference').as_posix(): p.read_bytes()
                             for p in (root/'reference').rglob('*') if p.is_file()}
                self.assertEqual(expected, reference)
                provenance = json.loads((root/'provenance.json').read_text())
                self.assertEqual(provenance['inputs'], manifest(config, self.native[name])['inputs'])

    def test_source_byte_change(self):
        (self.root/self.data['guides'][0]['source']).write_text('# Invented\n')
        self.reject()

    def test_stylesheet_changed(self):
        (self.root/self.data['stylesheet']['source']).write_text('body {}')
        self.reject()

    def test_missing_stylesheet(self):
        (self.root/self.data['stylesheet']['source']).unlink()
        self.reject()

    def test_duplicate_manifest_keys(self):
        p = self.root/'authored.json'; payload = p.read_bytes().replace(b'"schema_version": 2', b'"schema_version": 2, "schema_version": 2')
        p.write_bytes(payload); self.config = replace(self.config, guide_sha256=digest(payload))
        self.reject()

    def test_unknown_manifest_key(self):
        self.data['arbitrary_template'] = 'yes'; self.authorize_synthetic(); self.reject()

    def test_duplicate_identity(self):
        self.data['guides'].append(self.data['guides'][0]); self.authorize_synthetic(); self.reject()

    def test_ambiguous_source_mapping(self):
        self.data['guides'][1]['source'] = self.data['guides'][0]['source']
        self.authorize_synthetic(); self.reject()

    def test_unauthorized_path(self):
        self.data['guides'][0]['path'] = 'api/injected.html'; self.authorize_synthetic(); self.reject()

    def test_extra_input(self):
        self.data['inputs']['docs/extra.md'] = digest(b'hi'); (self.root/'docs/extra.md').write_text('hi')
        self.authorize_synthetic(); self.reject()

    def test_extra_guide_source(self):
        (self.root/'docs/guides/extra.md').write_text('# Extra\n'); self.reject()

    def test_missing_guide(self):
        self.data['guides'].pop(); self.authorize_synthetic(); self.reject()

    def test_missing_examples(self):
        self.data['examples'] = []; self.authorize_synthetic(); self.reject()

    def test_unused_example(self):
        p = 'docs/examples/invented.adb'; (self.root/p).write_text('procedure Invented is begin null; end;\n')
        self.data['examples'].append(p); self.data['inputs'][p] = ''
        self.authorize_synthetic(); self.reject()

    def test_ambiguous_example(self):
        p = 'docs/examples/duplicate.adb'; shutil.copyfile(self.root/self.data['examples'][0], self.root/p)
        self.data['examples'].append(p); self.data['inputs'][p] = ''
        self.authorize_synthetic(); self.reject()

    def test_ada_fence_literal_mutation(self):
        p = self.root/self.data['guides'][0]['source']; text = p.read_text()
        start = text.index('```ada\n') + len('```ada\n')
        p.write_text(text[:start] + '-- synthetic mutation\n' + text[start:])
        self.authorize_synthetic(); self.reject()

    def test_truncated_ada_fence(self):
        p = self.root/self.data['guides'][0]['source']; text = p.read_text()
        start = text.index('```ada\n') + len('```ada\n'); end = text.index('\n', start)
        p.write_text(text[:start] + text[end + 1:]); self.authorize_synthetic(); self.reject()

    def test_unknown_api_name(self):
        p = self.root/self.data['guides'][0]['source']; p.write_text(p.read_text() + '\n[Wrong](api:Invented)\n')
        self.authorize_synthetic(); self.reject()

    def test_broken_guide_fragment(self):
        p = self.root/self.data['guides'][0]['source']; p.write_text(p.read_text() + '\n[Wrong](#invented)\n')
        self.authorize_synthetic(); self.reject()

    def test_source_order_not_native_order(self):
        from ada_gnatdoc_enhancer.inventory import packages, direct_callables
        from ada_gnatdoc_enhancer.profiles import reconcile
        api = api_destinations(self.config, self.native['imgproc'])
        pkg = next(iter(packages(self.config).values())); page = next(iter(self.native['imgproc'].pages.values()))
        names = [d.name.lower() for d in pkg.declarations]
        name = next(n for n in names if names.count(n) > 1)
        declarations = [d for d in pkg.declarations if d.name.lower() == name]
        reversed_page = replace(page, sections=list(reversed(page.sections)))
        native = replace(self.native['imgproc'], pages={pkg.name.lower(): reversed_page})
        self.assertEqual(api, api_destinations(self.config, native))
        targets = []
        for i, decl in enumerate(declarations, 1):
            section, = [s for s in page.sections if s.name.lower() == name and
                        reconcile(decl.signature, s.code, direct_callables(pkg))]
            self.assertTrue(api[f'{name}/{i}'].endswith('#' + section.anchor)); targets.append(section.anchor)
        self.assertEqual(len(targets), len(set(targets)))

    def test_wrong_existing_anchor_native_evidence(self):
        native = self.native['imgproc']; page = next(iter(native.pages.values()))
        a, b = page.sections[:2]
        text = page.original.replace(a.anchor, 'PLACEHOLDER').replace(b.anchor, a.anchor).replace('PLACEHOLDER', b.anchor)
        mutated = replace(native, pages={page.package.lower(): replace(page, original=text)})
        with self.assertRaisesRegex(EnhancementError, 'destination evidence'):
            render(self.config, mutated)

    def test_symlink_source(self):
        p = self.root/self.data['guides'][0]['source']; target = self.root/'saved.md'; p.rename(target); p.symlink_to(target)
        self.reject()

    def test_symlink_source_directory(self):
        p = self.root/'docs/guides'; target = self.root/'saved'; p.rename(target); p.symlink_to(target, target_is_directory=True)
        self.reject()

    def test_source_path_traversal(self):
        self.data['guides'][0]['source'] = '../outside'; self.authorize_synthetic(); self.reject()

    def test_unclosed_fence(self):
        with self.assertRaisesRegex(EnhancementError, 'unclosed'):
            markdown('# Title\n\n```ada\nprocedure X;\n', ['ada'])

    def test_unknown_language(self):
        with self.assertRaisesRegex(EnhancementError, 'language'):
            markdown('# Title\n\n```python\nprint(1)\n```\n', ['ada'])

    def test_heading_collisions(self):
        _, ids, _ = markdown('# Title\n\n## Same\n\n## Same\n\n## Same-1\n', [])
        self.assertEqual(ids, ['title', 'same', 'same-1', 'same-1-1'])

    def test_heading_hierarchy(self):
        for text in ('## No H1\n', '# Title\n\n### Jump\n', '# Title\n\n# Second\n'):
            with self.subTest(text=text), self.assertRaises(EnhancementError): markdown(text, [])

    def test_raw_html_images_and_executable_links(self):
        for text in ('<script>bad</script>', '![image](https://github.com/a)', '<b>raw</b>',
                     '[bad](javascript:alert(1))', '[bad](data:text/html,evil)', '[bad](file:///etc/passwd)'):
            with self.subTest(text=text), self.assertRaises(EnhancementError):
                markdown('# Title\n\n' + text + '\n', [], lambda link: (safe_uri(link, self.config), link)[1])

    def test_unsafe_links(self):
        for link in ('https://evil.invalid/', 'https://github.com/?q=x', 'https://github.com:443/',
                     'https://github.com/%252e', '%ZZ', '#bad%2', '../outside', 'a/../x', '/absolute',
                     'https://user@github.com/', '//github.com/', 'javascript:alert(1)', 'a%2fb'):
            with self.subTest(link=link), self.assertRaises(EnhancementError): safe_uri(link, self.config)

    def test_pinned_markdown_versions(self):
        with patch('ada_gnatdoc_enhancer.authored.version', return_value='999'):
            with self.assertRaisesRegex(EnhancementError, 'dependency version'): markdown('# Title\n', [])

    def test_original_modes_still_accepted(self):
        from ada_gnatdoc_enhancer.guides import render as guides_render
        self.assertEqual(guides_render(replace(self.config, guides='none'), self.native['imgproc']), {})

    def test_mel_security_and_unresolved_tokens(self):
        from ada_gnatdoc_enhancer.authored import check_html, portal
        config = load(FIXTURES/'mel', 'project.toml'); native = self.native['mel']; data = manifest(config, native)
        for text in ('<script>alert(1)</script>', '<a onclick="bad()">Bad</a>', '<input>', '<a ping="/ping">Bad</a>',
                     '<div id="same"></div><p id="same"></p>'):
            with self.subTest(text=text), self.assertRaises(EnhancementError): check_html(text)
        for text in ('{{unknown}}', '{{package:Missing}}'):
            with self.subTest(text=text), self.assertRaises(EnhancementError): portal(text, 'index.html', data, native)

    def test_mel_package_groups_and_directory_cardinality(self):
        from ada_gnatdoc_enhancer.authored import portal
        config = load(FIXTURES/'mel', 'project.toml'); native = self.native['mel']; data = manifest(config, native)
        for mutate in (lambda d: d['groups'][0]['packages'].pop(),
                       lambda d: d['groups'].append(d['groups'][0]),
                       lambda d: d['groups'][0].update(label='')):
            bad = json.loads(json.dumps(data)); mutate(bad)
            with self.assertRaises(EnhancementError): portal('{{package-directory}}', 'index.html', bad, native)

    def mel_copy(self):
        root = Path(self.temp.name)/'mel'; shutil.copytree(FIXTURES/'mel', root)
        self.root = root; self.config = load(root, 'project.toml')
        self.data = json.loads((root/'authored.json').read_text())

    def test_malformed_mel_site_map(self):
        self.mel_copy(); p = self.root/self.data['site_map']
        data = json.loads(p.read_text()); data['guides'][0]['label'] = 'Synthetic'
        p.write_text(sorted_json(data)); self.authorize_synthetic()
        with self.assertRaisesRegex(EnhancementError, 'site map mismatch'):
            render(self.config, self.native['mel'])

    def test_mel_swapped_hashed_filename(self):
        self.mel_copy(); p = self.root/self.data['anchors']; evidence = json.loads(p.read_text())
        first = next(iter(evidence)); different = next(k for k in evidence if evidence[k]['page'] != evidence[first]['page'])
        evidence[first]['page'] = evidence[different]['page']; p.write_text(sorted_json(evidence))
        self.authorize_synthetic()
        with self.assertRaisesRegex(EnhancementError, 'native anchor evidence'):
            render(self.config, self.native['mel'])

    def test_mel_wrong_but_existing_anchor(self):
        self.mel_copy(); p = self.root/self.data['anchors']; evidence = json.loads(p.read_text())
        a, b = list(evidence)[:2]; evidence[a]['anchor'] = evidence[b]['anchor']
        p.write_text(sorted_json(evidence)); self.authorize_synthetic()
        with self.assertRaisesRegex(EnhancementError, 'native anchor evidence'):
            render(self.config, self.native['mel'])

    def test_mel_missing_api_map_directory(self):
        self.mel_copy(); p = self.root/'docs/guides/api-map.html'
        p.write_text(p.read_text().replace('{{package-directory}}', ''))
        self.authorize_synthetic()
        with self.assertRaisesRegex(EnhancementError, 'directory cardinality'):
            render(self.config, self.native['mel'])

    def test_mel_renderer_exception_not_credited_or_fabricated(self):
        from ada_gnatdoc_enhancer.pipeline import expected_output
        self.mel_copy()
        with self.assertRaises(EnhancementError):
            expected_output(replace(self.config, renderer_exceptions=('Synthetic.Status',)), self.root/'native')
        with self.assertRaises(EnhancementError):
            expected_output(replace(self.config, renderer_exceptions=()), self.root/'native')
        _, values, counts = expected_output(self.config, self.root/'native')
        self.assertEqual(counts['unrendered_renderer_exceptions'], 1)
        self.assertEqual(counts['declaration_snippets'], 1237)
        self.assertFalse(any(b'Metadata.Status</a>' in value for value in values.values()))

    def test_css_resources_rejected_under_synthetic_authorization(self):
        (self.root/self.data['stylesheet']['source']).write_text('@import "https://github.com/a.css";')
        self.authorize_synthetic(); self.reject()

    def test_build_project_does_not_compile_all_examples(self):
        p = self.root/self.data['example_project']; p.write_text(p.read_text().replace('"filtering_and_transforms.adb",', ''))
        self.authorize_synthetic(); self.reject()

    def test_extra_unapproved_example_source(self):
        (self.root/'docs/examples/extra.adb').write_text('procedure Extra is begin null; end;\n')
        self.reject()

    def test_ambiguous_api_names_across_packages_rejected(self):
        from ada_gnatdoc_enhancer.inventory import packages
        # Explicit synthetic second package with the same declarations. Pinned
        # Geometry happens not to share any scanner names across its packages.
        pkg = next(iter(packages(self.config).values()))
        synthetic = replace(pkg, name='Synthetic.Owner')
        original = self.native['imgproc']; page = next(iter(original.pages.values()))
        native = replace(original, pages={pkg.name.lower(): page,
            'synthetic.owner': replace(page, package='Synthetic.Owner')})
        with patch('ada_gnatdoc_enhancer.authored.packages', return_value={
                pkg.name.lower(): pkg, 'synthetic.owner': synthetic}):
            api = api_destinations(self.config, native)
        for declaration in pkg.declarations:
            name = declaration.name.lower()
            self.assertNotIn(name, api); self.assertNotIn(name + '/1', api)

    def test_output_symlink_and_nonregular_rejected(self):
        site = self.root/'native'; target = site/'extra'; target.symlink_to(self.root/'project.toml')
        with self.assertRaises(EnhancementError): enhance(self.config, site)
        target.unlink()
        import os
        os.mkfifo(target)
        with self.assertRaises(EnhancementError): enhance(self.config, site)

    def test_atomic_failure(self):
        site = self.root/'native'; before = hashes(site)
        p = self.root/self.data['guides'][0]['source']; p.write_text(p.read_text() + '\n<script>bad</script>\n')
        self.authorize_synthetic()
        with self.assertRaises(EnhancementError): enhance(self.config, site)
        self.assertEqual(hashes(site), before)

    def test_publication_reconstruction_tampering_determinism_idempotence(self):
        # Smallest authentic complete portal; 29 native packages, all six pages.
        root = Path(self.temp.name)/'mel'; shutil.copytree(FIXTURES/'mel', root)
        config = load(root, 'project.toml'); site = root/'native'
        enhance(config, site); before = hashes(site); verify(config, site); enhance(config, site)
        self.assertEqual(before, hashes(site))
        second = root/'second'; shutil.copytree(FIXTURES/'mel'/'native', second); enhance(config, second)
        self.assertEqual(before, hashes(second))
        page = site/'guides/api-map.html'; good = page.read_bytes(); page.write_bytes(good.replace(b'Architecture', b'Invented'))
        metadata = site/'api/presentation.json'; original = metadata.read_bytes(); data = json.loads(original)
        data['output_sha256']['guides/api-map.html'] = digest(page.read_bytes()); metadata.write_text(sorted_json(data))
        with self.assertRaises(EnhancementError): verify(config, site)
        page.write_bytes(good); metadata.write_bytes(original); verify(config, site)
        (site/'extra.html').write_text('extra')
        with self.assertRaises(EnhancementError): verify(config, site)