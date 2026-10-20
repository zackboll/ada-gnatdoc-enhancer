import json,sys,re
from pathlib import Path
E=Path('/home/zboll/qualification/gnatdoc011r3');M=Path('/home/zboll/qualification/mel-doc010-20261019')
R=Path('/home/zboll/git/ams-mel-doc-010');sys.path[:0]=[str(R/'scripts'),str(R/'docs/tools')]
from local_type_audit import Authority
a=Authority(R,M/'pristine-first')
rows=json.loads((E/'independent-symbol-inventory.json').read_text())
symbols={r['page']+'#'+r['anchor'] for r in rows}
approved=re.findall(r'<a href=([a-f0-9]{64}\.html#[a-f0-9]{64}) target=document-content>',(M/'pristine-first/api/index.html').read_text())
target=next(href for href in approved if href in symbols)
page,anchor=target.split('#');declaration=a.sections[page,anchor]
canonical=next(r['canonical'] for r in rows if r['page']+'#'+r['anchor']==target)
result={'revision':'36ecb1e63c24df855d6f6e85f8245e16fc9d8d53','default_package':'AMS.MEL',
        'alternate_package':'AMS.MEL.IR','primary':'AMS.MEL.Session','secondary':'AMS.MEL.Version',
        'symbols':{r['canonical']:r for r in rows},
        'packages':{name:page for page,name in a.page_packages.items()},
        'api_files':[p.name for p in (E/'site-C/api').iterdir()],
        'declaration':{'owner':a.page_packages[page],'symbol':canonical,**{k:declaration[k] for k in ['page','anchor']}}}
(E/'mel-browser-oracle.json').write_text(json.dumps(result,indent=2)+'\n')