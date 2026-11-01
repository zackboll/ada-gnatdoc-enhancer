"""Mixed source-text publishing: authentic units grant no authority to fragments."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from ada_gnatdoc_enhancer.authored import render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.examples import Resolver, code, landing
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.util import digest, sorted_json
from test_verified_examples import CodeHTML
from verified_support import mixed_core, production_core


class MixedVerifiedExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'authority'
        self.config, self.data = mixed_core(self.root)
        self.native = snapshot(self.config, self.root / 'native')
        self.text = (self.root / 'docs/example.adb').read_text()

    def publish(self):
        payload = sorted_json(self.data).encode(); (self.root / 'authored.json').write_bytes(payload)
        self.config = replace(self.config, guide_sha256=digest(payload))
        return render(self.config, self.native)

    def input(self, name, text):
        (self.root / name).parent.mkdir(parents=True, exist_ok=True)
        (self.root / name).write_text(text)
        self.data['inputs'][name] = digest(text.encode())

    def test_mixed_complete_unit_only_adds_four_links_and_preserves_other_html(self):
        enabled = self.publish()['guides/verified.html'].decode()
        disabled = render(replace(self.config, verified_examples={}), self.native)['guides/verified.html'].decode()
        # Only the complete first fence changes: fragment lexical links, prose and
        # non-Ada fences retain their previous exact HTML, not merely their text.
        self.assertEqual(enabled.split('</pre>', 1)[1], disabled.split('</pre>', 1)[1])
        self.assertEqual(len(CodeHTML(enabled).links) - len(CodeHTML(disabled).links), 4)
        self.assertEqual(''.join(CodeHTML(enabled).text), ''.join(CodeHTML(disabled).text))
        self.assertIn('<code>Image.Clone</code>', enabled)
        self.assertIn('class="language-sh"', enabled)
        self.assertIn('class="language-text"', enabled)
        first = CodeHTML(enabled.split('</pre>', 1)[0] + '</pre>')
        self.assertEqual(''.join(first.text), self.text)
        self.assertEqual(len(first.links), 6)  # two lexical Mat marks retained

    def test_authentic_landing_four_native_destinations_and_not_umat(self):
        page = self.publish()['index.html'].decode()
        parsed = CodeHTML('<pre' + page.split('<pre class="ada-example"', 1)[1])
        self.assertEqual(''.join(parsed.text), self.text.rstrip('\n'))
        resolver = Resolver(self.config, self.native, ['docs/example.adb'])
        mappings = json.loads((self.root / 'mapping.json').read_text())['mappings']
        self.assertEqual([m['selected']['line'] for m in mappings], [1130, 1242, 3661, 3669])
        for _, _, href in resolver.verified.positions(self.text, 'docs/example.adb'):
            self.assertIn('api/' + href, parsed.links)
        umat = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : UMat)' in d.declaration.signature)
        self.assertNotIn('api/' + umat.href, parsed.links)
        self.assertEqual(len(parsed.links), 6)

    def test_landing_is_separately_authorized_not_a_guide_example(self):
        self.data['examples'] = []; self.data['example_project'] = None
        result = self.publish()
        self.assertEqual(len(CodeHTML(result['index.html'].decode()).links), 6)
        # A landing identity alone cannot authenticate a guide fence.
        first = result['guides/verified.html'].decode().split('</pre>', 1)[0] + '</pre>'
        self.assertEqual(len(CodeHTML(first).links), 2)

    def test_modified_unmatched_complete_fence_stays_lexical(self):
        guide = (self.root / 'guide.md').read_text()
        # Retain one exact unit, adding a near match with shifted byte offsets.
        self.input('guide.md', guide + '\n```ada\n' + self.text.replace('   Copy ', '    Copy ') + '```\n')
        enabled = self.publish()['guides/verified.html'].decode()
        disabled = render(replace(self.config, verified_examples={}), self.native)['guides/verified.html'].decode()
        self.assertEqual(len(CodeHTML(enabled).links), len(CodeHTML(disabled).links) + 4)
        self.assertEqual(enabled.rsplit('<pre', 1)[1], disabled.rsplit('<pre', 1)[1])

    def test_source_text_examples_still_must_appear_in_guides(self):
        self.input('guide.md', '# Verified calls\n\n```ada\nCopy := Image.Clone;\n```\n')
        with self.assertRaisesRegex(EnhancementError, 'missing from guides'): self.publish()

    def test_missing_project_and_wrong_directory_or_main_rejected(self):
        original = (self.root / 'docs/example.gpr').read_text()
        for project in (None, 'docs/wrong.gpr'):
            with self.subTest(project=project):
                self.data['example_project'] = project
                if project:
                    for changed in (original.replace('"."', '"elsewhere"'),
                                    original.replace('for Source_Files use ("example.adb")', 'for Source_Files use ("other.adb")'),
                                    original.replace('for Main use ("example.adb")', 'for Main use ("other.adb")')):
                        self.input(project, changed)
                        # Remove now-unused original project? It is still the landing project.
                        with self.assertRaisesRegex(EnhancementError, 'covered by'): self.publish()
                else:
                    with self.assertRaisesRegex(EnhancementError, 'build project'): self.publish()

    def test_duplicate_source_bytes_and_aliases_rejected(self):
        self.input('docs/duplicate.adb', self.text)
        self.data['examples'].append('docs/duplicate.adb')
        self.input('docs/both.gpr', 'project Both is\nfor Main use ("example.adb", "duplicate.adb");\nend Both;\n')
        self.data['example_project'] = 'docs/both.gpr'
        with self.assertRaisesRegex(EnhancementError, 'duplicate/conflicting'): self.publish()

    def test_build_project_must_belong_to_compiler_snapshot(self):
        self.input('docs/uncompiled.gpr', (self.root / 'docs/example.gpr').read_text())
        self.data['example_project'] = 'docs/uncompiled.gpr'
        with self.assertRaisesRegex(EnhancementError, 'build project not bound'): self.publish()

    def test_conditional_build_project_not_inferred(self):
        original = (self.root / 'docs/example.gpr').read_text()
        self.input('docs/example.gpr', original.replace('for Main use',
                   'case external ("CHOICE", "yes") is\nwhen "yes" => for Main use').replace(
                       'end Example;', 'end case;\nend Example;'))
        with self.assertRaisesRegex(EnhancementError, 'conditional'): self.publish()

    def test_unapproved_guide_source_mapping_rejected_even_when_rehashed(self):
        data = json.loads((self.root / 'mapping.json').read_text())
        # Existing mapping bytes cannot authorize an unlisted guide file.
        data['mappings'][0]['source']['file'] = 'guide.md'
        data['mappings'][0]['source']['sha256'] = digest((self.root / 'guide.md').read_bytes())
        data['inputs']['guide.md'] = data['mappings'][0]['source']['sha256']
        payload = sorted_json(data).encode(); (self.root / 'mapping.json').write_bytes(payload)
        self.config = replace(self.config, verified_examples={'mapping': 'mapping.json', 'sha256': digest(payload)})
        with self.assertRaisesRegex(EnhancementError, 'unowned/uncompiled'): self.publish()

    def test_landing_only_final_lfs_not_whitespace_or_shifted_offsets(self):
        resolver = Resolver(self.config, self.native, ['docs/example.adb'])
        expected = self.text.rstrip('\n')
        for changed in ('\n' + expected, expected + ' ', expected.replace('   Copy ', '    Copy ')):
            with self.subTest(changed=changed), self.assertRaisesRegex(EnhancementError, 'complete authoritative'):
                code(changed, resolver, landing=True, source='docs/example.adb')
        self.assertEqual(len(CodeHTML('<pre>' + code(expected, resolver, landing=True,
                                                   source='docs/example.adb') + '</pre>').links), 6)
        with self.assertRaisesRegex(EnhancementError, 'complete authoritative'):
            code(expected, resolver, source='docs/example.adb')

    def test_landing_content_mismatch_rejected_and_no_second_renderer(self):
        home = (self.root / 'home.html').read_text().replace('Image.Clone', 'Image.Clone ')
        self.input('home.html', home)
        with self.assertRaisesRegex(EnhancementError, 'landing example differs'): self.publish()
        with self.assertRaisesRegex(EnhancementError, 'exactly one authoritative'):
            landing(home, self.text)

    def test_disabled_verification_ignores_mapping_bytes(self):
        config = replace(self.config, verified_examples={})
        before = render(config, self.native)
        (self.root / 'mapping.json').unlink()
        self.assertEqual(before, render(config, self.native))


class ProductionCore(unittest.TestCase):
    def test_pinned_five_guides_38_fences_unchanged_and_home_six_links(self):
        from ada_gnatdoc_enhancer.authored import markdown
        with tempfile.TemporaryDirectory() as temp:
            config = production_core(Path(temp) / 'authority')
            native = snapshot(config, config.root / 'native')
            enabled = render(config, native)
            disabled = render(replace(config, verified_examples={}), native)
            data = json.loads((config.root / 'authored.json').read_text())
            self.assertEqual(data['ada_policy'], 'source-text')
            self.assertEqual(data['examples'], [])
            self.assertEqual(len(data['guides']), 5)
            fences = []
            for guide in data['guides']:
                self.assertEqual(enabled[guide['path']], disabled[guide['path']])
                fences.extend(markdown((config.root / guide['source']).read_text(), data['languages'])[2])
            self.assertEqual(len(fences), 38)
            self.assertEqual(len(CodeHTML(enabled['index.html'].decode()).links), 6)
            self.assertEqual(len(CodeHTML(disabled['index.html'].decode()).links), 2)
            self.assertEqual(''.join(CodeHTML(enabled['index.html'].decode()).text),
                             ''.join(CodeHTML(disabled['index.html'].decode()).text))


if __name__ == '__main__': unittest.main()