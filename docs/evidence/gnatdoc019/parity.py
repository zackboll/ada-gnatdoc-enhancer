"""Complete publication regeneration, exact merged-main/candidate byte classification."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

E=Path('/home/zboll/qualifications/gnatdoc019')
S=Path('/home/zboll/git/ada-gnatdoc-enhancer-019')
T=Path('/home/zboll/gnatdoc-017-evidence')
R=Path('/home/zboll/qualification/gnatdoc012r2')
O=E/'parity';O.mkdir(exist_ok=False)
entries=[('current-core-symbols',T/'authority','default.toml',T/'pristine'),
         ('current-core-incoming',T/'authority','default-incoming.toml',T/'pristine')]
for label in ('core-current','core-050'):
    for profile,root,config in [('packages',R/(label+'-default-authority'),'default.toml'),
                                ('symbols',R/(label+'-authority'),'disabled.toml'),
                                ('incoming',R/(label+'-authority'),'qualification.toml')]:
        publication=R/(label+'-'+('default' if profile=='packages' else 'instance' if profile=='incoming' else 'symbols')+'-release')
        entries.append((label+'-'+profile,root,config,publication))
for profile,config in [('packages','docs/gnatdoc-enhance.toml'),('symbols','docs/symbols.toml')]:
    entries.append(('mel-'+profile,R/'mel-authority',config,R/('mel-'+('default' if profile=='packages' else 'symbols')+'-release')))
for name in ('core','imgproc','geometry','mel'):
    entries.append(('authored-'+name,S/'tests/authored-fixtures'/name,'project.toml',S/'tests/authored-fixtures'/name/'native'))
    entries.append(('synthetic-'+name,S/'tests/fixtures'/name,'project.toml',S/'tests/fixtures'/name/'_site'))
entries.extend([('features',T/'features-authority','docs/gnatdoc-enhance.toml',Path('/home/zboll/git/opencv/features-doc-011-evidence/final-hosted/native')),
                ('imgproc81',Path('/home/zboll/gnatdoc-018-evidence/imgproc-authority'),'candidate.toml',Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native'))])
assert len(entries)==20
for label in ('historical-imgproc','current-imgproc'):
    entries.append((label,E/label,'qualification.toml',E/label/'pristine'))
entries.extend([('current-core-custom-symbols',T/'authority','custom.toml',T/'pristine'),
                ('current-core-custom-incoming',T/'authority','custom-incoming.toml',T/'pristine')])
program='''import json,sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes,preserve_native,identities
c=load(Path(sys.argv[1]),sys.argv[2]);s=Path(sys.argv[3]);p=Path(sys.argv[4])
r=enhance(c,s);verify(c,s);before=hashes(s);enhance(c,s);assert before==hashes(s)
preservation=preserve_native(identities(p),s,config=c,pristine=p)
print(json.dumps(dict(default=c.navigation!='none' and not c.symbol_bookmarks and not c.instance_references,hashes=before,result=r,native_preservation=preservation)))
'''
report={}
for label,root,config,native in entries:
    stage=O/label;pristine=stage/'pristine';(pristine/'api').mkdir(parents=True)
    if (native/'api/presentation.json').exists():
        data=json.loads((native/'api/presentation.json').read_text())
        for name,text in data['original_api_html'].items():(pristine/name).write_text(text)
        shutil.copyfile(native/'api/gnatdoc.css',pristine/'api/gnatdoc.css')
    else:shutil.copytree(native,pristine,dirs_exist_ok=True)
    results={}
    for kind,src in [('baseline',E/'baseline-source/src'),('candidate',S/'src'),('second',S/'src')]:
        site=stage/kind;shutil.copytree(pristine,site)
        env=dict(os.environ,PYTHONPATH=str(src))
        result=subprocess.run(['/home/zboll/git/ada-gnatdoc-enhancer/.venv/bin/python','-c',program,str(root),config,str(site),str(pristine)],cwd=O,env=env,text=True,capture_output=True)
        (stage/(kind+'.log')).write_text(result.stdout+result.stderr);result.check_returncode()
        results[kind]=json.loads(result.stdout)
    assert results['candidate']['hashes']==results['second']['hashes'],label+' nondeterministic'
    a=results['baseline']['hashes'];b=results['candidate']['hashes'];assert a.keys()==b.keys(),label+' file inventory'
    changed=sorted(n for n in a if a[n]!=b[n])
    if results['candidate']['default']:
        assert changed==['api/gnatdoc-navigation.js','api/presentation.json'],(label,changed)
        old=json.loads((stage/'baseline/api/presentation.json').read_text())
        new=json.loads((stage/'candidate/api/presentation.json').read_text())
        assert new['output_sha256']['api/gnatdoc-navigation.js']==b['api/gnatdoc-navigation.js']
        new['output_sha256']['api/gnatdoc-navigation.js']=old['output_sha256']['api/gnatdoc-navigation.js']
        assert new==old,label+' unrelated manifest field changed'
    else:assert changed==[],(label,changed)
    for n in set(a)-set(changed):assert (stage/'baseline'/n).read_bytes()==(stage/'candidate'/n).read_bytes()
    report[label]=dict(changed=changed,files=len(a),deterministic=True,byte_idempotent=True,results=results)
    (O/'parity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(label,len(a),'files',changed,flush=True)