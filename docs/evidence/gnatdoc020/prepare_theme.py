from pathlib import Path
import shutil,json,hashlib
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes,preserve_native,identities
E=Path('/home/zboll/qualifications/gnatdoc020');T=Path('/home/zboll/gnatdoc-017-evidence');O=E/'theme';O.mkdir()
shutil.copytree(T/'legacy',O/'legacy')
report={}
for kind,config in [('candidate','custom.toml'),('candidate-second','custom.toml'),('incoming','custom-incoming.toml')]:
 site=O/kind;shutil.copytree(T/'pristine',site);c=load(T/'authority',config)
 r=enhance(c,site);verify(c,site);before=hashes(site);enhance(c,site);assert hashes(site)==before
 assert before['api/gnatdoc-theme.css']=='fa265d63e73436a6a449fd16011c3db68a5430e7fa6a98ea8eb0fd6821dca9b2'
 preservation=preserve_native(identities(T/'pristine'),site,config=c,pristine=T/'pristine')
 report[kind]=dict(result=r,preservation=preservation,hashes=before)
assert report['candidate']['hashes']==report['candidate-second']['hashes']
(O/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Custom theme exact bytes, source/native preservation, fresh determinism and idempotence passed')
