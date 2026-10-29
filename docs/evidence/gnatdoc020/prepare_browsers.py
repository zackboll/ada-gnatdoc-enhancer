from pathlib import Path
import json,shutil
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.qualification import hashes
E=Path('/home/zboll/qualifications/gnatdoc020');old=Path('/home/zboll/qualifications/gnatdoc019');out=E/'visibility';out.mkdir()
for label in ('historical-imgproc','current-imgproc','core'):
 root=out/label;root.mkdir();prior=old/label
 authority=prior/'authority' if label=='core' else prior
 config='qualification.toml' if label!='core' else 'qualification.toml'
 print(label,list((prior/'authority').glob('*.toml')) if label=='core' else config,flush=True)
 if label=='core':config='default.toml'
 c=load(authority,config)
 pristine=prior/'pristine';site=root/'candidate';shutil.copytree(pristine,site)
 ds=source_destinations(c,snapshot(c,pristine))
 proof=[dict(package=d.package,name=d.declaration.name,ordinal=d.ordinal,overloads=d.total,href=d.href,native_profile=d.section.code,source_profile=d.declaration.signature,source_line=d.declaration.line) for group in ds.values() for d in group]
 assert proof==json.loads((prior/'oracle.json').read_text())
 (root/'oracle.json').write_text(json.dumps(proof,indent=2)+'\n')
 enhance(c,site);verify(c,site);before=hashes(site);enhance(c,site);assert hashes(site)==before
 print(label,len(proof),'installed v0.1.2 source/native-bound',flush=True)
