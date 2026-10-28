from pathlib import Path
import importlib.util,tarfile,zipfile,json,io,shutil
E=Path('/home/zboll/qualifications/gnatdoc020');S=E/'delivery-source';spec=importlib.util.spec_from_file_location('audit',S/'scripts/check_distributions.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
D=E/'distributions/python-3.11';wheel=next((D/'artifacts').glob('*.whl'));sdist=next((D/'artifacts').glob('*.tar.gz'));rebuilt=next((D/'rebuilt').glob('*.whl'));O=E/'archive-version-mutations';O.mkdir();report={}
for label,target in [('wheel','ada_gnatdoc_enhancer-0.1.2.dist-info/METADATA'),('sdist','PKG-INFO'),('egg-info','src/ada_gnatdoc_enhancer.egg-info/PKG-INFO')]:
 root=O/label;root.mkdir();w=root/wheel.name;t=root/sdist.name
 if label=='wheel':
  shutil.copyfile(sdist,t)
  with zipfile.ZipFile(wheel) as z,zipfile.ZipFile(w,'w') as out:
   for m in z.infolist():
    b=z.read(m.filename)
    if m.filename==target:
     assert b'Version: 0.1.2\n' in b;b=b.replace(b'Version: 0.1.2\n',b'Version: 0.1.1\n',1)
    out.writestr(m,b)
 else:
  shutil.copyfile(wheel,w)
  with tarfile.open(sdist) as archive,tarfile.open(t,'w:gz') as out:
   for m in archive:
    b=archive.extractfile(m).read() if m.isfile() else None
    if m.name=='ada_gnatdoc_enhancer-0.1.2/'+target:
     assert b'Version: 0.1.2\n' in b;b=b.replace(b'Version: 0.1.2\n',b'Version: 0.1.1\n',1);m.size=len(b)
    out.addfile(m,io.BytesIO(b) if b is not None else None)
 try:a.audit(S,w,t,rebuilt)
 except ValueError as exc:report[label]=dict(rejected=True,reason=str(exc),mutation='Version: 0.1.1 under correctly named 0.1.2 archive')
 else:raise AssertionError(label+' old metadata accepted')
(E/'archive-version-mutations.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
