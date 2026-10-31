import concurrent.futures, subprocess
from pathlib import Path
root=Path('/tmp/gnatdoc028')
def run(name):
 with (root/'logs'/('browser-real-'+name+'.log')).open('w') as out:
  subprocess.run(['/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python',root/'source/scripts/check_real_browser.py','--workspace',root/'real-sites'/name,'--output',root/(name+'-real-browser.json')],stdout=out,stderr=subprocess.STDOUT,check=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,['core','geometry','imgproc','mel']))
(root/'real-browsers.ok').touch()
