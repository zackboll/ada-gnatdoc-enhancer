import json
import os
from pathlib import Path
import shutil
import subprocess

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes

ROOT = Path('/tmp/gnatdoc024')
SOURCE = ROOT/'source'
old = Path('/home/zboll/qualifications/gnatdoc019')
out = ROOT/'visibility'; out.mkdir()
for label in ('historical-imgproc', 'current-imgproc', 'core'):
    prior = old/label
    authority = prior/'authority' if label == 'core' else prior
    config = load(authority, 'default.toml' if label == 'core' else 'qualification.toml')
    root = out/label; root.mkdir()
    pristine = prior/'pristine'; site = root/'candidate'; shutil.copytree(pristine, site)
    proof = [dict(package=d.package, name=d.declaration.name, ordinal=d.ordinal,
                  overloads=d.total, href=d.href, native_profile=d.section.code,
                  source_profile=d.declaration.signature, source_line=d.declaration.line)
             for group in source_destinations(config, snapshot(config, pristine)).values() for d in group]
    assert proof == json.loads((prior/'oracle.json').read_text())
    (root/'oracle.json').write_text(json.dumps(proof, indent=2)+'\n')
    enhance(config, site); verify(config, site)
    before = hashes(site); enhance(config, site); assert hashes(site) == before

env = dict(os.environ, PLAYWRIGHT_MODULE='/home/zboll/.npm/_npx/e41f203b7505f1fb/node_modules/playwright',
           CHROME='/usr/bin/google-chrome', GNATDOC019_WORKSPACE=str(out),
           GNATDOC019_REPORT=str(ROOT/'legacy-history-browser.json'))
env.pop('PYTHONPATH', None)
subprocess.run(['node', SOURCE/'tests/default_visibility_browser.cjs'], cwd=ROOT, env=env, check=True)

# Independently retained operation-profile oracle; product and assertions unchanged.
prior = Path('/home/zboll/qualifications/gnatdoc023/historical-operation/first')
workspace = ROOT/'historical-operation'
authority = workspace/'first'; shutil.copytree(prior, authority, ignore=shutil.ignore_patterns('_site'))
manifest = json.loads((prior/'_site/api/presentation.json').read_text())
site = authority/'_site'; (site/'api').mkdir(parents=True)
for path, text in manifest['original_api_html'].items(): (site/path).write_text(text)
shutil.copy(prior/'_site/api/gnatdoc.css', site/'api/gnatdoc.css')
config = load(authority, 'qualification.toml')
proof = [dict(package=d.package, name=d.declaration.name, ordinal=d.ordinal,
              overloads=d.total, href=d.href, native_profile=d.section.code,
              source_profile=d.declaration.signature, source_line=d.declaration.line)
         for group in source_destinations(config, snapshot(config, site)).values() for d in group]
(ROOT/'operation-proof.json').write_text(json.dumps(proof, indent=2)+'\n')
enhance(config, site); verify(config, site)
subprocess.run([ROOT/'envs/wheel-3.13/bin/python', SOURCE/'scripts/check_operation_browser.py',
                '--workspace', workspace, '--proof', ROOT/'operation-proof.json',
                '--output', ROOT/'operation-browser.json'], cwd=ROOT, env=env, check=True)
(ROOT/'legacy.ok').touch()