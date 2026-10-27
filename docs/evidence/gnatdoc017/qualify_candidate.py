import json
from pathlib import Path
import shutil
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native, bind_pristine
from ada_gnatdoc_enhancer.util import sorted_json, digest

E = Path('/home/zboll/gnatdoc-017-evidence'); W = E/'authority'
theme = (E/'core-source/docs/assets/gnatdoc-theme.css').read_bytes()
assert digest(theme) == 'fa265d63e73436a6a449fd16011c3db68a5430e7fa6a98ea8eb0fd6821dca9b2'
text = (W/'default.toml').read_text() + f'''\n[presentation]
theme = true
theme_css_source = "docs/assets/gnatdoc-theme.css"
theme_css_sha256 = "{digest(theme)}"
'''
(W/'custom.toml').write_text(text)
config = load(W, 'custom.toml'); report = {}
for name in ('candidate', 'candidate-second'):
    shutil.copytree(E/'pristine', E/name)
    report[name] = enhance(config, E/name); verify(config, E/name)
    before = hashes(E/name); enhance(config, E/name); assert hashes(E/name) == before
    bind_pristine(E/'pristine', E/name)
    report[name]['preservation'] = preserve_native(identities(E/'pristine'), E/name,
                                                  config=config, pristine=E/'pristine')
assert hashes(E/'candidate') == hashes(E/'candidate-second')
a = hashes(E/'shared-baseline'); b = hashes(E/'candidate')
assert a.keys() == b.keys()
assert [n for n in a if a[n] != b[n]] == ['api/gnatdoc-theme.css', 'api/presentation.json']
assert (E/'candidate/api/gnatdoc-theme.css').read_bytes() == theme
report.update(deterministic=True, idempotent=True, only_css_and_manifest_changed=True,
              source_theme_sha256=digest(theme), output_sha256=b)
(E/'candidate.json').write_text(sorted_json(report))
print(sorted_json(report['candidate']))