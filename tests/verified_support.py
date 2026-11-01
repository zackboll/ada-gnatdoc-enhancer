"""Reconstruction of retained mixed/production publishing fixtures for qualification."""
from dataclasses import replace
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.util import digest, sorted_json

FIXTURES = Path(__file__).parent / 'verified-fixtures'


def mixed_core(root):
    """Overlay only publishing inputs, preserving authentic source/compiler evidence."""
    shutil.copytree(FIXTURES / 'core', root)
    for name in ('home.html', 'guide.md'):
        shutil.copyfile(FIXTURES / 'mixed-core' / name, root / name)
    data = json.loads((root / 'authored.json').read_text())
    data['ada_policy'] = 'source-text'
    for name in ('home.html', 'guide.md'):
        data['inputs'][name] = digest((root / name).read_bytes())
    payload = sorted_json(data).encode(); (root / 'authored.json').write_bytes(payload)
    config = load(root, 'project.toml')
    return replace(config, guide_sha256=digest(payload), ada_landing_example_highlighting=True), data


def production_core(root):
    """Reconstruct pinned Core homepage and all five original guides, without edits.

    Historical fixture supplies unchanged inputs; retained current overlays supply
    only bytes changed at dbdb410. Compiler inputs remain outside the public scan.
    """
    shutil.copytree(FIXTURES.parents[0] / 'authored-fixtures/core', root)
    compiler = FIXTURES / 'core'
    mapping = json.loads((FIXTURES / 'mixed-core/production/mapping.json').read_text())
    for name in mapping['inputs']:
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(compiler / name, target)
    shutil.copytree(FIXTURES / 'mixed-core/production', root, dirs_exist_ok=True)
    shutil.copyfile(compiler / 'public/opencv-core.ads', root / 'source/src/opencv-core.ads')
    shutil.copyfile(compiler / 'native/api/6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html',
                    root / 'native/api/6913f2e7169ad4fb9224d4d93fd20e50615a317c7374a7e469bab89cdd6bb7e9.html')
    config = load(root, 'project.toml')
    return replace(config, guide_sha256=digest((root / 'authored.json').read_bytes()),
                   ada_example_highlighting=True, ada_example_api_links=True,
                   ada_landing_example_highlighting=True,
                   verified_examples={'mapping': 'mapping.json', 'sha256': digest((root / 'mapping.json').read_bytes())})


