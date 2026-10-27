"""Acquire current Core contracts before changing the enhancer implementation."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native, bind_pristine
from ada_gnatdoc_enhancer.util import digest, sorted_json

E = Path('/home/zboll/gnatdoc-017-evidence')
S = Path('/home/zboll/git/ada-gnatdoc-enhancer-017')
R = E/'core-source'
W = E/'authority'
W.mkdir()
shutil.copytree(R/'docs', W/'docs')
(W/'public').mkdir()
sys.path.insert(0, str(R/'scripts'))
from link_gnatdoc_types import sources
from enhance_gnatdoc_instances import discover, ELEMENTS
source_map = sources(R/'src')
# Core's own validator publishes only immediate public specs.
for path in (R/'src').glob('*.ads'):
    shutil.copyfile(path, W/'public'/path.name)
base = '''schema_version = 1
project = "OpenCV Core Ada"
[sources]
directories = ["public"]
[navigation]
mode = "packages"
symbol_bookmarks = true
default_package = "OpenCV.Core"
[security]
external_hosts = ["github.com", "zackboll.github.io"]
'''
(W/'base.toml').write_text(base)
c = load(W, 'base.toml')
source = packages(c)
assert set(source) == set(source_map)
instances = {key: dict(package=source[key].name, template=value[0], element_type=value[1],
                       dimensions=value[2], element_owner=ELEMENTS[value[1]][0])
             for key, value in discover(source_map).items()}
record = dict(schema_version=1, instances=instances,
              source_sha256={p.path.relative_to(W).as_posix(): digest(p.path.read_bytes())
                             for p in source.values()}, native_sha256=hashes(E/'pristine'))
payload = sorted_json(record).encode()
(W/'generic.json').write_bytes(payload)
spec = importlib.util.spec_from_file_location('qualify_authored', S/'scripts/qualify_authored.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
authored = module.contract('core', R, E/'pristine')
for name in authored['inputs']:
    (W/name).parent.mkdir(parents=True, exist_ok=True)
    if not (W/name).exists():
        shutil.copyfile(R/name, W/name)
payload2 = sorted_json(authored).encode()
(W/'authored.json').write_bytes(payload2)
config = base + f'''[generic_instances]
qualification = "generic.json"
sha256 = "{digest(payload)}"
[guides]
mode = "authored-markdown"
manifest = "authored.json"
sha256 = "{digest(payload2)}"
'''
(W/'default.toml').write_text(config)
shutil.copytree(E/'pristine', E/'shared-baseline')
c = load(W, 'default.toml')
result = enhance(c, E/'shared-baseline'); verify(c, E/'shared-baseline')
bind_pristine(E/'pristine', E/'shared-baseline')
preservation = preserve_native(identities(E/'pristine'), E/'shared-baseline', config=c, pristine=E/'pristine')
for name in ['index.html', 'guides/gnatdoc-guides.css', *(e['path'] for e in authored['guides'])]:
    assert (E/'legacy'/name).read_bytes() == (E/'shared-baseline'/name).read_bytes(), name
report = dict(enhancer_start='dd100f026e13cdd9e97b283d50130241d71bdb9d',
              core_revision='33a2a4f3b83606a5c779b8a93abeb6c91fa49a21',
              theme_sha256=digest((R/'docs/assets/gnatdoc-theme.css').read_bytes()),
              source_sha256=record['source_sha256'], pristine_sha256=hashes(E/'pristine'),
              legacy_sha256=hashes(E/'legacy'), shared_sha256=hashes(E/'shared-baseline'),
              shared_result=result, native_preservation=preservation,
              authored_bytes_identical=True)
(E/'baseline.json').write_text(sorted_json(report))
print(sorted_json(result))