import json
import os
from pathlib import Path
import shutil
import subprocess
E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
report={}
for label in ['core-current','core-050']:
    root=E/(label+'-default-authority')
    if not root.exists():shutil.copytree(E/(label+'-authority'),root)
    config=(root/'disabled.toml').read_text().replace('symbol_bookmarks = true\ndefault_package = "OpenCV.Core"\n','')
    (root/'default.toml').write_text(config)
    outputs=[]
    for kind,python,source in [('base',E/'py-3.13/bin/python',Path('/home/zboll/qualification/mel-doc010-20261019/upstream-source/src')),
                               ('corrected',E/'py-3.13/bin/python',R/'src')]:
        site=E/(label+'-default-'+kind)
        if not site.exists():shutil.copytree(W/(label+'-pristine'),site)
        env=dict(os.environ,TMPDIR=str(E/'tmp'));env.pop('PYTHONPATH',None)
        if source:env['PYTHONPATH']=str(source)
        program='import json;from pathlib import Path;from ada_gnatdoc_enhancer.config import load;from ada_gnatdoc_enhancer.pipeline import enhance,verify;from ada_gnatdoc_enhancer.qualification import hashes;c=load(Path('+repr(str(root))+'),"default.toml");p=Path('+repr(str(site))+');enhance(c,p);verify(c,p);h=hashes(p);enhance(c,p);assert hashes(p)==h;print(json.dumps(h))'
        outputs.append(json.loads(subprocess.check_output([str(python),'-c',program],env=env,text=True)))
    assert outputs[0]==outputs[1],label
    report[label]={'byte_identical_to_immutable_merge':True,'files':len(outputs[0]),'sha256':outputs[0]}
    print(label,'disabled symbols exact publication parity',flush=True)
(E/'core-disabled-parity.json').write_text(json.dumps(report,indent=2)+'\n')