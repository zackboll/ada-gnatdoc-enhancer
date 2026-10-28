"""Exact official v0.1.1 / candidate output comparison, no version normalization."""
import json
import os
from pathlib import Path
import shutil
import subprocess

E = Path('/home/zboll/gnatdoc-017-evidence')
S = Path('/home/zboll/git/ada-gnatdoc-enhancer')
R = Path('/home/zboll/qualification/gnatdoc012r2')
official = E/'baseline-env/bin/python'
candidate = Path('/home/zboll/gnatdoc-018-evidence/r1/baseline-source/.unused')
O = Path('/home/zboll/gnatdoc-018-evidence/r1/default-parity'); O.mkdir()
entries = [('current-core-symbols', E/'authority', 'default.toml', E/'pristine'),
           ('current-core-incoming', E/'authority', 'default-incoming.toml', E/'pristine')]
for label in ('core-current', 'core-050'):
    for profile, root, config in [('packages', R/(label+'-default-authority'), 'default.toml'),
                                  ('symbols', R/(label+'-authority'), 'disabled.toml'),
                                  ('incoming', R/(label+'-authority'), 'qualification.toml')]:
        publication = R/(label+'-'+('default' if profile=='packages' else 'instance' if profile=='incoming' else 'symbols')+'-release')
        entries.append((label+'-'+profile,root,config,publication))
for profile, config in [('packages','docs/gnatdoc-enhance.toml'),('symbols','docs/symbols.toml')]:
    entries.append(('mel-'+profile,R/'mel-authority',config,R/('mel-'+('default' if profile=='packages' else 'symbols')+'-release')))
for name in ('core','imgproc','geometry','mel'):
    entries.append(('authored-'+name,S/'tests/authored-fixtures'/name,'project.toml',S/'tests/authored-fixtures'/name/'native'))
    entries.append(('synthetic-'+name,S/'tests/fixtures'/name,'project.toml',S/'tests/fixtures'/name/'_site'))
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
entries.extend([('features', E/'features-authority', 'docs/gnatdoc-enhance.toml', Path('/home/zboll/git/opencv/features-doc-011-evidence/final-hosted/native')), ('imgproc81', Path('/home/zboll/gnatdoc-018-evidence/imgproc-authority'), 'candidate.toml', Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native'))])
for label, root, config, native in entries:
    stage = O/label; pristine = stage/'pristine'; (pristine/'api').mkdir(parents=True)
    if (native/'api/presentation.json').exists():
        data = json.loads((native/'api/presentation.json').read_text())
        for name,text in data['original_api_html'].items(): (pristine/name).write_text(text)
        (pristine/'api/gnatdoc.css').write_bytes((native/'api/gnatdoc.css').read_bytes())
    else:
        shutil.copytree(native,pristine,dirs_exist_ok=True)
    results = {}
    for kind, python in [('official',official),('baseline',Path('/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python')),('candidate',Path('/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python'))]:
        site = stage/kind; shutil.copytree(pristine,site)
        env['PYTHONPATH'] = str(Path('/home/zboll/gnatdoc-018-evidence/r1/baseline-source/src')) if kind=='baseline' else str(Path('/home/zboll/git/ada-gnatdoc-enhancer/src')) if kind=='candidate' else ''
        results[kind] = json.loads(subprocess.check_output([python,'-c',program,root,config,site],cwd=O,env=env,text=True))
        assert ('site-packages' in results[kind]['module']) if kind=='official' else True
    assert results['official']['hashes'] == results['baseline']['hashes'] == results['candidate']['hashes'],label
    for name in results['official']['hashes']:
        assert (stage/'official'/name).read_bytes() == (stage/'candidate'/name).read_bytes(),(label,name)
    report[label] = results
    (O/'parity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(label,'exact byte parity',len(results['official']['hashes']),flush=True)