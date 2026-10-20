"""Observed malformed-distribution controls against the final release auditor."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import stat
import tarfile
import zipfile

E = Path(__file__).resolve().parent
S = E/'final-source'
P = E/'final/python-3.13'
wheel = next((P/'artifacts').glob('*.whl'))
sdist = next((P/'artifacts').glob('*.tar.gz'))
rebuilt = next((P/'rebuilt').glob('*.whl'))
spec = importlib.util.spec_from_file_location('audit', S/'scripts/check_distributions.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
out = E/'archive-negatives'; out.mkdir()
results = {}


def check(label, w=wheel, t=sdist):
    try:
        module.audit(S, w, t, rebuilt)
    except (ValueError, KeyError) as error:
        results[label] = dict(mutation_observed=True, rejected=str(error))
    else:
        raise AssertionError('accepted '+label)


def wheel_case(label, modify=lambda n,d: (n,d), extra=None):
    target = out/(label+'.whl')
    with zipfile.ZipFile(wheel) as src, zipfile.ZipFile(target, 'w') as dst:
        for member in src.infolist():
            pair = modify(member.filename, src.read(member.filename))
            if pair is not None:
                name, data = pair
                member = copy.copy(member); member.filename = name
                dst.writestr(member, data)
        if extra:
            member, data = extra; dst.writestr(member, data)
    assert target.read_bytes() != wheel.read_bytes()
    check(label, w=target)


wheel_case('changed-router', lambda n,d: (n,b'/* tamper */') if n.endswith('/assets/gnatdoc-symbol-navigation.js') else (n,d))
wheel_case('missing-asset', lambda n,d: None if n.endswith('/assets/gnatdoc-symbol-navigation.js') else (n,d))
wheel_case('runtime-dependency', lambda n,d: (n,d.replace(b'Requires-Python:',b'Requires-Dist: unexpected-runtime\nRequires-Python:')) if n.endswith('/METADATA') else (n,d))
wheel_case('absolute-metadata', lambda n,d: (n,d.replace(b'Author:',b'Unexpected-Path: /home/build/private\nAuthor:')) if n.endswith('/METADATA') else (n,d))
wheel_case('generated-file', extra=('ada_gnatdoc_enhancer/__pycache__/module.pyc',b'junk'))
wheel_case('absolute-wheel-path', extra=('/absolute',b'junk'))
wheel_case('traversal-wheel-path', extra=('../escape',b'junk'))
for label, kind in [('symlink', stat.S_IFLNK), ('fifo', stat.S_IFIFO), ('device', stat.S_IFCHR)]:
    member = zipfile.ZipInfo('ada_gnatdoc_enhancer-0.1.0.dist-info/'+label)
    member.create_system = 3; member.external_attr = (kind|0o777)<<16
    wheel_case('wheel-'+label, extra=(member,b'METADATA'))
wheel_case('duplicate-wheel', extra=('ada_gnatdoc_enhancer/__init__.py',b'junk'))

for label, name, kind in [('symlink', 'ada_gnatdoc_enhancer-0.1.0/link',tarfile.SYMTYPE),
                          ('hardlink','ada_gnatdoc_enhancer-0.1.0/link',tarfile.LNKTYPE),
                          ('fifo','ada_gnatdoc_enhancer-0.1.0/fifo',tarfile.FIFOTYPE),
                          ('traversal','ada_gnatdoc_enhancer-0.1.0/../../escape',tarfile.REGTYPE),
                          ('absolute','/escape',tarfile.REGTYPE),
                          ('duplicate','ada_gnatdoc_enhancer-0.1.0/PKG-INFO',tarfile.REGTYPE)]:
    target = out/('sdist-'+label+'.tar.gz')
    with tarfile.open(sdist) as src, tarfile.open(target,'w:gz') as dst:
        for member in src.getmembers():
            dst.addfile(member, src.extractfile(member) if member.isfile() else None)
        member = tarfile.TarInfo(name); member.type = kind
        if kind in (tarfile.SYMTYPE,tarfile.LNKTYPE): member.linkname='PKG-INFO'
        dst.addfile(member, io.BytesIO(b''))
    assert target.read_bytes() != sdist.read_bytes()
    check('sdist-'+label,t=target)
(E/'distribution-audit-negative-controls.json').write_text(json.dumps(results,indent=2)+'\n')
print(len(results), 'observed malformed archives rejected')