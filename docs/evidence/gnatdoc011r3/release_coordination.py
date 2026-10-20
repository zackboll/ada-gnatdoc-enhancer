"""Read-only release-branch integration preview, no merge or worktree changes."""
import json
from pathlib import Path
import subprocess
E=Path('/home/zboll/qualification/gnatdoc011r3');R=Path('/home/zboll/git/ada-gnatdoc-enhancer-011r3')
before=json.loads((E/'release-pr14-before.json').read_text())
current=json.loads(subprocess.check_output(['gh','pr','view','14','-R','zackboll/ada-gnatdoc-enhancer',
 '--json','number,title,state,headRefName,headRefOid,baseRefName,autoMergeRequest,url'],text=True))
assert current==before
release=current['headRefOid'];base='697d4ca91dc81812e501e501c9766d9b3ec88924'
paths=['src/ada_gnatdoc_enhancer/assets/gnatdoc-symbol-navigation.js','tests/symbol_canonicalization.cjs',
       'tests/test_symbol_canonicalization.py','docs/stable-public-symbol-bookmarks.md']
conflicts=[]
for path in paths:
 if subprocess.check_output(['git','-C',str(R),'diff','--name-only',base,release,'--',path],text=True):conflicts.append(path)
assert not conflicts
test=subprocess.check_output(['git','-C',str(R),'show',release+':tests/test_release.py'],text=True)
assert '7af8dd92f7f31ff9a14fd55a41d81d9bcfe9ae3bce8506f9254a376404ea7ee3' in test
result={'pr14_unchanged':True,'head':release,'textual_overlap_on_corrective_paths':conflicts,
 'required_followup':['incorporate independently approved corrective merge before release',
 'update tests/test_release.py old symbol-router digest to reviewed R3 digest; retain default/instance identities',
 'rerun release source/wheel/sdist Python matrix, browser, mutation and complete publication qualification',
 'retain old release evidence as historical; record new artifact digests and exact final head'],
 'release_tag_or_publication_authorized':False}
(E/'release-coordination.json').write_text(json.dumps(result,indent=2)+'\n');print(result)