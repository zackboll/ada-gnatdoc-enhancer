"""Source/configuration, never generated metadata, approve custom CSS bytes."""
import json
import shutil
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.theme import asset, theme_asset
from ada_gnatdoc_enhancer.util import digest, sorted_json
from ada_gnatdoc_enhancer.validation import css_safe
from _helper import Fixture


CSS = b''':root { --page: #fff; --link: #1556a5; }
@media (prefers-color-scheme: dark) { :root { --page: #141b26; } }
.landing { max-width: 64rem; margin: auto; }
.eyebrow { text-transform: uppercase; letter-spacing: .12em; }
.lead { font-size: 1.2rem; }
.api-button { display: inline-block; background: var(--link); }
.landing nav { display: flex; flex-wrap: wrap; }
h4:target { background: var(--page); }
a:focus-visible { outline: 3px solid var(--link); }
.generic-instance-summary { border: 1px solid; padding: 1rem; }
.generic-instance-summary h2 { margin-top: 0; }
.generic-instance-summary table { table-layout: fixed; }
'''


class CustomTheme(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture('core'); self.addCleanup(self.fx.cleanup)
        self.path = self.fx.root/'project.toml'
        self.original = self.path.read_text()
        self.css = self.fx.root/'theme.css'; self.css.write_bytes(CSS)

    def configure(self, source='theme.css', sha=None, enabled=True):
        text = self.original.split('[presentation]')[0] + '\n[presentation]\n'
        text += f'theme = {str(enabled).lower()}\n'
        if source is not None:
            text += 'theme_css_source = ' + json.dumps(source) + '\n'
        if sha is not False:
            text += f'theme_css_sha256 = "{sha if sha is not None else digest(CSS)}"\n'
        self.path.write_text(text)
        return load(self.fx.root, 'project.toml')

    def test_exact_bytes_html_contract_and_default_delta(self):
        default = self.fx.root/'default'; shutil.copytree(self.fx.site, default)
        enhance(self.fx.config, default)
        c = self.configure(); enhance(c, self.fx.site); verify(c, self.fx.site)
        self.assertEqual((self.fx.site/'api/gnatdoc-theme.css').read_bytes(), CSS)
        a = hashes(default); b = hashes(self.fx.site)
        self.assertEqual([n for n in a if a[n] != b[n]],
                         ['api/gnatdoc-theme.css', 'api/presentation.json'])
        self.assertNotIn('theme_source', json.loads((default/'api/presentation.json').read_text()))

    def test_default_ignores_unconfigured_consumer_css(self):
        self.css.write_bytes(b'@import "bad";')
        enhance(self.fx.config, self.fx.site)
        self.assertEqual((self.fx.site/'api/gnatdoc-theme.css').read_bytes(), asset('gnatdoc-theme.css'))

    def test_determinism_and_idempotence(self):
        second = self.fx.root/'second'; shutil.copytree(self.fx.site, second)
        c = self.configure(); enhance(c, self.fx.site); before = hashes(self.fx.site)
        enhance(c, self.fx.site); enhance(c, second)
        self.assertEqual(before, hashes(self.fx.site)); self.assertEqual(before, hashes(second))

    def test_missing_source(self):
        with self.assertRaises(EnhancementError): self.configure('missing.css')

    def test_missing_hash(self):
        with self.assertRaises(EnhancementError): self.configure(sha=False)

    def test_missing_source_field(self):
        with self.assertRaises(EnhancementError): self.configure(source=None)

    def test_invalid_hash(self):
        for sha in ('', 'a'*63, 'a'*65, 'G'*64, 'A'*64):
            with self.subTest(sha=sha), self.assertRaises(EnhancementError): self.configure(sha=sha)

    def test_source_hash_mismatch(self):
        with self.assertRaises(EnhancementError): self.configure(sha='0'*64)

    def test_wrong_existing_source(self):
        (self.fx.root/'wrong.css').write_bytes(b'body{}')
        with self.assertRaises(EnhancementError): self.configure('wrong.css')

    def test_theme_disabled(self):
        with self.assertRaises(EnhancementError): self.configure(enabled=False)

    def test_unsafe_paths(self):
        for source in ('/tmp/theme.css', '../theme.css', 'a/../theme.css',
                       './theme.css', 'a//theme.css', 'C:/theme.css', 'a\\theme.css',
                       'theme%2ecss', 'theme.css#x', 'theme.css?x'):
            with self.subTest(source=source), self.assertRaises(EnhancementError): self.configure(source)

    def test_symlink_file(self):
        (self.fx.root/'link.css').symlink_to(self.css)
        with self.assertRaises(EnhancementError): self.configure('link.css')

    def test_symlink_ancestor_within_root(self):
        (self.fx.root/'assets').mkdir(); (self.fx.root/'assets/theme.css').write_bytes(CSS)
        (self.fx.root/'link').symlink_to(self.fx.root/'assets', target_is_directory=True)
        with self.assertRaises(EnhancementError): self.configure('link/theme.css')

    def test_symlink_root(self):
        self.configure()
        link = self.fx.root.parent/'root-link'; link.symlink_to(self.fx.root, target_is_directory=True)
        with self.assertRaises(EnhancementError): load(link, 'project.toml')

    def test_symlink_config(self):
        self.configure(); p = self.fx.root/'link.toml'; p.symlink_to(self.path)
        with self.assertRaises(EnhancementError): load(self.fx.root, 'link.toml')

    def test_source_changed_after_load_atomic_failure(self):
        c = self.configure(); before = hashes(self.fx.site)
        self.css.write_bytes(CSS + b'/* changed */')
        with self.assertRaises(EnhancementError): enhance(c, self.fx.site)
        self.assertEqual(before, hashes(self.fx.site))

    def test_source_changed_after_enhancement(self):
        c = self.configure(); enhance(c, self.fx.site); self.css.write_bytes(CSS + b' ')
        with self.assertRaises(EnhancementError): verify(c, self.fx.site)

    def test_config_changed_after_load(self):
        c = self.configure(); self.path.write_text(self.path.read_text() + '\n# changed\n')
        with self.assertRaises(EnhancementError): enhance(c, self.fx.site)

    def test_reloaded_config_identity_changed_after_enhancement(self):
        c = self.configure(); enhance(c, self.fx.site)
        self.path.write_text(self.path.read_text() + '\n# changed\n')
        with self.assertRaises(EnhancementError): verify(load(self.fx.root, 'project.toml'), self.fx.site)

    def test_same_bytes_different_source_identity(self):
        c = self.configure(); enhance(c, self.fx.site)
        (self.fx.root/'copy.css').write_bytes(CSS)
        with self.assertRaises(EnhancementError): verify(self.configure('copy.css'), self.fx.site)

    def test_symlink_substitution_after_enhancement(self):
        c = self.configure(); enhance(c, self.fx.site)
        copy = self.fx.root/'copy.css'; copy.write_bytes(CSS)
        self.css.unlink(); self.css.symlink_to(copy)
        with self.assertRaises(EnhancementError): verify(c, self.fx.site)

    def test_output_mutation(self):
        c = self.configure(); enhance(c, self.fx.site)
        (self.fx.site/'api/gnatdoc-theme.css').write_bytes(b'body{}')
        with self.assertRaises(EnhancementError): verify(c, self.fx.site)

    def test_rehashed_output_manifest_cannot_approve_theme(self):
        c = self.configure(); enhance(c, self.fx.site)
        changed = b'body{color:red}'
        (self.fx.site/'api/gnatdoc-theme.css').write_bytes(changed)
        p = self.fx.site/'api/presentation.json'; data = json.loads(p.read_text())
        data['output_sha256']['api/gnatdoc-theme.css'] = digest(changed)
        data['theme_source']['sha256'] = digest(changed); p.write_text(sorted_json(data))
        with self.assertRaises(EnhancementError): verify(c, self.fx.site)

    def test_extra_output_asset(self):
        c = self.configure(); enhance(c, self.fx.site)
        (self.fx.site/'api/extra.css').write_bytes(CSS)
        with self.assertRaises(EnhancementError): verify(c, self.fx.site)

    def test_default_selection_cannot_verify_custom_publication(self):
        c = self.configure(); enhance(c, self.fx.site)
        with self.assertRaises(EnhancementError): verify(self.fx.config, self.fx.site)

    def test_direct_config_requires_loaded_identity(self):
        c = replace(self.fx.config, theme_css_source='theme.css', theme_css_sha256=digest(CSS))
        with self.assertRaises(EnhancementError): theme_asset(c)

    def test_dataclass_override_cannot_bypass_approved_config(self):
        c = self.configure(); self.css.write_bytes(b'body{}')
        with self.assertRaises(EnhancementError): theme_asset(replace(c, theme_css_sha256=digest(b'body{}')))

    def test_invalid_encoding(self):
        for content in (b'\xff', b'\xff\xfea\x00', b'\xef\xbb\xbfbody{}', b'body{\x00}'):
            with self.subTest(content=content):
                self.css.write_bytes(content)
                with self.assertRaises(EnhancementError): self.configure(sha=digest(content))

    def test_unsafe_resources_and_execution(self):
        for text in ('@import "https://bad/x.css";', '@IMPORT "local.css";',
                     'a{background:url(local.png)}', 'a{background:u/**/rl(https://bad)}',
                     r'@im\70ort "bad";', r'a{background:u\72l(x)}',
                     'a{width:expression(alert(1))}', 'a{behavior:script.htc}',
                     'a{-moz-binding:url(x)}', '@charset "iso-8859-1";',
                     'a{background:image-set("https://bad" 1x)}',
                     'a{background:-webkit-image-set("local.png" 1x)}',
                     'a{background:image("local.png")}', '@font-face{src:local(x)}',
                     'a{background:src("https://bad")} ',
                     'a{filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src="bad")}',
                     '@document "https://bad" {}'):
            content = text.encode(); self.css.write_bytes(content)
            with self.subTest(text=text), self.assertRaises(EnhancementError):
                self.configure(sha=digest(content))

    def test_positive_core_rule_shapes(self):
        css_safe(CSS); self.assertEqual(theme_asset(self.configure()), CSS)