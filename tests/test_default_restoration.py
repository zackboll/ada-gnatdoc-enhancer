"""Publication/security boundaries of the default-only runtime correction."""
import json
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.pipeline import enhance, expected_output, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.theme import asset
from ada_gnatdoc_enhancer.util import digest
from _helper import Fixture


class DefaultRestoration(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(); self.addCleanup(self.fx.cleanup)

    def test_independent_router_assets_unchanged(self):
        self.assertEqual(digest(asset('gnatdoc-symbol-navigation.js')),
                         '233cf43211a711d0d64dfba2815bc2d9cc887720faed0ca38f464bc6d29e145f')
        self.assertEqual(digest(asset('gnatdoc-instance-navigation.js')),
                         '97dcc75055842e98a6294809b8e8c4e7436a427039d19c8afb6fdd1ca21ea310')

    def test_default_manifest_binds_exact_shipped_runtime(self):
        enhance(self.fx.config, self.fx.site)
        data = json.loads((self.fx.site/'api/presentation.json').read_text())
        runtime = (self.fx.site/'api/gnatdoc-navigation.js').read_bytes()
        self.assertEqual(runtime, asset('gnatdoc-navigation.js'))
        self.assertEqual(data['output_sha256']['api/gnatdoc-navigation.js'], digest(runtime))
        before = hashes(self.fx.site); enhance(self.fx.config, self.fx.site)
        verify(self.fx.config, self.fx.site); self.assertEqual(before, hashes(self.fx.site))

    def test_navigation_disabled_does_not_publish_runtime(self):
        config = replace(self.fx.config, navigation='none')
        _, outputs, _ = expected_output(config, self.fx.site)
        self.assertNotIn('api/gnatdoc-navigation.js', outputs)
        self.assertNotIn(b'gnatdoc-navigation.js', outputs['api/index.html'])

    def test_rehashed_runtime_forgery_is_rejected(self):
        enhance(self.fx.config, self.fx.site)
        runtime = self.fx.site/'api/gnatdoc-navigation.js'
        runtime.write_bytes(runtime.read_bytes()+b'\n/* unauthorized */\n')
        manifest = self.fx.site/'api/presentation.json'
        data = json.loads(manifest.read_text())
        data['output_sha256']['api/gnatdoc-navigation.js'] = digest(runtime.read_bytes())
        manifest.write_text(json.dumps(data))
        with self.assertRaises(EnhancementError):verify(self.fx.config, self.fx.site)

    def test_default_output_mutations_remain_rejected(self):
        enhance(self.fx.config, self.fx.site)
        index = self.fx.site/'api/index.html'; original = index.read_bytes()
        for payload in (b'<script>alert(1)</script>', b'<a onclick="alert(1)">bad</a>'):
            with self.subTest(payload=payload):
                try:
                    index.write_bytes(original+payload)
                    with self.assertRaises(EnhancementError):verify(self.fx.config, self.fx.site)
                finally:index.write_bytes(original)
        extra = self.fx.site/'api/unauthorized.js'; extra.write_text('/* extra */')
        with self.assertRaises(EnhancementError):verify(self.fx.config, self.fx.site)
        extra.unlink(); verify(self.fx.config, self.fx.site)