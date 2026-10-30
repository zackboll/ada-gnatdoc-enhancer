import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native

ROOT = Path('/tmp/gnatdoc024')
SOURCE = ROOT/'source'
OUT = ROOT/'compatibility'
BASELINE = ROOT/'baseline-env/bin/python'
spec = importlib.util.spec_from_file_location('audit', SOURCE/'scripts/compare_release_outputs.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
report = {}
environment = dict(os.environ); environment.pop('PYTHONPATH', None)

def baseline(authority, config, pristine, destination):
    subprocess.run([BASELINE, '-c',
        'from pathlib import Path; import shutil,sys; from ada_gnatdoc_enhancer.config import load; '
        'from ada_gnatdoc_enhancer.pipeline import enhance,verify; '
        'root,name,raw,site=sys.argv[1:]; shutil.copytree(raw,site); c=load(Path(root),name); '
        'enhance(c,Path(site)); verify(c,Path(site))',
        str(authority), config, str(pristine), str(destination)], cwd=ROOT, env=environment, check=True)

def candidate(label, authority, config, pristine, old):
    site = OUT/('new-'+label); shutil.copytree(pristine, site)
    c = load(authority, config); enhance(c, site); verify(c, site)
    before = hashes(site); enhance(c, site); assert hashes(site) == before
    second = OUT/('second-'+label); shutil.copytree(pristine, second)
    enhance(c, second); assert hashes(second) == before
    record = audit.compare(old, site, official=True)
    record.update(preservation=preserve_native(identities(pristine), site, config=c, pristine=pristine),
                  deterministic=True, idempotent=True, publication_sha256=before,
                  baseline_publication_sha256=hashes(old), search_opt_in=False)
    report[label] = record
    (ROOT/'compatibility.json').write_text(json.dumps(report, indent=2)+'\n')
    print(label, 'PASS', flush=True)

fixture = SOURCE/'tests/real-fixtures/search-core'
for variant, config in [('default', 'default.toml'), ('symbol', 'symbol.toml'), ('instance', 'qualification.toml')]:
    old = OUT/('old-'+variant)
    if not (old/'api/presentation.json').exists():
        if old.exists(): shutil.rmtree(old)
        baseline(OUT/'authority', config, fixture/'pristine', old)
    candidate('core-'+variant, OUT/'authority', config, fixture/'pristine', old)

prior_root = Path('/home/zboll/git/gnatdoc-021-release/four-site-work')
for name in ('core', 'geometry', 'imgproc', 'mel'):
    prior = prior_root/name/'first'
    workspace = ROOT/'real-sites'/name
    authority = workspace/'first'; shutil.copytree(prior, authority, ignore=shutil.ignore_patterns('_site'))
    pristine = workspace/'pristine'; (pristine/'api').mkdir(parents=True)
    manifest = json.loads((prior/'_site/api/presentation.json').read_text())
    for path, text in manifest['original_api_html'].items(): (pristine/path).write_text(text)
    shutil.copy(prior/'_site/api/gnatdoc.css', pristine/'api/gnatdoc.css')
    old = OUT/('old-real-'+name); baseline(authority, 'qualification.toml', pristine, old)
    candidate('real-'+name, authority, 'qualification.toml', pristine, old)
    shutil.copytree(OUT/('new-real-'+name), authority/'_site')

# Navigation-disabled publication: no filter-label change is permitted.
authority = OUT/'none-authority'; shutil.copytree(SOURCE/'tests/fixtures/core', authority,
                                                ignore=shutil.ignore_patterns('_site'))
path = authority/'project.toml'; path.write_text(path.read_text().replace('mode = "packages"', 'mode = "none"'))
pristine = SOURCE/'tests/fixtures/core/_site'
old = OUT/'old-none'; baseline(authority, 'project.toml', pristine, old)
candidate('none', authority, 'project.toml', pristine, old)