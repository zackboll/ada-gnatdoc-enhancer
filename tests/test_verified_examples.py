"""Compiler-free consumption of retained fresh GNAT/LAL evidence and mutations."""
from __future__ import annotations

import copy
from dataclasses import replace
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ada_gnatdoc_enhancer.authored import render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.examples import Resolver, code
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.util import digest, sorted_json

FIXTURES = Path(__file__).parent / 'verified-fixtures'


class CodeHTML(HTMLParser):
    def __init__(self, markup):
        super().__init__(); self.depth = 0; self.text = []; self.links = []; self.active = False
        self.feed(markup); self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'pre': self.depth += 1
        if self.depth and tag == 'a':
            if self.active: raise ValueError('nested hyperlink')
            self.active = True; self.links.append(dict(attrs)['href'])

    def handle_endtag(self, tag):
        if tag == 'pre': self.depth -= 1
        if tag == 'a': self.active = False

    def handle_data(self, value):
        if self.depth: self.text.append(value)


class VerifiedExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'authority'
        shutil.copytree(FIXTURES / 'overloads', self.root)
        self.config = load(self.root, 'project.toml')
        self.native = snapshot(self.config, self.root / 'native')
        self.data = json.loads((self.root / 'mapping.json').read_text())

    def resolver(self, data=None):
        config = self.config
        if data is not None:
            payload = sorted_json(data).encode(); (self.root / 'mapping.json').write_bytes(payload)
            config = replace(config, verified_examples={'mapping': 'mapping.json', 'sha256': digest(payload)})
        return Resolver(config, self.native, ['valid.adb'])

    def test_exact_overloads_named_defaulted_and_return_context(self):
        resolver = self.resolver()
        text = (self.root / 'valid.adb').read_text()
        positions = resolver.verified.positions(text, 'valid.adb')
        self.assertEqual(len(positions), 12)
        expected = {6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11,
                    14: 12, 15: 14, 16: 15, 17: 6}
        self.assertEqual({m['occurrence']['line']: m['selected']['line'] for m in self.data['mappings']}, expected)
        targets = [href for _, _, href in positions]
        self.assertNotEqual(targets[0], targets[1])
        self.assertNotEqual(targets[2], targets[3])
        self.assertNotEqual(targets[9], targets[10])
        parsed = CodeHTML('<pre>' + code(text, resolver, source='valid.adb') + '</pre>')
        self.assertEqual(''.join(parsed.text).encode(), text.encode())
        self.assertEqual(len(parsed.links), 12)

    def test_complete_authored_overload_render(self):
        result = render(self.config, self.native)
        parsed = CodeHTML(result['guides/verified.html'].decode())
        self.assertEqual(len(parsed.links), 12)
        self.assertEqual(''.join(parsed.text).encode(), (self.root / 'valid.adb').read_bytes())

    def test_real_authored_core_html_mat_not_umat(self):
        root = FIXTURES / 'core'; config = load(root, 'project.toml')
        native = snapshot(config, root / 'native'); result = render(config, native)
        parsed = CodeHTML(result['guides/verified.html'].decode())
        self.assertEqual(''.join(parsed.text).encode(), (root / 'docs/example.adb').read_bytes())
        resolver = Resolver(config, native, ['docs/example.adb'])
        mappings = json.loads((root / 'mapping.json').read_text())['mappings']
        self.assertEqual([m['selected']['line'] for m in mappings], [1130, 1242, 3661, 3669])
        clone = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : Mat)' in d.declaration.signature)
        umat = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : UMat)' in d.declaration.signature)
        self.assertIn('../api/' + clone.href, parsed.links)
        self.assertNotIn('../api/' + umat.href, parsed.links)
        self.assertEqual(len(parsed.links), 6)  # four verified plus two unchanged lexical type marks

    def test_wrong_lal_identity_rejected_even_with_new_mapping_pin(self):
        data = copy.deepcopy(self.data); data['mappings'][0]['selected']['line'] = 5
        with self.assertRaisesRegex(EnhancementError, 'compiler/Libadalang'): self.resolver(data)

    def test_wrong_compiler_identity_rejected(self):
        data = copy.deepcopy(self.data); data['mappings'][0]['compiler_selected']['line'] = 5
        with self.assertRaises(EnhancementError): self.resolver(data)

    def test_duplicate_and_conflicting_spans_rejected(self):
        for conflict in (False, True):
            data = copy.deepcopy(self.data); entry = copy.deepcopy(data['mappings'][0])
            if conflict: entry['profile'] = data['mappings'][1]['profile']
            data['mappings'].append(entry)
            with self.subTest(conflict=conflict), self.assertRaises(EnhancementError): self.resolver(data)

    def test_wrong_columns_and_token_boundaries_rejected(self):
        for key in ('line', 'column', 'start', 'end'):
            data = copy.deepcopy(self.data); data['mappings'][0]['occurrence'][key] += 1
            with self.subTest(key=key), self.assertRaises(EnhancementError): self.resolver(data)

    def test_unknown_incomplete_and_url_authority_rejected(self):
        for mutation in ('url', 'missing', 'schema', 'kind', 'profile', 'identity', 'fingerprint', 'classification'):
            data = copy.deepcopy(self.data); entry = data['mappings'][0]
            if mutation == 'url': entry['url'] = 'https://evil.invalid'
            elif mutation == 'missing': del entry['profile']
            elif mutation == 'schema': data['schema_version'] = 2
            elif mutation == 'kind': entry['selected']['kind'] = 'SubpRenamingDecl'
            elif mutation == 'profile': entry['profile'] = data['mappings'][1]['profile']
            elif mutation == 'identity': entry['identity'] = 'other.clone'
            elif mutation == 'fingerprint': entry['evidence_sha256'] = '0' * 64
            else: entry['classification'] = 'dispatching-call'
            with self.subTest(mutation=mutation), self.assertRaises(EnhancementError): self.resolver(data)

    def test_tampered_mapping_with_original_pin_rejected(self):
        path = self.root / 'mapping.json'; path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(EnhancementError, 'pin mismatch'): self.resolver()

    def test_missing_mapping_rejected(self):
        (self.root / 'mapping.json').unlink()
        with self.assertRaises(EnhancementError): self.resolver()

    def test_duplicate_json_keys_rejected(self):
        payload = (self.root / 'mapping.json').read_bytes().replace(b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1', 1)
        (self.root / 'mapping.json').write_bytes(payload)
        self.config = replace(self.config, verified_examples={'mapping': 'mapping.json', 'sha256': digest(payload)})
        with self.assertRaisesRegex(EnhancementError, 'duplicate'): self.resolver()

    def test_stale_sources_and_project_rejected(self):
        for name in ('valid.adb', 'overloads.ads', 'fixtures.gpr'):
            path = self.root / name; original = path.read_bytes(); path.write_bytes(original + b'\n-- stale\n')
            with self.subTest(name=name), self.assertRaises(EnhancementError): self.resolver()
            path.write_bytes(original)

    def test_reordered_overloads_rejected_even_if_input_hashes_rewritten(self):
        path = self.root / 'overloads.ads'; text = path.read_text(); lines = text.splitlines(True)
        lines[3], lines[4] = lines[4], lines[3]; path.write_text(''.join(lines))
        # Also mutate the public export and input pin: the old canonical profile
        # still cannot match the compiler's defining-token coordinates.
        (self.root / 'public/overloads.ads').write_bytes(path.read_bytes())
        data = copy.deepcopy(self.data); data['inputs']['overloads.ads'] = digest(path.read_bytes())
        for mapping in data['mappings']:
            if mapping['selected']['file'] == 'overloads.ads':
                mapping['selected']['sha256'] = mapping['compiler_selected']['sha256'] = digest(path.read_bytes())
        with self.assertRaises(EnhancementError): self.resolver(data)

    def test_changed_native_anchor_and_profile_rejected(self):
        from ada_gnatdoc_enhancer.native_html import Section
        page = self.native.pages['overloads']; old = page.sections[0]
        for changed in (replace(old, anchor='f' * 64), Section(old.anchor, old.name, old.code + ' invalid')):
            page.sections[0] = changed
            with self.assertRaises(EnhancementError): self.resolver()
        page.sections[0] = old

    def test_incomplete_fragment_or_unowned_source_gets_no_verified_link(self):
        resolver = self.resolver()
        self.assertNotIn('<a ', code('X := U.Clone;', resolver))
        self.assertNotIn('<a ', code('X := U.Clone;', resolver, source='unowned.adb'))
        with self.assertRaisesRegex(EnhancementError, 'complete authoritative'):
            code('X := U.Clone;', resolver, source='valid.adb')

    def test_no_verified_links_on_landing_or_without_identity(self):
        resolver = self.resolver(); text = (self.root / 'valid.adb').read_text()
        self.assertEqual(code(text, resolver), code(text, Resolver(replace(self.config, verified_examples={}), self.native)))

    def test_configuration_requires_pin_and_explicit_links(self):
        path = self.root / 'project.toml'; original = path.read_text()
        for changed in (original.replace('ada_example_api_links = true', 'ada_example_api_links = false'),
                        original.replace('mapping = "mapping.json"', ''),
                        original.replace(self.config.verified_examples['sha256'], 'not-a-hash')):
            path.write_text(changed)
            with self.assertRaises(EnhancementError): load(self.root, 'project.toml')

    def test_disabled_feature_ignores_missing_mapping_and_preserves_bytes(self):
        config = replace(self.config, verified_examples={})
        before = Resolver(config, self.native)
        (self.root / 'mapping.json').unlink()
        text = (self.root / 'valid.adb').read_text()
        self.assertEqual(code(text, before), code(text, Resolver(config, self.native)))

    def test_full_pipeline_repeated_generation_and_tamper_verification(self):
        from ada_gnatdoc_enhancer.pipeline import enhance, verify
        from ada_gnatdoc_enhancer.qualification import hashes
        root = FIXTURES / 'core'; config = load(root, 'project.toml')
        site = Path(self.temp.name) / 'site'; shutil.copytree(root / 'native', site)
        enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); self.assertEqual(before, hashes(site))
        page = site / 'guides/verified.html'; good = page.read_text()
        resolver = Resolver(config, snapshot(config, root / 'native'), ['docs/example.adb'])
        mat = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : Mat)' in d.declaration.signature)
        umat = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : UMat)' in d.declaration.signature)
        page.write_text(good.replace(mat.href, umat.href))
        with self.assertRaises(EnhancementError): verify(config, site)

    def test_malformed_json_and_traversal_rejected(self):
        payload = b'{"schema_version":'
        (self.root / 'mapping.json').write_bytes(payload)
        self.config = replace(self.config, verified_examples={'mapping': 'mapping.json', 'sha256': digest(payload)})
        with self.assertRaises(EnhancementError): self.resolver()
        data = copy.deepcopy(self.data); data['inputs']['../escape.ads'] = '0' * 64
        with self.assertRaises(EnhancementError): self.resolver(data)


if __name__ == '__main__': unittest.main()