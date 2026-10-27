"""Extra authentic Features / Imgproc default profiles, never write consumers."""
import json
import os
from pathlib import Path
import shutil
import subprocess

E = Path('/home/zboll/gnatdoc-017-evidence'); O = E/'extra-parity-final'; O.mkdir()
entries = [('features',E/'features-authority','docs/gnatdoc-enhance.toml',
            Path('/home/zboll/git/opencv/features-doc-011-evidence/final-hosted/native')),
           ('imgproc81',Path('/home/zboll/qualification/gnatdoc015/final-consumer-wheel/source'),
            'candidate.toml',Path('/home/zboll/qualification/gnatdoc015/final-consumer-wheel/default'))]
program = '''import json,sys
from pathlib import Path
import ada_gnatdoc_enhancer as p
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes
c=load(Path(sys.argv[1]),sys.argv[2]);site=Path(sys.argv[3])
enhance(c,site);result=verify(c,site);before=hashes(site);enhance(c,site)
assert before==hashes(site)
print(json.dumps(dict(module=p.__file__,hashes=before,result=result)))
'''
env = dict(os.environ); env.pop('PYTHONPATH',None)
report = {}
for label,root,config,native in entries:
    stage = O/label; pristine = stage/'pristine'; (pristine/'api').mkdir(parents=True)
    if (native/'api/presentation.json').exists():
        data = json.loads((native/'api/presentation.json').read_text())
        for name,text in data['original_api_html'].items(): (pristine/name).write_text(text)
        (pristine/'api/gnatdoc.css').write_bytes((native/'api/gnatdoc.css').read_bytes())
    else: shutil.copytree(native,pristine,dirs_exist_ok=True)
    results = {}
    for kind,python in [('official',E/'baseline-env/bin/python'),
                        ('candidate',E/'distributions/python-3.11/wheel-env/bin/python')]:
        site = stage/kind; shutil.copytree(pristine,site)
        results[kind] = json.loads(subprocess.check_output([python,'-c',program,root,config,site],cwd=O,env=env,text=True))
        assert 'site-packages' in results[kind]['module']
    assert results['official']['hashes']==results['candidate']['hashes'],label
    report[label]=results
    (O/'parity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(label,'exact byte parity',len(results['official']['hashes']),flush=True)