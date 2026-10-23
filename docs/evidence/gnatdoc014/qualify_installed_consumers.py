import concurrent.futures,subprocess,os,json
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Replay full read-only Imgproc qualification in six installed environments')
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--workspace',type=Path,required=True)
args=parser.parse_args()
s=args.source.resolve();w=args.workspace.resolve()
def run(pair):
 v,kind=pair;label=v+'-'+kind;py=w/'distributions-final'/('python-'+v)/(kind+'-env')/'bin/python'
 assert py.is_file(),py
 dest=w/('installed-final-'+label)
 args=[py,s/'scripts/qualify_external_type_target.py','--consumer','/home/zboll/git/opencv/imgproc-gnatdoc009','--retained','/home/zboll/git/opencv/imgproc-gnatdoc009-r1-work','--native','/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native','--baseline-src',w/'baseline/src','--output',dest]
 env=dict(os.environ);env.pop('PYTHONPATH',None)
 with (w/('installed-final-'+label+'.log')).open('w') as out:subprocess.run(list(map(str,args)),env=env,cwd=w,stdout=out,stderr=subprocess.STDOUT,check=True)
 report=(dest/'qualification.json').read_bytes();assert report==(w/'imgproc/qualification.json').read_bytes()
 return dict(python=v,archive=kind,full_consumer_qualification_equal=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:results=list(p.map(run,[(v,k) for v in ('3.11','3.12','3.13') for k in ('wheel','sdist')]))
(s/'docs/evidence/gnatdoc014/installed-consumer-matrix.json').write_text(json.dumps(results,indent=2)+'\n')
print('All six clean installed wheel/rebuilt-sdist consumer qualifications equal source')
