"""Read-only retained acquisition audit and three identified publication campaigns."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from dataclasses import replace

E = Path(__file__).resolve().parent
S = E/'source'
R3 = Path('/home/zboll/qualification/gnatdoc011r3')
W = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r1-work')
W2 = Path('/home/zboll/git/ada-gnatdoc-enhancer-011r2-work')
M = Path('/home/zboll/qualification/mel-doc010-20261019')
sys.path[:0] = [str(S/'src'), str(S/'scripts')]
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes


def save(name, data):
    (E/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def file_sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def checked_copy(src, dst):
    shutil.copytree(src, dst)
    assert hashes(src) == hashes(dst)


sources = json.loads((W/'acquisition-source-proof.json').read_text())
native = json.loads((S/'docs/evidence/gnatdoc011r2/acquisition-preservation.json').read_text())
identities = {}
for label in ('core-current', 'core-050'):
    core = W/label
    revision = subprocess.check_output(['git', '-C', str(core), 'rev-parse', 'HEAD'], text=True).strip()
    assert revision == sources[label]['revision'] == native[label]['source_revision']
    assert {n: file_sha(core/n) for n in sources[label]['source_sha256']} == sources[label]['source_sha256']
    assert hashes(W/(label+'-pristine')) == native[label]['pristine_sha256']
    assert not subprocess.check_output(['git', '-C', str(core), 'diff', 'HEAD', '--', 'src', 'scripts'])
    checked_copy(R3/(label+'-authority'), E/(label+'-authority'))
    checked_copy(R3/(label+'-default-authority'), E/(label+'-default-authority'))
    identities[label] = dict(revision=revision, source_files=len(sources[label]['source_sha256']),
                             pristine_files=len(native[label]['pristine_sha256']), fresh_acquisition=False)

# MEL retained native bytes are authorized by the independently retained acquisition
# evidence manifest, not by any candidate-generated presentation manifest.
manifest = json.loads((M/'EVIDENCE-MANIFEST.json').read_text())
mel_pristine = {n.removeprefix('pristine-first/'): h for n,h in manifest.items() if n.startswith('pristine-first/')}
assert hashes(M/'pristine-first') == mel_pristine
mel_root = Path('/home/zboll/git/ams-mel-doc-010')
revision = subprocess.check_output(['git', '-C', str(mel_root), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == '36ecb1e63c24df855d6f6e85f8245e16fc9d8d53'
tracked = subprocess.check_output(['git', '-C', str(mel_root), 'ls-tree', '-r', 'HEAD', '--', 'ada/src', 'docs'], text=True)
source_ledger = {}
for line in tracked.splitlines():
    mode, kind, rest = line.split(' ', 2)
    oid, name = rest.split('\t', 1)
    assert kind == 'blob' and mode != '120000'
    data = (mel_root/name).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() == oid, name
    source_ledger[name] = hashlib.sha256(data).hexdigest()
assert not subprocess.check_output(['git', '-C', str(mel_root), 'status', '--porcelain=v1'])
checked_copy(R3/'mel-authority', E/'mel-authority')
assert hashes(E/'mel-authority/ada/src') == hashes(mel_root/'ada/src')
assert hashes(E/'mel-authority/docs') == hashes(mel_root/'docs')
identities['mel'] = dict(revision=revision, source_files=len(source_ledger),
                         source_sha256=source_ledger, pristine_sha256=mel_pristine, fresh_acquisition=False)
save('retained-input-verification.json', identities)

def generate(root, config, pristine, destination, campaign):
    checked_copy(pristine, destination)
    env = dict(os.environ, PYTHONPATH=str(E/('source-'+campaign)/'src') if campaign != 'release' else str(S/'src'))
    program = '''import json,sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
from ada_gnatdoc_enhancer.qualification import hashes
c=load(Path(sys.argv[1]),sys.argv[2]);p=Path(sys.argv[3]);counts=enhance(c,p);verify(c,p)
before=hashes(p);enhance(c,p);verify(c,p);assert hashes(p)==before
print(json.dumps(counts))'''
    result = subprocess.check_output([sys.executable, '-c', program, str(root), config, str(destination)],
                                     env=env, cwd=E, text=True)
    return json.loads(result)


def compare(a, b, allowed, version_only=False):
    old, new = hashes(a), hashes(b)
    assert old.keys() == new.keys()
    delta = sorted(n for n in old if old[n] != new[n])
    assert delta == sorted(allowed), delta
    if version_only:
        assert (b/'api/presentation.json').read_bytes() == (a/'api/presentation.json').read_bytes().replace(
            b'"enhancer_version": "0.1.0.dev0"', b'"enhancer_version": "0.1.0"')
    else:
        ma = json.loads((a/'api/presentation.json').read_text())
        mb = json.loads((b/'api/presentation.json').read_text())
        keys = {k for k in ma if ma[k] != mb[k]}
        assert keys == {'output_sha256'}, keys
        assert {k for k in ma['output_sha256'] if ma['output_sha256'][k] != mb['output_sha256'][k]} == {'api/gnatdoc-navigation.js'}
    return dict(files=len(new), changed=delta, before=old, after=new,
                fingerprint=hashlib.sha256(json.dumps(new, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                manifest_version_substitution_only=version_only)


report = {}
counts = {}
for label in ('core-current', 'core-050', 'mel'):
    if label == 'mel':
        root = E/'mel-authority'
        api_pristine = E/'mel-api-pristine'
        api_pristine.mkdir()
        checked_copy(M/'pristine-first/api', api_pristine/'api')
        cfg = load(root, 'docs/gnatdoc-enhance.toml')
        # Config authorizes symbols through an explicit copied TOML opt-in.
        text = (root/'docs/gnatdoc-enhance.toml').read_text()
        (root/'docs/symbols.toml').write_text(text.replace('[navigation]', '[navigation]\nsymbol_bookmarks = true\ndefault_package = "AMS.MEL"'))
        configs = [('default', root, 'docs/gnatdoc-enhance.toml'), ('symbols', root, 'docs/symbols.toml')]
        pristine = api_pristine
    else:
        root = E/(label+'-authority')
        pristine = W/(label+'-pristine')
        configs = [('default', E/(label+'-default-authority'), 'default.toml'),
                   ('symbols', root, 'disabled.toml'), ('instance', root, 'qualification.toml')]
    for mode, authority, config in configs:
        key = label+'-'+mode
        before = hashes(authority)
        sites = {}
        for campaign in ('R2', 'R3', 'old-release', 'release'):
            destination = E/(key+'-'+campaign)
            counts[key+'-'+campaign] = generate(authority, config, pristine, destination, campaign)
            if label == 'mel':
                complete = E/(key+'-'+campaign+'-complete')
                checked_copy(M/'pristine-first', complete)
                shutil.copytree(destination/'api', complete/'api', dirs_exist_ok=True)
                sites[campaign] = complete
            else:
                sites[campaign] = destination
        second = E/(key+'-second')
        generate(authority, config, pristine, second, 'release')
        assert hashes(second) == hashes(E/(key+'-release'))
        assert hashes(authority) == before
        r3 = hashes(sites['R3']); r2 = hashes(sites['R2'])
        approved_r3 = (R3/(key+'-complete-first') if label == 'mel' else
                       R3/(key+'-first') if mode != 'default' else R3/(label+'-default-corrected'))
        assert r3 == hashes(approved_r3), key+' does not reproduce independently reviewed R3'
        if label == 'mel': approved_r2 = M/('site-C' if mode == 'symbols' else 'site-B')
        elif mode == 'instance': approved_r2 = W2/(label+'-candidate')
        elif mode == 'symbols': approved_r2 = W/(label+'-disabled')
        else: approved_r2 = R3/(label+'-default-base')
        assert r2 == hashes(approved_r2), key+' does not reproduce historical R2'
        delta = ['api/gnatdoc-navigation.js', 'api/presentation.json'] if mode == 'symbols' else []
        if delta:
            r2_r3 = compare(sites['R2'], sites['R3'], delta)
        else:
            assert r2 == r3
            r2_r3 = dict(files=len(r3), changed=[], sha256=r3)
        release_delta = compare(sites['R3'], sites['release'], ['api/presentation.json'], version_only=True)
        if delta: old_release_delta = compare(sites['old-release'], sites['release'], delta)
        else:
            assert hashes(sites['old-release']) == hashes(sites['release'])
            old_release_delta = dict(files=len(r3), changed=[])
        report[key] = dict(R2_to_R3=r2_r3, R3_development_to_release=release_delta,
                           old_release_to_corrected=old_release_delta,
                           two_copy_determinism=True, byte_idempotence=True, authority_unchanged=True)
        if mode in ('symbols', 'instance'):
            asset = 'gnatdoc-symbol-navigation.js' if mode == 'symbols' else 'gnatdoc-instance-navigation.js'
            assert (sites['release']/'api/gnatdoc-navigation.js').read_bytes() == (S/'src/ada_gnatdoc_enhancer/assets'/asset).read_bytes()
        print(key, counts[key+'-release'], flush=True)
        save('publication-comparisons-progress.json', report)
save('publication-comparisons.json', report)
save('publication-counts.json', counts)

# Execute unchanged source/native independent audits in separate processes.
for label in ('core-current', 'core-050'):
    core = W/label
    for mode in ('symbols', 'instance'):
        output = E/(label+'-'+mode+'-native-audit.json')
        program = ('import json;from pathlib import Path;from qualify_symbol_bookmarks import audit;'
                   'r=audit(Path('+repr(str(core))+'),Path('+repr(str(W/(label+'-pristine')))+'),'
                   'Path('+repr(str(E/(label+'-'+mode+'-release')))+'),instance_references='+repr(mode=='instance')+');'
                   'Path('+repr(str(output))+').write_text(json.dumps(r,indent=2))')
        env = dict(os.environ, PYTHONPATH=str(S/'src')+':'+str(S/'scripts'))
        subprocess.run([sys.executable, '-c', program], env=env, cwd=E, check=True)
        result = json.loads(output.read_text())
        assert result['symbols'] == json.loads((S/'docs/evidence/gnatdoc011r3'/(label+'-native-symbol-audit.json')).read_text())['symbols']
        assert result['public_symbols'] == 215 and result['public_packages'] == 195
        assert result['native_sections'] == (1282 if label == 'core-current' else 1268)
    command = [sys.executable, str(S/'scripts/qualify_instance_references.py'), '--core', str(core),
               '--pristine', str(W/(label+'-pristine')), '--legacy', str(core/'_site'),
               '--candidate', str(E/(label+'-instance-release')), '--baseline', str(E/(label+'-symbols-release')),
               '--output', str(E/(label+'-occurrences.json'))]
    subprocess.run(command, env=env, check=True, cwd=E)
    assert json.loads((E/(label+'-occurrences.json')).read_text()) == json.loads((W2/(label+'-occurrences.json')).read_text())
    shutil.copy2(R3/(label+'-browser-oracle.json'), E/(label+'-browser-oracle.json'))
shutil.copy2(R3/'mel-browser-oracle.json', E/'mel-browser-oracle.json')
# Independent MEL inventory must equal each published native symbol mapping.
rows = json.loads((S/'docs/evidence/gnatdoc011r3/independent-symbol-inventory.json').read_text())
index = (E/'mel-symbols-release/api/index.html').read_text()
import re
links = re.findall(r'<a href="([a-f0-9]{64}\.html#[a-f0-9]{64})" data-symbol="([^"]+)"></a>', index)
metadata = dict((name, target) for target, name in links)
assert len(rows) == 238
assert metadata == {row['canonical']: row['page']+'#'+row['anchor'] for row in rows}
assert sum(row['kind'] == 'type' for row in rows) == 231
assert sum(row['kind'] == 'subtype' for row in rows) == 7
assert len({row['owner'] for row in rows}) == 24
from html.parser import HTMLParser
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href'): self.links.append(value)
    handle_startendtag = handle_starttag
complete = E/'mel-symbols-release-complete'
assert len(hashes(complete)) == 43
assert len(list(complete.rglob('*.html'))) == 38
references = 0
for page in complete.rglob('*.html'):
    parser = Page(); parser.feed(page.read_text()); references += len(parser.links)
assert references == 3259, references
save('real-qualification-complete.json', dict(source_native_audits=True, campaigns=list(report),
                                            mel_symbols=len(rows), mel_metadata=metadata,
                                            mel_files=43, mel_html=38, mel_references=references))