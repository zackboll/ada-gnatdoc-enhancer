"""Additive release contracts; installed archive auditing is a separate gate."""
from dataclasses import replace
import json
from pathlib import Path
import tomllib
import unittest

from ada_gnatdoc_enhancer import __version__
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from _helper import Fixture


class ReleaseContracts(unittest.TestCase):
    def test_source_metadata_version_license_and_python(self):
        root = Path(__file__).resolve().parents[1]
        metadata = tomllib.loads((root/'pyproject.toml').read_text())['project']
        self.assertEqual(metadata['version'], __version__)
        self.assertEqual(__version__, '0.1.0')
        self.assertEqual(metadata['license'], 'Apache-2.0')
        self.assertEqual(metadata['license-files'], ['LICENSE'])
        self.assertEqual(metadata['requires-python'], '>=3.11')
        self.assertEqual(metadata['dependencies'], [])
        self.assertEqual(metadata['optional-dependencies']['guides'],
                         ['markdown-it-py==3.0.0', 'mdurl==0.1.2'])

    def test_presentation_manifest_is_release_version_bound(self):
        fx = Fixture(); self.addCleanup(fx.cleanup)
        enhance(fx.config, fx.site)
        manifest = fx.site/'api/presentation.json'
        data = json.loads(manifest.read_text())
        self.assertEqual(data['enhancer_version'], '0.1.0')
        data['enhancer_version'] = '0.1.0.dev0'
        manifest.write_text(json.dumps(data))
        before = hashes(fx.site)
        with self.assertRaises(EnhancementError):verify(fx.config, fx.site)
        self.assertEqual(before, hashes(fx.site))

    def test_default_and_symbol_only_router_byte_contracts(self):
        for symbols, expected in [(False, 'b3fb428b507844d6be76fb40156058d39a5b5f57004bde04e33b0411f68504cd'),
                                  (True, '233cf43211a711d0d64dfba2815bc2d9cc887720faed0ca38f464bc6d29e145f')]:
            with self.subTest(symbols=symbols):
                fx = Fixture(); self.addCleanup(fx.cleanup)
                config = replace(fx.config, symbol_bookmarks=symbols,
                                 default_package='OpenCV.Core' if symbols else '')
                enhance(config, fx.site)
                self.assertEqual(hashes(fx.site)['api/gnatdoc-navigation.js'], expected)