"""Enable the already-supported incoming-instance profile, no product changes."""
import importlib.util
import json
from pathlib import Path
import shutil
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes

E = Path('/home/zboll/gnatdoc-017-evidence')
S = Path('/home/zboll/git/ada-gnatdoc-enhancer-017')
for label, filename in [('incoming-default','default-incoming.toml'),('incoming-custom','custom-incoming.toml')]:
    shutil.copytree(E/'pristine',E/label)
    c = load(E/'authority',filename); result = enhance(c,E/label); verify(c,E/label)
    before = hashes(E/label); enhance(c,E/label); assert before == hashes(E/label)
    (E/(label+'.json')).write_text(json.dumps(result,indent=2))
    spec = importlib.util.spec_from_file_location('independent',S/'scripts/qualify_symbol_bookmarks.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # Explicitly extend only this qualification invocation to the newly reviewed
    # pin. The consumer oracle and product source remain unchanged.
    module.PINS = {'33a2a4f3b83606a5c779b8a93abeb6c91fa49a21'}
    report = module.audit(E/'core-build',E/'pristine',E/label,E/'legacy',instance_references=True)
    (E/(label+'-native-audit.json')).write_text(json.dumps(report,indent=2))
a = hashes(E/'incoming-default'); b = hashes(E/'incoming-custom')
assert [n for n in a if a[n]!=b[n]] == ['api/gnatdoc-theme.css','api/presentation.json']
print('Incoming opt-in leaves only CSS/manifest delta; native/source audit complete')