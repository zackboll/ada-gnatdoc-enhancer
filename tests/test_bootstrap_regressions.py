"""Qualification regressions for immutable inputs and conservative presentation."""
import json
import re
import shutil
import subprocess
import sys
import unittest
from dataclasses import replace

from ada_gnatdoc_enhancer.conformance import tree_hashes
from ada_gnatdoc_enhancer.errors import EnhancementError
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot, verified_types
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.syntax import CODE, TYPE_LINK, plain, resolve
from ada_gnatdoc_enhancer.validation import Page

from _helper import Fixture


class BootstrapRegressions(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture('core');self.addCleanup(self.fx.cleanup)

    def cli(self, command='enhance'):
        return subprocess.run(
            [sys.executable,'-m','ada_gnatdoc_enhancer',command,
             '--source-root',str(self.fx.root),'--config','project.toml'],
            capture_output=True,text=True)

    def test_unknown_passive_elements_and_native_text_preserved(self):
        native=snapshot(self.fx.config,self.fx.site)
        page=native.pages['opencv.core'].path
        unknown='<aside data-vendor="future"><details><summary>Extra</summary><p>Keep &amp; preserve.</p></details></aside>'
        page.write_text(page.read_text().replace('</body>',unknown+'</body>'),encoding='utf-8')
        originals={p.name:p.read_text(encoding='utf-8') for p in self.fx.site.glob('api/*.html')}
        css=(self.fx.site/'api/gnatdoc.css').read_bytes()
        enhance(self.fx.config,self.fx.site)
        self.assertIn(unknown,page.read_text(encoding='utf-8'))
        self.assertEqual(css,(self.fx.site/'api/gnatdoc.css').read_bytes())
        for name,original in originals.items():
            rendered=(self.fx.site/'api'/name).read_text(encoding='utf-8')
            native_ids=Page(original).ids
            self.assertEqual(native_ids,[identity for identity in Page(rendered).ids if identity in native_ids])
            self.assertEqual([plain(m[2]) for m in CODE.finditer(original)],
                             [plain(m[2]) for m in CODE.finditer(rendered)])
        verify(self.fx.config,self.fx.site)

    def test_no_duplicate_injections_on_any_profile(self):
        for profile in ('core','imgproc','geometry','mel'):
            with self.subTest(profile=profile):
                fx=Fixture(profile);self.addCleanup(fx.cleanup)
                enhance(fx.config,fx.site)
                before=tree_hashes(fx.site)
                enhance(fx.config,fx.site)
                self.assertEqual(before,tree_hashes(fx.site))
                for page in fx.site.glob('api/*.html'):
                    text=page.read_text(encoding='utf-8')
                    self.assertEqual(text.count('<link rel="stylesheet" href="gnatdoc-theme.css">'),1)
                    self.assertEqual(text.count('<script src="gnatdoc-navigation.js" defer></script>'),
                                     int(page.name=='index.html'))
                verify(fx.config,fx.site)

    def test_missing_input_leaves_project_unchanged(self):
        shutil.rmtree(self.fx.site)
        before=tree_hashes(self.fx.root)
        result=self.cli()
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        self.assertEqual(before,tree_hashes(self.fx.root))

    def test_malformed_native_input_is_transactional(self):
        page=snapshot(self.fx.config,self.fx.site).pages['opencv.core'].path
        page.write_text(page.read_text().replace('<h1>','<h2>'),encoding='utf-8')
        before=tree_hashes(self.fx.root)
        result=self.cli()
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        self.assertEqual(before,tree_hashes(self.fx.root))

    def test_malformed_toml_is_reported_without_traceback(self):
        (self.fx.root/'project.toml').write_text('schema_version = [',encoding='utf-8')
        result=self.cli()
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_nonobject_manifest_is_reported_without_traceback(self):
        enhance(self.fx.config,self.fx.site)
        manifest=self.fx.site/'api/presentation.json'
        for value in (None,1,[],[{}],"invalid"):
            with self.subTest(value=value):
                manifest.write_text(json.dumps(value),encoding='utf-8')
                result=self.cli('verify')
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertNotIn('Traceback',result.stderr)
                self.assertIn('presentation manifest',result.stderr)

    def test_no_links_to_unknown_or_ambiguous_symbols(self):
        source=packages(self.fx.config)
        native=snapshot(self.fx.config,self.fx.site)
        targets=verified_types(native,source)
        pkg=source['opencv.core']
        self.assertIsNone(resolve('Missing',pkg,source,targets,{}))
        self.assertIsNone(resolve('OpenCV.Core.Missing',pkg,source,targets,{}))
        imported=replace(pkg,name='Client',imports=frozenset({'one','two'}),
                         uses=frozenset({'one','two'}))
        ambiguous={'one.mat':targets['opencv.core.mat'],'two.mat':targets['opencv.core.mat']}
        self.assertIsNone(resolve('Mat',imported,source,ambiguous,{}))
        self.assertEqual(resolve('One.Mat',imported,source,ambiguous,{}),('one.mat','local'))

    def test_unresolved_reference_remains_plain_text(self):
        native=snapshot(self.fx.config,self.fx.site)
        page=native.pages['opencv.core'].path
        signature='function External (Item : Missing_Type) return Missing_Type;'
        source=self.fx.root/'src/opencv-core.ads'
        source.write_text(source.read_text().replace('end OpenCV.Core;',signature+'\nend OpenCV.Core;'),encoding='utf-8')
        section='<h4 id="'+('f'*64)+'">External</h4><pre class=ada-code-snippet><code>'+signature+'</code></pre>'
        page.write_text(page.read_text().replace('</body>',section+'</body>'),encoding='utf-8')
        enhance(self.fx.config,self.fx.site)
        text=page.read_text(encoding='utf-8')
        self.assertNotIn('missing_type',[m[2] for m in TYPE_LINK.finditer(text)])
        self.assertIn(signature,[plain(m[2]) for m in CODE.finditer(text)])
        verify(self.fx.config,self.fx.site)

    def test_missing_real_type_anchor_is_not_invented(self):
        native=snapshot(self.fx.config,self.fx.site)
        page=native.pages['opencv.core'].path
        page.write_text(re.sub(r'<h4 id=[^>]+>Mat</h4>\s*<pre.*?</pre>','',page.read_text(),count=1,flags=re.S),encoding='utf-8')
        before=tree_hashes(self.fx.root)
        with self.assertRaisesRegex(EnhancementError,'native declaration profile unmatched'):
            enhance(self.fx.config,self.fx.site)
        self.assertEqual(before,tree_hashes(self.fx.root))

    def test_subtype_links_use_real_anchors(self):
        native=snapshot(self.fx.config,self.fx.site)
        page=native.pages['opencv.core'].path
        signatures=('subtype Mat_View is Mat;', 'function View return Mat_View;')
        source=self.fx.root/'src/opencv-core.ads'
        source.write_text(source.read_text().replace('end OpenCV.Core;','\n'.join(signatures)+'\nend OpenCV.Core;'),encoding='utf-8')
        sections=''.join('<h4 id="'+char*64+'">'+name+'</h4><pre class=ada-code-snippet><code>'+sig+'</code></pre>'
                         for char,name,sig in zip('ef',('Mat_View','View'),signatures))
        page.write_text(page.read_text().replace('</body>',sections+'</body>'),encoding='utf-8')
        enhance(self.fx.config,self.fx.site)
        links={m[2]:m[1] for m in TYPE_LINK.finditer(page.read_text(encoding='utf-8'))}
        self.assertEqual(links['opencv.core.mat_view'],page.name+'#'+'e'*64)
        verify(self.fx.config,self.fx.site)

    def test_relative_paths_under_nested_output_location(self):
        destination=self.fx.root/'build/docs/deep/site'
        destination.parent.mkdir(parents=True)
        shutil.move(str(self.fx.site),destination)
        enhance(self.fx.config,destination)
        for page in destination.glob('api/*.html'):
            parsed=Page(page.read_text(encoding='utf-8'))
            self.assertIn('gnatdoc-theme.css',parsed.links)
            for link in parsed.links:
                self.assertFalse(link.startswith('/'),link)
                target=link.split('#')[0]
                self.assertTrue((page.parent/target if target else page).is_file(),link)
        verify(self.fx.config,destination)

    def test_only_output_directory_changes(self):
        sentinel=self.fx.root/'unrelated.txt';sentinel.write_bytes(b'untouched\n')
        before={n:h for n,h in tree_hashes(self.fx.root).items() if not n.startswith('_site/')}
        enhance(self.fx.config,self.fx.site)
        enhance(self.fx.config,self.fx.site)
        self.assertEqual(before,{n:h for n,h in tree_hashes(self.fx.root).items() if not n.startswith('_site/')})

    def test_symlink_site_root_is_rejected_without_writes(self):
        alias=self.fx.root/'alias';alias.symlink_to(self.fx.site,target_is_directory=True)
        before=tree_hashes(self.fx.site)
        with self.assertRaisesRegex(EnhancementError,'symlink'):
            enhance(self.fx.config,alias)
        self.assertEqual(before,tree_hashes(self.fx.site))

    def test_symlink_site_ancestor_is_rejected_without_writes(self):
        alias=self.fx.root/'alias';alias.symlink_to(self.fx.root,target_is_directory=True)
        before=tree_hashes(self.fx.site)
        with self.assertRaisesRegex(EnhancementError,'symlink'):
            enhance(self.fx.config,alias/'_site')
        self.assertEqual(before,tree_hashes(self.fx.site))

    def test_symlink_api_directory_is_rejected_without_writes(self):
        external=self.fx.root/'external-api'
        shutil.move(str(self.fx.site/'api'),external)
        (self.fx.site/'api').symlink_to(external,target_is_directory=True)
        before=tree_hashes(external)
        with self.assertRaisesRegex(EnhancementError,'symlink'):
            enhance(self.fx.config,self.fx.site)
        self.assertEqual(before,tree_hashes(external))

    def test_verify_rejects_symlink_site_root(self):
        enhance(self.fx.config,self.fx.site)
        alias=self.fx.root/'alias';alias.symlink_to(self.fx.site,target_is_directory=True)
        with self.assertRaisesRegex(EnhancementError,'symlink'):
            verify(self.fx.config,alias)


if __name__=='__main__':unittest.main()