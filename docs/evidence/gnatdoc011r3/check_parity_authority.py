import json
import sys
from pathlib import Path
E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
sys.path.insert(0,str(R/'scripts'))
from compare_default_symbol_outputs import output
from ada_gnatdoc_enhancer.qualification import hashes
reviewed=json.loads((R/'docs/evidence/gnatdoc011r2/default-and-symbol-only-parity.json').read_text())
actual=json.loads((E/'default-parity-final/parity.json').read_text())
report={}
for label,record in actual.items():
    assert record['sha256']==reviewed[label]['sha256'],label
    report[label]={'files':record['files'],'matches_complete_reviewed_R2_inventory':True}
for label in ['core-current','core-050']:
    manifest=json.loads((E/(label+'-symbols-first/api/presentation.json')).read_text())
    old=json.loads((Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')/(label+'-disabled/api/presentation.json')).read_text())
    assert set(k for k in manifest if manifest[k]!=old[k])=={'output_sha256'}
    assert set(k for k in manifest['output_sha256'] if manifest['output_sha256'][k]!=old['output_sha256'][k])=={'api/gnatdoc-navigation.js'}
(E/'reviewed-parity-authority.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)