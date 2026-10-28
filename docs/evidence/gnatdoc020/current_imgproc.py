from pathlib import Path
import subprocess,shutil,hashlib,json
E=Path('/home/zboll/qualifications/gnatdoc020');b=E/'current-imgproc-build';b.mkdir();src=b/'source';old=Path('/home/zboll/qualifications/gnatdoc019/current-source')
shutil.copytree(old,src,ignore=shutil.ignore_patterns('.git','alire','obj','lib','bin','_site','gnatdoc'))
a=['alr','-n','-s',str(E/'acquisition/settings')]
def run(argv,name):
 with (b/name).open('w') as f:subprocess.run(list(map(str,argv)),cwd=src,stdout=f,stderr=subprocess.STDOUT,check=True)
run(a+['pin','opencv_core','--use='+str(E/'acquisition/core-dependency')],'pin.log');run(a+['build'],'build.log')
for p in ('docs/example.gpr','docs/examples/examples.gpr'):run(a+['exec','--','gprbuild','-p','-P',p],p.replace('/','-')+'.log')
for p in ('obj/docs','obj/docs-internal'):(src/p).mkdir(parents=True,exist_ok=True)
run(a+['exec','--','/home/zboll/.alire/gnatdoc_bin_26.0.0_6e6e0320/bin/gnatdoc','-P','docs_api.gpr','--backend','html','--generate','public','--style','leading','--warnings','-O',str(b/'pristine/api')],'gnatdoc.log')
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
assert hashes(b/'pristine')==hashes(Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native'))
run(['python3','scripts/compare_gnatdoc_warnings.py','--fail-on-removed','docs/gnatdoc-warning-baseline.txt',str(b/'gnatdoc.log')],'warnings.log')
run(['python3','scripts/check_doc_coverage.py','--fail-on-removed','docs/gnatdoc-coverage-baseline.txt',str(b/'pristine')],'coverage.log')
(b/'result.json').write_text(json.dumps(dict(revision='d4c30f12353ac8e7f70709ff12843445ad0de563',fresh_native_matches_approved=True,native_sha256=hashes(b/'pristine')),indent=2)+'\n');print('Current Imgproc 329 declarations: fresh native, build/examples, warnings/coverage passed')
