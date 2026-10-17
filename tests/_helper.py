"""Synthetic GNATdoc 26 fixtures are explicit, immutable regression inputs."""
from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from ada_gnatdoc_enhancer.config import load

FIXTURES = Path(__file__).resolve().parent/'fixtures'

class Fixture:
    def __init__(self, name='core'):
        self.temp=tempfile.TemporaryDirectory(prefix='ada-gde-fixture-')
        self.root=Path(self.temp.name)/name
        shutil.copytree(FIXTURES/name,self.root)
        self.config=load(self.root,'project.toml')
        self.site=self.root/'_site'
    def cleanup(self):self.temp.cleanup()
