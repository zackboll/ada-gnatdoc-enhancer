"""Compare reconstructed publications; only the reviewed router delta is allowed."""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

E=Path('/home/zboll/qualification/gnatdoc011r3')
R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
M=Path('/home/zboll/qualification/mel-doc010-20261019')
W=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
W2=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify, expected_output, _presentation, MANIFEST
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, sorted_json

def generate(config,pristine,destination):
    shutil.copytree(pristine,destination)
    enhance(config,destination);verify(config,destination)
    before=hashes(destination);enhance(config,destination);verify(config,destination)
    assert before==hashes(destination),'byte idempotence'
    return before

def compare(old,new,label,changed):
    a,b=hashes(old),hashes(new);assert a.keys()==b.keys(),label
    delta=[n for n in a if a[n]!=b[n]]
    assert set(delta)==set(changed),(label,delta)
    return {'files':len(b),'changed':delta,'before':a,'after':b,
            'fingerprint':digest(json.dumps(b,sort_keys=True,separators=(',',':')).encode())}

report={}
mel=E/'mel-authority';(mel/'ada').mkdir(parents=True,exist_ok=True)
if not (mel/'ada/src').exists():
    shutil.copytree(Path('/home/zboll/git/ams-mel-doc-010/ada/src'),mel/'ada/src')
    shutil.copytree(Path('/home/zboll/git/ams-mel-doc-010/docs'),mel/'docs')
assert hashes(mel/'ada/src')==hashes(Path('/home/zboll/git/ams-mel-doc-010/ada/src'))
config=load(mel,'docs/gnatdoc-enhance.toml')
for mode,cfg in [('default',config),('symbols',replace(config,symbol_bookmarks=True,default_package='AMS.MEL'))]:
    stage=E/('mel-'+mode+'-pristine')
    if not stage.exists():
        stage.mkdir();shutil.copytree(M/'pristine-first/api',stage/'api')
    for copy in ['first','second']:
        generated=E/('mel-'+mode+'-'+copy)
        if not generated.exists():generate(cfg,stage,generated)
        complete=E/('mel-'+mode+'-complete-'+copy)
        if not complete.exists():
            shutil.copytree(M/'pristine-first',complete)
            shutil.copytree(generated/'api',complete/'api',dirs_exist_ok=True)
    assert hashes(E/('mel-'+mode+'-complete-first'))==hashes(E/('mel-'+mode+'-complete-second'))
    report['mel-'+mode]=compare(M/('site-C' if mode=='symbols' else 'site-B'),
        E/('mel-'+mode+'-complete-first'),mode,
        ['api/gnatdoc-navigation.js','api/presentation.json'] if mode=='symbols' else [])

preservation=json.loads((R/'docs/evidence/gnatdoc011r2/acquisition-preservation.json').read_text())
for label in ['core-current','core-050']:
    pristine=W/(label+'-pristine');core=W/label
    assert hashes(pristine)==preservation[label]['pristine_sha256']
    assert subprocess.check_output(['git','-C',str(core),'rev-parse','HEAD'],text=True).strip()==preservation[label]['source_revision']
    assert not subprocess.check_output(['git','-C',str(core),'diff','HEAD','--','src','scripts'])
    authority=E/(label+'-authority')
    if not authority.exists():shutil.copytree(W/(label+'-authority'),authority)
    for mode,filename in [('symbols','disabled.toml'),('instance','qualification.toml')]:
        cfg=load(authority,filename)
        for copy in ['first','second']:
            destination=E/(label+'-'+mode+'-'+copy)
            if not destination.exists():generate(cfg,pristine,destination)
        assert hashes(E/(label+'-'+mode+'-first'))==hashes(E/(label+'-'+mode+'-second'))
        original=W/(label+'-disabled') if mode=='symbols' else W2/(label+'-candidate')
        report[label+'-'+mode]=compare(original,E/(label+'-'+mode+'-first'),label+'-'+mode,
            ['api/gnatdoc-navigation.js','api/presentation.json'] if mode=='symbols' else [])
    # Independent unchanged Core source/native oracle, not candidate symbols.
    sys.path.insert(0,str(R/'scripts'))
    from qualify_symbol_bookmarks import audit
    for name in ['link_gnatdoc_types','highlight_gnatdoc_ada','compare_gnatdoc_warnings']:
        sys.modules.pop(name,None)
    result=audit(core,pristine,E/(label+'-symbols-first'))
    (E/(label+'-native-symbol-audit.json')).write_text(json.dumps(result,indent=2)+'\n')
    old=json.loads((W2/(label+'-native-symbol-audit.json')).read_text())
    assert result['symbols']==old['symbols']
    text=(E/(label+'-symbols-first/api/index.html')).read_text()
    primary='OpenCV.Core.Mat';secondary='OpenCV.Rect'
    entries={}
    for canonical,target in result['symbols'].items():
        page,anchor=target.split('#')
        raw=(pristine/'api'/page).read_text()
        match=re.search(r'<h4 id='+anchor+r'>([^<]+)</h4><pre class=ada-code-snippet><code>(.*?)</code></pre>',raw,re.S)
        assert match is not None
        entries[canonical]={'owner':canonical.rpartition('.')[0],'page':page,'anchor':anchor,'native_profile':html.unescape(match[2])}
    packages=dict((name,filename) for filename,name in re.findall(r'<a href=([a-f0-9]{64}\.html) target=document-content>([^<]+)</a>',text))
    # Pick a genuine sidebar declaration not aliased to a public type.
    targets=set(result['symbols'].values())
    target=next(iter(result['symbols'].values()))
    canonical=next(n for n,t in result['symbols'].items() if t==target)
    filename,anchor=target.split('#');owner=next(n for n,f in packages.items() if f==filename)
    browser={'revision':result['core_revision'],'default_package':'OpenCV.Core','alternate_package':'OpenCV.Core.Sparse',
             'primary':primary,'secondary':secondary,'symbols':entries,'packages':packages,
             'api_files':[p.name for p in (E/(label+'-symbols-first/api')).iterdir()],
             'declaration':{'owner':owner,'page':filename,'anchor':anchor,'symbol':canonical}}
    (E/(label+'-browser-oracle.json')).write_text(json.dumps(browser,indent=2)+'\n')
    print(label,'source/native symbols:',len(entries),flush=True)

(E/'publication-comparisons.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:{'files':v['files'],'changed':v['changed'],'fingerprint':v['fingerprint']} for k,v in report.items()},flush=True)