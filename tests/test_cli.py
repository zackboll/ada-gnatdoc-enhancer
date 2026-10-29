"""CLI exit statuses, safe dry-run semantics and registered commands."""
import subprocess
import sys
import unittest
from pathlib import Path
from _helper import Fixture

class CLI(unittest.TestCase):
    def setUp(self):self.fx=Fixture();self.addCleanup(self.fx.cleanup)
    def call(self,*args):
        return subprocess.run([sys.executable,'-m','ada_gnatdoc_enhancer',*args],
                              capture_output=True,text=True)
    def test_version(self):
        r=self.call('--version')
        self.assertEqual(r.returncode,0)
        self.assertEqual(r.stdout.strip(),'0.1.2')
    def test_inventory(self):
        r=self.call('inventory','--config','project.toml','--source-root',str(self.fx.root))
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('OpenCV.Core',r.stdout)
    def test_enhance_then_verify(self):
        base=['--config','project.toml','--source-root',str(self.fx.root)]
        self.assertEqual(self.call('enhance',*base).returncode,0)
        self.assertEqual(self.call('verify',*base).returncode,0)
    def test_bad_config_exits_nonzero(self):
        p=self.fx.root/'project.toml'
        p.write_text(p.read_text().replace('26.0.0','99.0.0'))
        r=self.call('enhance','--config','project.toml','--source-root',str(self.fx.root))
        self.assertEqual(r.returncode,2)
        self.assertIn('unsupported',r.stderr)

if __name__=='__main__':unittest.main()
