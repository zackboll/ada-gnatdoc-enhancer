import json,shutil,subprocess
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes,check_snapshot,identities,preserve_native
import sys
sys.path.insert(0,'/tmp/gnatdoc028/source/scripts')
from compare_release_013_014 import compare
root=Path('/tmp/gnatdoc028'); inputs=json.loads(Path('/tmp/gnatdoc024/real-input-identities.json').read_text()); report={}
for name,d in inputs.items():
 prior=Path('/tmp/gnatdoc024/real-sites')/name
 check_snapshot(prior/'first',d['source_sha256'],staged=True)
 assert hashes(prior/'pristine')==d['pristine_sha256']
 work=root/'real-sites'/name; authority=work/'first'
 shutil.copytree(prior/'first',authority,ignore=shutil.ignore_patterns('_site'))
 pristine=work/'pristine';shutil.copytree(prior/'pristine',pristine)
 config=load(authority,'qualification.toml')
 site=authority/'_site';shutil.copytree(pristine,site)
 r=enhance(config,site);verify(config,site)
 before=hashes(site);enhance(config,site);assert hashes(site)==before
 second=work/'second';shutil.copytree(pristine,second);enhance(config,second);assert hashes(second)==before
 baseline=work/'baseline'
 subprocess.run([root/'official-env/bin/python','-c','from pathlib import Path; import shutil,sys; from ada_gnatdoc_enhancer.config import load; from ada_gnatdoc_enhancer.pipeline import enhance,verify; root,raw,site=sys.argv[1:]; shutil.copytree(raw,site);c=load(Path(root),"qualification.toml");enhance(c,Path(site));verify(c,Path(site))',authority,pristine,baseline],cwd=root,check=True)
 report[name]=dict(input=d,publication=r,comparison=compare(baseline,site),deterministic=True,idempotent=True,native_preservation=preserve_native(identities(pristine),site,config=config,pristine=pristine),publication_sha256=before)
 (root/'real-compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
 print(name,'PASS',flush=True)
