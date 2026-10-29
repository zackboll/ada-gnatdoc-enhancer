from pathlib import Path
import subprocess,json,hashlib
O=Path('/home/zboll/qualifications/gnatdoc020/acquisition');b=O/'mel';src=b/'source';old=Path('/home/zboll/qualifications/gnatdoc019/acquisition/mel');gnatdoc='/home/zboll/.alire/gnatdoc_bin_26.0.0_6e6e0320/bin/gnatdoc'
def run(argv,log):
 with (b/log).open('w') as f:subprocess.run(list(map(str,argv)),cwd=src,stdout=f,stderr=subprocess.STDOUT,check=True)
run(['git','read-tree','6065129aba5dee89e70b61e05a9e1c9b2c3061c0'],'read-tree.log')
run(['python3','scripts/check_doc_source_integrity.py'],'source-integrity-final.log')
a=['alr','-n','-s',str(O/'settings'),'-C','docs/toolchain','exec','--','sh','-c']
run(a+['cd ../.. && python3 scripts/gnatdoc_inventory.py --source-list obj/docs/public-sources.txt --report obj/docs/inventory.json && gprbuild -p -P docs_api.gpr -u -c -gnatc'],'build-final.log')
for p in ('obj/docs','obj/docs-internal'):(src/p).mkdir(parents=True,exist_ok=True)
run(a+[f'cd ../.. && {gnatdoc} -P docs_api.gpr --backend html --generate public --style trailing --warnings -O {b}/pristine/api'],'gnatdoc-final.log')
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
assert hashes(b/'pristine')==hashes(old/'pristine')
run(['python3','scripts/compare_gnatdoc_warnings.py','--fail-on-removed','docs/gnatdoc-warning-baseline.txt',str(b/'gnatdoc-final.log')],'warnings-final.log')
run(['python3','scripts/check_doc_coverage.py',str(b/'pristine'),'--report',str(b/'coverage-final.json')],'coverage-final.log')
(b/'result.json').write_text(json.dumps(dict(site='mel',fresh_native_matches_approved=True,source_integrity='passed',native_sha256=hashes(b/'pristine')),indent=2)+'\n')
print('MEL fresh source integrity/build/native/warnings/coverage passed')
