from pathlib import Path
import json,hashlib
E=Path('/home/zboll/qualifications/gnatdoc020');O=E/'external-profiles';summary=json.loads((O/'summary.json').read_text());assert len(summary)==8 and all(x['returncode']==0 for x in summary)
result=dict(profiles=[],assertions=0,responses=0,browser_bodies=0,separate_https_audits=0,failures=[])
for row in summary:
 p=O/(row['profile']+'.json');d=json.loads(p.read_text());assert not d['failures'];a=len(d['assertions']);r=len(d['responses']);result['assertions']+=a;result['responses']+=r
 from collections import Counter
 types=Counter(x.get('evidence') for x in d['responses']);result['browser_bodies']+=types['browser-response-body'];result['separate_https_audits']+=r-types['browser-response-body']
 result['profiles'].append(dict(profile=row['profile'],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),assertions=a,responses=r,evidence_types=dict(types),browser=d['browser'],failures=d['failures']))
(E/'external-browser-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['assertions'],'assertions',result['responses'],'responses')
