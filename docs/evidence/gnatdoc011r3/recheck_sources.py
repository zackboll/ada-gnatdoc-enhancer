"""Independent retained acquisition identities; no new GNATdoc acquisition claim."""
import hashlib
import json
from pathlib import Path
import subprocess
E=Path('/home/zboll/qualification/gnatdoc011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
source=json.loads((W/'acquisition-source-proof.json').read_text());result={}
for label in ['core-current','core-050']:
    core=W/label;record=source[label]
    assert subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip()==record['revision']
    assert {n:hashlib.sha256((core/n).read_bytes()).hexdigest() for n in record['source_sha256']}==record['source_sha256']
    result[label]={'revision':record['revision'],'source_files_verified':len(record['source_sha256']),
                   'retained_acquisition_hashes_match':True,'fresh_Ada_GNATdoc_acquisition':False}
(E/'retained-source-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)