"""Independent writable snapshots only; historical inputs remain read-only."""
from pathlib import Path
import concurrent.futures,subprocess,json,shutil,os,hashlib
E=Path('/home/zboll/qualifications/gnatdoc020');OLD=Path('/home/zboll/qualifications/gnatdoc019');O=E/'acquisition';O.mkdir()
shutil.copytree(OLD/'acquisition/settings',O/'settings')
settings=str(O/'settings');gnatdoc='/home/zboll/.alire/gnatdoc_bin_26.0.0_6e6e0320/bin/gnatdoc'
def run(argv,cwd,log):
 with log.open('w') as out:subprocess.run(list(map(str,argv)),cwd=cwd,stdout=out,stderr=subprocess.STDOUT,check=True)
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def qualify(name):
 b=O/name;b.mkdir();src=b/'source';prior=OLD/'acquisition'/name/'snapshot'
 shutil.copytree(prior,src,ignore=shutil.ignore_patterns('alire','obj','lib','bin','.git','_site','gnatdoc'))
 if name in ('imgproc','geometry'):
  dep=O/'core-dependency'
  run(['alr','-n','-s',settings,'pin','opencv_core','--use='+str(dep)],src,b/'pin.log')
 a=['alr','-n','-s',settings]
 if name=='mel':
  run(['python3','scripts/check_doc_source_integrity.py'],src,b/'source-integrity.log')
  run(a+['-C','docs/toolchain','exec','--','sh','-c','cd ../.. && python3 scripts/gnatdoc_inventory.py --source-list obj/docs/public-sources.txt --report obj/docs/inventory.json && gprbuild -p -P docs_api.gpr -u -c -gnatc'],src,b/'build.log')
  command=a+['-C','docs/toolchain','exec','--','sh','-c',f'cd ../.. && {gnatdoc} -P docs_api.gpr --backend html --generate public --style trailing --warnings -O {b}/pristine/api']
 else:
  run(a+['build'],src,b/'build.log')
  for project in ('docs/example.gpr','docs/examples/examples.gpr'):
   if (src/project).exists():run(a+['exec','--','gprbuild','-p','-P',project],src,b/(project.replace('/','-')+'.log'))
  command=a+['exec','--',gnatdoc,'-P','docs_api.gpr','--backend','html','--generate','public','--style','leading','--warnings','-O',str(b/'pristine/api')]
 run(command,src,b/'gnatdoc.log')
 assert hashes(b/'pristine')==hashes(OLD/'acquisition'/name/'pristine'),name+' native mismatch'
 warn=['python3','scripts/compare_gnatdoc_warnings.py']+([] if name=='core' else ['--fail-on-removed'])+['docs/gnatdoc-warning-baseline.txt',str(b/'gnatdoc.log')]
 run(warn,src,b/'warnings.log')
 if name in ('imgproc','geometry'):run(['python3','scripts/check_doc_coverage.py','--fail-on-removed','docs/gnatdoc-coverage-baseline.txt',str(b/'pristine')],src,b/'coverage.log')
 if name=='mel':run(['python3','scripts/check_doc_coverage.py',str(b/'pristine'),'--report',str(b/'coverage.json')],src,b/'coverage.log')
 report=dict(site=name,fresh_native_matches_approved=True,source_native=hashes(b/'pristine'))
 (b/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(name,'fresh build/native/examples/ratchets passed',flush=True)
 return report
shutil.copytree(OLD/'acquisition/core-dependency',O/'core-dependency',ignore=shutil.ignore_patterns('.git','obj','lib','bin'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(qualify,('core','imgproc','geometry','mel')))
(O/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
