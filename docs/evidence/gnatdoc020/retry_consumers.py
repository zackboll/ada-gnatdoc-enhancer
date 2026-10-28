from pathlib import Path
import subprocess,json,concurrent.futures,hashlib
O=Path('/home/zboll/qualifications/gnatdoc020/acquisition');OLD=Path('/home/zboll/qualifications/gnatdoc019/acquisition');settings=str(O/'settings');gnatdoc='/home/zboll/.alire/gnatdoc_bin_26.0.0_6e6e0320/bin/gnatdoc'
def run(argv,cwd,log):
 with log.open('w') as f:subprocess.run(list(map(str,argv)),cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def qualify(name):
 b=O/name;src=b/'source';a=['alr','-n','-s',settings]
 if name=='mel':
  run(['git','clone','--no-hardlinks','--no-checkout',str(OLD/'mel/source'),str(b/'git-authority')],b,b/'git-clone.log')
  (src/'.git').write_text('gitdir: '+str(b/'git-authority/.git')+'\n')
  run(['git','--git-dir',str(b/'git-authority/.git'),'config','core.worktree',str(src)],b,b/'git-worktree.log')
  run(['python3','scripts/check_doc_source_integrity.py'],src,b/'source-integrity-retry.log')
  run(a+['-C','docs/toolchain','exec','--','sh','-c','cd ../.. && python3 scripts/gnatdoc_inventory.py --source-list obj/docs/public-sources.txt --report obj/docs/inventory.json && gprbuild -p -P docs_api.gpr -u -c -gnatc'],src,b/'build-retry.log')
  command=a+['-C','docs/toolchain','exec','--','sh','-c',f'cd ../.. && {gnatdoc} -P docs_api.gpr --backend html --generate public --style trailing --warnings -O {b}/pristine/api']
 else:
  for p in ('obj/docs','obj/docs-internal'):(src/p).mkdir(parents=True,exist_ok=True)
  command=a+['exec','--',gnatdoc,'-P','docs_api.gpr','--backend','html','--generate','public','--style','leading','--warnings','-O',str(b/'pristine/api')]
 run(command,src,b/'gnatdoc-retry.log');assert hashes(b/'pristine')==hashes(OLD/name/'pristine')
 run(['python3','scripts/compare_gnatdoc_warnings.py']+([] if name=='core' else ['--fail-on-removed'])+['docs/gnatdoc-warning-baseline.txt',str(b/'gnatdoc-retry.log')],src,b/'warnings-retry.log')
 if name in ('imgproc','geometry'):run(['python3','scripts/check_doc_coverage.py','--fail-on-removed','docs/gnatdoc-coverage-baseline.txt',str(b/'pristine')],src,b/'coverage-retry.log')
 if name=='mel':run(['python3','scripts/check_doc_coverage.py',str(b/'pristine'),'--report',str(b/'coverage-retry.json')],src,b/'coverage-retry.log')
 r=dict(site=name,fresh_native_matches_approved=True,warning_ratchet='passed',native_sha256=hashes(b/'pristine'));(b/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(name,'retry passed',flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(qualify,('core','imgproc','geometry','mel')))
(O/'summary.json').write_text(json.dumps(r,indent=2)+'\n')
