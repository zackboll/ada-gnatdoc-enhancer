"""Read-only retained native/source binding; generate with unchanged merged main."""
import hashlib
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes

E = Path('/home/zboll/qualifications/gnatdoc019')
S = E/'baseline-source'
records = {}
for label, native, source, config_root, config_name in [
    ('historical-imgproc', Path('/home/zboll/qualification/gnatdoc012r2/historical-profile-imgproc'),
     E/'historical-opencv-image_processing.ads', None, None),
    ('current-imgproc', Path('/home/zboll/git/opencv/imgproc-gnatdoc009-evidence/reconciled-native'),
     E/'current-opencv-image_processing.ads', Path('/home/zboll/gnatdoc-018-evidence/r1/authority'), 'direct.toml'),
]:
    root = E/label; root.mkdir()
    if config_root:
        shutil.copytree(config_root/'qualification-public', root/'qualification-public')
        assert (root/'qualification-public/opencv-image_processing.ads').read_bytes() == source.read_bytes()
        shutil.copyfile(config_root/'categories.json', root/'categories.json')
        (root/'qualification.toml').write_bytes((config_root/config_name).read_bytes())
        authority = json.loads(Path('/home/zboll/gnatdoc-018-evidence/imgproc-baseline.json').read_text())
        assert hashes(native) == authority['pristine_sha256']
    else:
        authority = json.loads((S/'docs/evidence/gnatdoc002/imgproc-input.json').read_text())
        assert hashes(native) == authority['pristine_sha256']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == authority['source_sha256']['src/opencv-image_processing.ads']
        (root/'qualification-public').mkdir()
        shutil.copyfile(source, root/'qualification-public/opencv-image_processing.ads')
        (root/'docs').mkdir()
        shutil.copyfile(E/'historical-categories.json', root/'docs/api-categories.json')
        assert hashlib.sha256((root/'docs/api-categories.json').read_bytes()).hexdigest() == authority['source_sha256']['docs/api-categories.json']
        (root/'qualification.toml').write_text(authority['configuration'])
    shutil.copytree(native, root/'pristine')
    shutil.copytree(native, root/'site')
    c = load(root, 'qualification.toml')
    destinations = source_destinations(c, snapshot(c, root/'pristine'))
    proof = [dict(package=d.package, name=d.declaration.name, ordinal=d.ordinal, overloads=d.total,
                  href=d.href, native_profile=d.section.code, source_profile=d.declaration.signature,
                  source_line=d.declaration.line) for group in destinations.values() for d in group]
    if not config_root:
        old = json.loads((S/'docs/evidence/gnatdoc008b/source-native-proof.json').read_text())
        assert [{k:d[k] for k in proof[0]} for d in old] == proof
    (root/'oracle.json').write_text(json.dumps(proof, indent=2)+'\n')
    result = enhance(c, root/'site'); verify(c, root/'site')
    assert (root/'site/api/gnatdoc-navigation.js').read_bytes() == (S/'src/ada_gnatdoc_enhancer/assets/gnatdoc-navigation.js').read_bytes()
    records[label] = dict(native_sha256=hashes(native), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                          declarations=len(proof), publication=result, freshly_generated=False)
    print(label, len(proof), 'source/native bound, unchanged main generated', flush=True)
(E/'baseline-inputs.json').write_text(json.dumps(records, indent=2)+'\n')