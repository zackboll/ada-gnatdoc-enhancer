"""Source-preserving enhancement, output reconstruction and publication security."""
import json
import unittest
from pathlib import Path

from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.util import digest
from ada_gnatdoc_enhancer.validation import css_safe,validate_files

from _helper import Fixture

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture('core');self.addCleanup(self.fx.cleanup)

    def test_clean_enhance_verify_and_idempotence(self):
        r=enhance(self.fx.config,self.fx.site)
        self.assertEqual(r['mode'],'enhanced')
        self.assertEqual(r['public_packages'],3)
        self.assertGreaterEqual(r['linked_types'],3)
        files={x.relative_to(self.fx.site).as_posix():digest(x.read_bytes())
               for x in self.fx.site.rglob('*') if x.is_file()}
        verified=verify(self.fx.config,self.fx.site)
        self.assertEqual(verified['mode'],'verified')
        enhance(self.fx.config,self.fx.site)
        self.assertEqual(files,{x.relative_to(self.fx.site).as_posix():digest(x.read_bytes())
                                for x in self.fx.site.rglob('*') if x.is_file()})

    def test_dry_run_is_nonmutating(self):
        before={x.relative_to(self.fx.site).as_posix():digest(x.read_bytes())
                for x in self.fx.site.rglob('*') if x.is_file()}
        r=enhance(self.fx.config,self.fx.site,dry_run=True)
        self.assertEqual(r['mode'],'dry-run')
        self.assertEqual(before,{x.relative_to(self.fx.site).as_posix():digest(x.read_bytes())
                                 for x in self.fx.site.rglob('*') if x.is_file()})

    def test_changed_native_css_fails(self):
        enhance(self.fx.config,self.fx.site)
        p=self.fx.site/'api/gnatdoc.css';p.write_text('/* compromised */')
        with self.assertRaisesRegex(EnhancementError,'native GNATdoc stylesheet'):
            verify(self.fx.config,self.fx.site)

    def test_changed_presentation_css_fails(self):
        enhance(self.fx.config,self.fx.site)
        p=self.fx.site/'api/gnatdoc-theme.css';p.write_text('body { color:red; }')
        with self.assertRaisesRegex(EnhancementError,'published file differs'):
            verify(self.fx.config,self.fx.site)

    def test_changed_navigation_javascript_fails(self):
        enhance(self.fx.config,self.fx.site)
        p=self.fx.site/'api/gnatdoc-navigation.js';p.write_text('alert(1)')
        with self.assertRaisesRegex(EnhancementError,'published file differs'):
            verify(self.fx.config,self.fx.site)

    def test_extra_asset_rejected(self):
        enhance(self.fx.config,self.fx.site)
        (self.fx.site/'extra.html').write_text('<script>alert(1)</script>')
        with self.assertRaisesRegex(EnhancementError,'unapproved output file'):
            verify(self.fx.config,self.fx.site)

    def test_source_mutation_rejected(self):
        enhance(self.fx.config,self.fx.site)
        p=self.fx.root/'src/opencv-core.ads'
        p.write_text(p.read_text()+'\n-- modified\n')
        with self.assertRaisesRegex(EnhancementError,'source differs'):
            verify(self.fx.config,self.fx.site)

    def test_broken_fragment_rejected(self):
        enhance(self.fx.config,self.fx.site)
        p=self.fx.site/'api/index.html'
        p.write_text(p.read_text().replace('href=#compilation-units','href=#absent'))
        with self.assertRaisesRegex(EnhancementError,'published file differs'):
            verify(self.fx.config,self.fx.site)

    def test_native_output_corrupted_with_manifest_rewrite_fails(self):
        enhance(self.fx.config,self.fx.site)
        mani=self.fx.site/'api/presentation.json'
        obj=json.loads(mani.read_text())
        # The manifest cannot approve a fake source declaration profile.
        name=next(p for p in obj['original_api_html'] if 'Convert' in obj['original_api_html'][p])
        obj['original_api_html'][name]=obj['original_api_html'][name].replace(
            'Convert (Source : Mat) return Mat','Convert (Source : Natural) return Mat')
        mani.write_text(json.dumps(obj))
        with self.assertRaisesRegex(EnhancementError,'native declaration profile unmatched'):
            verify(self.fx.config,self.fx.site)

    def test_safety_html_script_injection(self):
        enhance(self.fx.config,self.fx.site)
        path=next(self.fx.site.glob('api/[0-9a-f]*.html'))
        path.write_text(path.read_text()+'<script src="gnatdoc-navigation.js" defer></script>')
        with self.assertRaises(EnhancementError):verify(self.fx.config,self.fx.site)

    def test_symlink_extra_rejected(self):
        enhance(self.fx.config,self.fx.site)
        (self.fx.site/'bad').symlink_to(self.fx.site/'api/index.html')
        with self.assertRaisesRegex(EnhancementError,'symlink published'):
            verify(self.fx.config,self.fx.site)

    def test_css_invalid_resources(self):
        for unsafe in (b'@import "https://example.org/s.css";',b'body{background:url(https://bad)}',
                       b'@im\\70ort "https://example.org/x.css";',b'body{background:u/**/rl(x)}'):
            with self.subTest(source=unsafe):
                with self.assertRaises(EnhancementError):css_safe(unsafe)

if __name__=='__main__':unittest.main()
