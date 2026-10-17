"""End-to-end CLI output-path policy, before project-root canonicalization."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from ada_gnatdoc_enhancer.conformance import tree_hashes

from _helper import Fixture


class CLISitePaths(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture();self.addCleanup(self.fx.cleanup)
        self.alias=self.fx.root.parent/'alias'
        self.alias.symlink_to(self.fx.root,target_is_directory=True)

    def call(self, command, root, site=None, *extra):
        args=[sys.executable,'-m','ada_gnatdoc_enhancer',command,
              '--source-root',str(root),'--config','project.toml']
        if site is not None:args.extend(('--site',str(site)))
        return subprocess.run([*args,*extra],capture_output=True,text=True)

    def rejected(self, root, site=None, command='enhance', extra=()):
        before=tree_hashes(self.fx.root)
        result=self.call(command,root,site,*extra)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertIn('symlink site path',result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        self.assertEqual(result.stdout,'')
        self.assertEqual(before,tree_hashes(self.fx.root))

    def test_alias_source_root_relative_site_rejected(self):
        self.rejected(self.alias,'_site')

    def test_alias_source_root_default_site_rejected(self):
        self.rejected(self.alias)

    def test_relative_alias_source_root_rejected(self):
        self.rejected(Path(os.path.relpath(self.alias,Path.cwd())),'_site')

    def test_source_root_with_symlink_ancestor_rejected(self):
        parent_alias=self.fx.root.parent/'parent-alias'
        parent_alias.symlink_to(self.fx.root.parent,target_is_directory=True)
        self.rejected(parent_alias/self.fx.root.name,'_site')

    def test_absolute_site_with_symlink_ancestor_rejected(self):
        self.rejected(self.fx.root,self.alias/'_site')

    def test_relative_site_with_symlink_ancestor_rejected(self):
        (self.fx.root/'output-alias').symlink_to(self.fx.site,target_is_directory=True)
        self.rejected(self.fx.root,'output-alias')

    def test_dry_run_and_verify_reject_alias_without_changes(self):
        self.rejected(self.alias,'_site',extra=('--dry-run',))
        result=self.call('enhance',self.fx.root,'_site')
        self.assertEqual(result.returncode,0,result.stderr)
        self.rejected(self.alias,'_site',command='verify')
        self.rejected(self.fx.root,self.alias/'_site',command='verify')

    def test_ordinary_relative_and_absolute_paths_succeed(self):
        relative_root=Path(os.path.relpath(self.fx.root,Path.cwd()))
        for root,site in ((relative_root,'_site'),(self.fx.root,self.fx.site)):
            with self.subTest(root=root,site=site):
                for command in ('enhance','verify'):
                    result=self.call(command,root,site)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(json.loads(result.stdout)['public_packages'],3)

    def test_alias_source_with_ordinary_absolute_site_preserves_identity(self):
        # Only the output path must be symlink-free; a separate canonical output
        # must not be rejected merely because the source was given via an alias.
        result=self.call('enhance',self.alias,self.fx.site)
        self.assertEqual(result.returncode,0,result.stderr)
        manifest=json.loads((self.fx.site/'api/presentation.json').read_text())
        self.assertEqual(set(manifest['source_sha256']),
                         {'src/opencv-core.ads','src/opencv-core-sparse.ads',
                          'src/opencv-core-vectors.ads'})
        result=self.call('verify',self.fx.root,self.fx.site)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()