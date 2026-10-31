import json,os,shutil,subprocess
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.qualification import hashes
root=Path('/tmp/gnatdoc028');out=root/'visibility-final';out.mkdir()
source=root/'source'
for label in ('historical-imgproc','current-imgproc','core'):
 old=Path('/tmp/gnatdoc024/visibility')/label
 manifest=json.loads((old/'candidate/api/presentation.json').read_text())
 authority=out/label/'authority'
 prior=Path('/tmp/gnatdoc024/historical-operation/first') if label=='historical-imgproc' else Path('/tmp/gnatdoc024/real-sites/imgproc/first') if label=='current-imgproc' else source/'tests/real-fixtures/search-core/authority'
 shutil.copytree(prior,authority,ignore=shutil.ignore_patterns('_site'))
 if label=='current-imgproc':
  shutil.copy('/home/zboll/.cache/imgproc-gnatdoc009-r3/independent-final/src/opencv-image_processing.ads',authority/'qualification-public/opencv-image_processing.ads');shutil.rmtree(authority/'qualification-public/src');shutil.copy('/home/zboll/.cache/imgproc-gnatdoc009-r3/independent-final/docs/gnatdoc-enhancer.toml',authority/'qualification.toml');shutil.copy('/home/zboll/.cache/imgproc-gnatdoc009-r3/independent-final/docs/api-categories.json',authority/'categories.json')
 config=load(authority,'default.toml' if label=='core' else 'qualification.toml')
 # Existing publication source hashes are evidence, not replacements for scanner/source verification.
 for path,sha in manifest['source_sha256'].items():
  import hashlib
  assert hashlib.sha256((authority/path).read_bytes()).hexdigest()==sha,(label,path)
 pristine=out/label/'pristine';(pristine/'api').mkdir(parents=True)
 for name,text in manifest['original_api_html'].items():(pristine/name).write_text(text)
 shutil.copy(old/'candidate/api/gnatdoc.css',pristine/'api/gnatdoc.css')
 proof=[dict(package=d.package,name=d.declaration.name,ordinal=d.ordinal,overloads=d.total,href=d.href,native_profile=d.section.code,source_profile=d.declaration.signature,source_line=d.declaration.line) for group in source_destinations(config,snapshot(config,pristine)).values() for d in group]
 assert proof==json.loads((old/'oracle.json').read_text()),label
 (out/label/'oracle.json').write_text(json.dumps(proof,indent=2)+'\n')
 site=out/label/'candidate';shutil.copytree(pristine,site);enhance(config,site);verify(config,site)
 before=hashes(site);enhance(config,site);assert hashes(site)==before
 print(label,'PASS',flush=True)
env=dict(os.environ,PLAYWRIGHT_MODULE='/home/zboll/.npm/_npx/e41f203b7505f1fb/node_modules/playwright',CHROME='/usr/bin/google-chrome',GNATDOC019_WORKSPACE=str(out),GNATDOC019_REPORT=str(root/'legacy-history-browser.json'));env.pop('PYTHONPATH',None)
subprocess.run(['node',source/'tests/default_visibility_browser.cjs'],cwd=root,env=env,check=True)
subprocess.run(['/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python',source/'scripts/check_operation_browser.py','--workspace',Path('/tmp/gnatdoc028/real-sites/imgproc'),'--proof',Path('/tmp/gnatdoc024/operation-proof.json'),'--output',root/'operation-browser.json','--geometry',root/'real-sites/geometry'],cwd=source,env=env,check=True)
(root/'legacy.ok').touch()
