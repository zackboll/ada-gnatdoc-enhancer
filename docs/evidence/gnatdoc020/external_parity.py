from pathlib import Path
import subprocess,shutil,json,os,sys
E=Path('/home/zboll/qualifications/gnatdoc020');S=E/'candidate-source';O=E/'external-parity';O.mkdir();sys.path.insert(0,str(S/'scripts'));from compare_release_outputs import compare
program='''from pathlib import Path
from dataclasses import replace
import json,sys
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes
root=Path('/home/zboll/gnatdoc-018-evidence/r1/authority');c=load(root,'direct.toml');mode=sys.argv[1];s=Path(sys.argv[2])
if mode=='direct':c=replace(c,external_type_target=None)
if mode in ('stable','mixed'):
 q=json.loads((root/'qualified.json').read_text());p=json.loads(Path('/home/zboll/gnatdoc-018-evidence/imgproc-source/docs/evidence/gnatdoc009/r1/core-destination-proposal.json').read_text());names=sorted(t['identity'] for t in p['types'].values())
 import hashlib
 c=replace(c,external_symbol_bookmarks=dict(qualification='qualified.json',sha256=hashlib.sha256((root/'qualified.json').read_bytes()).hexdigest(),types=names if mode=='stable' else names[:1]))
enhance(c,s);verify(c,s);h=hashes(s);enhance(c,s);assert hashes(s)==h
print(json.dumps(h))
'''
report={};native=Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native')
for mode in ('direct','top','stable','mixed'):
 stage=O/mode;stage.mkdir();kinds=['baseline','candidate']+(['official'] if mode in ('direct','top') else [])
 for kind in kinds:
  site=stage/kind;shutil.copytree(native,site);env=dict(os.environ);env.pop('PYTHONPATH',None);py=E/'pilot-env/bin/python'
  if kind=='baseline':py=Path('/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python');env['PYTHONPATH']=str(E/'baseline-source/src')
  if kind=='official':py=E/'official-env/bin/python'
  p=subprocess.run([str(py),'-c',program,mode,str(site)],env=env,cwd=O,text=True,capture_output=True);(stage/(kind+'.log')).write_text(p.stdout+p.stderr);p.check_returncode()
 r={'merged':compare(stage/'baseline',stage/'candidate')}
 if 'official' in kinds:r['official']=compare(stage/'official',stage/'candidate',official=True,default_router=True)
 report[mode]=r;(O/'parity.json').write_text(json.dumps(report,indent=2)+'\n');print(mode,r,flush=True)
