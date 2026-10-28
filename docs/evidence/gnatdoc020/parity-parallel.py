import json,os,shutil,subprocess,sys
from pathlib import Path
E=Path('/home/zboll/qualifications/gnatdoc020')
OLD=Path('/home/zboll/qualifications/gnatdoc019')
S=E/'candidate-source'
T=Path('/home/zboll/gnatdoc-017-evidence')
R=Path('/home/zboll/qualification/gnatdoc012r2')
O=E/'parity-parallel';O.mkdir(exist_ok=False)
sys.path.insert(0,str(S/'scripts'))
from compare_release_outputs import compare
entries=[('current-core-symbols',T/'authority','default.toml',T/'pristine'),
         ('current-core-incoming',T/'authority','default-incoming.toml',T/'pristine')]
for label in ('core-current','core-050'):
    for profile,root,config in [('packages',R/(label+'-default-authority'),'default.toml'),
                                ('symbols',R/(label+'-authority'),'disabled.toml'),
                                ('incoming',R/(label+'-authority'),'qualification.toml')]:
        publication=R/(label+'-'+('default' if profile=='packages' else 'instance' if profile=='incoming' else 'symbols')+'-release')
        entries.append((label+'-'+profile,root,config,publication))
for profile,config in [('packages','docs/gnatdoc-enhance.toml'),('symbols','docs/symbols.toml')]:
    entries.append(('mel-'+profile,R/'mel-authority',config,R/('mel-'+('default' if profile=='packages' else 'symbols')+'-release')))
for name in ('core','imgproc','geometry','mel'):
    entries.append(('authored-'+name,S/'tests/authored-fixtures'/name,'project.toml',S/'tests/authored-fixtures'/name/'native'))
    entries.append(('synthetic-'+name,S/'tests/fixtures'/name,'project.toml',S/'tests/fixtures'/name/'_site'))
entries.extend([('features',T/'features-authority','docs/gnatdoc-enhance.toml',Path('/home/zboll/git/opencv/features-doc-011-evidence/final-hosted/native')),
                ('imgproc81',Path('/home/zboll/gnatdoc-018-evidence/imgproc-authority'),'candidate.toml',Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native'))])
assert len(entries)==20
for label in ('historical-imgproc','current-imgproc'):
    entries.append((label,OLD/label,'qualification.toml',OLD/label/'pristine'))
entries.extend([('current-core-custom-symbols',T/'authority','custom.toml',T/'pristine'),
                ('current-core-custom-incoming',T/'authority','custom-incoming.toml',T/'pristine')])

for label in ('historical-imgproc','current-imgproc'):
 entries.append((label+'-disabled',OLD/label,'qualification.toml',OLD/label/'pristine'))
assert len(entries)==26
program="""import json,sys
from pathlib import Path
from dataclasses import replace
import ada_gnatdoc_enhancer as p
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes,preserve_native,identities
c=load(Path(sys.argv[1]),sys.argv[2]);s=Path(sys.argv[3]);pristine=Path(sys.argv[4])
if sys.argv[5]=='True':c=replace(c,navigation='none',category_file=None)
r=enhance(c,s);verify(c,s);before=hashes(s);enhance(c,s);assert before==hashes(s)
preservation=preserve_native(identities(pristine),s,config=c,pristine=pristine)
print(json.dumps(dict(default=c.navigation!='none' and not c.symbol_bookmarks and not c.instance_references,hashes=before,result=r,native_preservation=preservation,module=p.__file__)))
"""
import concurrent.futures,threading
report={}
lock=threading.Lock()
def qualify(entry):
 label,root,config,native=entry
 stage=O/label;pristine=stage/'pristine';(pristine/'api').mkdir(parents=True)
 if (native/'api/presentation.json').exists():
  data=json.loads((native/'api/presentation.json').read_text())
  for name,text in data['original_api_html'].items():(pristine/name).write_text(text)
  shutil.copyfile(native/'api/gnatdoc.css',pristine/'api/gnatdoc.css')
 else:shutil.copytree(native,pristine,dirs_exist_ok=True)
 results={}
 modes=['baseline','candidate','second']
 if '-custom-' not in label:modes.append('official')
 for kind in modes:
  site=stage/kind;shutil.copytree(pristine,site)
  env=dict(os.environ);env.pop('PYTHONPATH',None)
  py=E/'distributions/python-3.11/wheel-env/bin/python'
  if kind=='baseline':
   py=Path('/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python');env['PYTHONPATH']=str(E/'baseline-source/src')
  if kind=='official':py=E/'official-env/bin/python'
  r=subprocess.run([str(py),'-c',program,str(root),config,str(site),str(pristine),str(label.endswith('-disabled'))],cwd=O,env=env,text=True,capture_output=True)
  (stage/(kind+'.log')).write_text(r.stdout+r.stderr);r.check_returncode();results[kind]=json.loads(r.stdout)
 assert results['candidate']['hashes']==results['second']['hashes']
 classified={'merged':compare(stage/'baseline',stage/'candidate')}
 if 'official' in results:classified['official']=compare(stage/'official',stage/'candidate',official=True,default_router=results['candidate']['default'])
 with lock:
  report[label]=dict(comparisons=classified,deterministic=True,idempotent=True,results=results)
  (O/'parity.json').write_text(json.dumps(report,indent=2)+'\n')
  print(label,classified,flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 list(pool.map(qualify,entries))
assert len(report)==26
