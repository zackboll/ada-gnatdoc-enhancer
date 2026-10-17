"""Additional independent output-security and unsupported-state mutations."""
import json
import unittest
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.validation import validate_files
from _helper import Fixture

class SecurityMutations(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture('core');self.addCleanup(self.fx.cleanup)
        enhance(self.fx.config,self.fx.site)
        self.expected={p.relative_to(self.fx.site).as_posix() for p in self.fx.site.rglob('*') if p.is_file()}
        self.doc=next(p for p in self.fx.site.glob('api/[0-9a-f]*.html') if 'Convert' in p.read_text())

    def try_document_mutation(self,payload):
        original=self.doc.read_text()
        try:
            self.doc.write_text(original+payload)
            with self.assertRaises(EnhancementError):
                validate_files(self.fx.site,self.fx.config,self.expected)
        finally:self.doc.write_text(original)

    def test_disallowed_active_html(self):
        for token in ('<script src="gnatdoc-navigation.js" defer></script>',
                      '<p onclick="alert(1)">x</p>',
                      '<p style="color:red">x</p>',
                      '<iframe name=document-content></iframe>',
                      '<img src="gnatdoc.css">',
                      '<a href="javascript:alert(1)">x</a>',
                      '<a href="/etc/passwd">x</a>',
                      '<a href="../../outside">x</a>',
                      '<meta http-equiv="refresh" content="0">',
                      '<object data="file">x</object>',
                      '<a href="#wrong-fragment">x</a>',
                      '<a href="#wrong" href="#other">x</a>'):
            with self.subTest(payload=token):self.try_document_mutation(token)

    def test_duplicate_id_and_external_resources(self):
        for token in ('<div id="d"></div><div id="d"></div>',
                      '<a href="https://example.com">offsite</a>',
                      '<link rel="stylesheet" href="https://example.com/style.css">'):
            with self.subTest(payload=token):self.try_document_mutation(token)

    def test_existing_but_wrong_target_still_rejected(self):
        files=list(self.fx.site.glob('api/[0-9a-f]*.html'))
        path=next(p for p in files if 'type-reference' in p.read_text())
        original=path.read_text()
        self.assertIn('href=',original)
        import re
        x=re.search(r'(<a class="type-reference" href=")([^"]+)(")',original)
        self.assertIsNotNone(x)
        wrong=next(y for y in files if y!=path)
        path.write_text(original.replace(x[0],x[1]+wrong.name+x[3],1))
        with self.assertRaisesRegex(EnhancementError,'published file differs'):
            verify(self.fx.config,self.fx.site)

    def test_symlink_presentation_file_rejected(self):
        path=self.fx.site/'api/gnatdoc-theme.css'
        clone=self.fx.site/'api/style-shadow.txt'
        clone.write_bytes(path.read_bytes())
        path.unlink();path.symlink_to(clone)
        with self.assertRaises(EnhancementError):verify(self.fx.config,self.fx.site)

    def test_altered_manifest_schema_rejected(self):
        path=self.fx.site/'api/presentation.json'
        obj=json.loads(path.read_text())
        obj['extra']='unknown'
        path.write_text(json.dumps(obj))
        with self.assertRaisesRegex(EnhancementError,'unexpected presentation manifest fields'):
            verify(self.fx.config,self.fx.site)

    def test_missing_package_rejected_before_enhance(self):
        fx=Fixture('imgproc');self.addCleanup(fx.cleanup)
        raw=next(p for p in fx.site.glob('api/[0-9a-f]*.html'))
        raw.unlink()
        with self.assertRaisesRegex(EnhancementError,'source/native package mismatch'):
            enhance(fx.config,fx.site)

    def test_mel_exact_renderer_exception_is_source_bound(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        path=fx.root/'src/ams-mel-ir-health_status-metadata.ads'
        path.write_text(path.read_text().replace('package Status renames AMS.MEL.Status;',
                                                '-- package Status renames AMS.MEL.Status;'))
        with self.assertRaisesRegex(EnhancementError,'renderer exception lacks exact source alias'):
            enhance(fx.config,fx.site)

    def test_mel_stale_exception_not_credited(self):
        fx=Fixture('mel');self.addCleanup(fx.cleanup)
        native=snapshot(fx.config,fx.site)
        path=native.pages['ams.mel.ir.health_status.metadata'].path
        text=path.read_text()
        text=text.replace('</body></html>',
             '<h4 id='+('a'*64)+'>Status</h4><pre class=ada-code-snippet><code>'
             'package Status renames AMS.MEL.Status;</code></pre></body></html>')
        path.write_text(text)
        with self.assertRaisesRegex(EnhancementError,'become rendered'):
            enhance(fx.config,fx.site)

if __name__=='__main__':unittest.main()
