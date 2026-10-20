import json,hashlib,os,subprocess,sys
from pathlib import Path
b=Path('/tmp/gnatdoc012-candidate');s=b/'source'
old=json.loads((s/'docs/evidence/gnatdoc011r2/default-and-symbol-only-parity.json').read_text())
inputs=json.loads(Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work/default-inputs.json').read_text())
report={}
for e in inputs:
 label=e['label']; pristine=b/('parity-'+label)
 program='import sys,json;from pathlib import Path;sys.path.insert(0,'+repr(str(s/'scripts'))+');from compare_default_symbol_outputs import output;print(json.dumps(output(Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]))))'
 reconstructed=json.loads(subprocess.check_output([sys.executable,'-c',program,e['root'],e['config'],str(pristine)],env=dict(os.environ,PYTHONPATH='/tmp/gnatdoc012/src'),text=True))
 assert reconstructed==old[label]['sha256'],label
 report[label]={'complete_reconstruction_equal_reviewed_R2_hash_inventory':True,'files':len(reconstructed),'input_config_sha256':hashlib.sha256((Path(e['root'])/e['config']).read_bytes()).hexdigest(),'pristine_sha256':{p.relative_to(pristine).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in pristine.rglob('*') if p.is_file()}}
(b/'parity-input-identity-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
