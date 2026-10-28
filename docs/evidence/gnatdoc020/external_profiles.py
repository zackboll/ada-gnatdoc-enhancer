import concurrent.futures,subprocess,os,json
from pathlib import Path
E=Path('/home/zboll/qualifications/gnatdoc020');out=E/'external-profiles'
profiles=[f'{w}-{color}-js{js}' for w in (1280,390) for color in ('light','dark') for js in ('true','false')]
def run(profile):
 env=dict(os.environ,PLAYWRIGHT_MODULE='/home/zboll/.npm/_npx/e41f203b7505f1fb/node_modules/playwright',CHROME='/usr/bin/google-chrome',GNATDOC018_WORKSPACE=str(E/'external'),GNATDOC018_REPORT=str(out/(profile+'.json')),GNATDOC018_PROFILE=profile)
 with (out/(profile+'.log')).open('w') as f:p=subprocess.run(['node',str(E/'candidate-source/tests/external_symbols_browser.cjs')],env=env,stdout=f,stderr=subprocess.STDOUT)
 print(profile,p.returncode,flush=True);return dict(profile=profile,returncode=p.returncode)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(run,profiles))
(out/'summary.json').write_text(json.dumps(r,indent=2)+'\n')
assert all(x['returncode']==0 for x in r)
