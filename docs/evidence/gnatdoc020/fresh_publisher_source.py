from pathlib import Path
import subprocess,tarfile,json,hashlib,io,sys
E=Path('/home/zboll/qualifications/gnatdoc020');O=E/'publisher';pin='33a2a4f3b83606a5c779b8a93abeb6c91fa49a21'
raw=subprocess.check_output(['gh','api','repos/zackboll/opencv_core_ada/tarball/'+pin]);(O/'source.tar.gz').write_bytes(raw)
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 content={m.name.split('/',1)[1]:t.extractfile(m).read() for m in t if m.isfile() and '/' in m.name}
A=Path('/home/zboll/gnatdoc-018-evidence/r1/authority');q=json.loads((A/'qualified.json').read_text());source=A/q['source'];expected={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for n,b in expected.items():assert content[n]==b,n
router=content[q['router_source']];assert hashlib.sha256(router).hexdigest()=='cba37439fa02e5b00e1f9de6648aca86ca3aaac61f2b8e01a45b8d99bf9ec497'
(O/'source-identity.json').write_text(json.dumps(dict(source_revision=pin,archive_sha256=hashlib.sha256(raw).hexdigest(),qualified_source_files=len(expected),all_qualified_source_bytes_match=True,router_sha256=hashlib.sha256(router).hexdigest(),deployed_source_not_current_main=True),indent=2)+'\n');print('Fresh pinned publisher source and approved router bytes match')
