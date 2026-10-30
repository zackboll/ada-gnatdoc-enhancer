from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native

root = Path('/tmp/gnatdoc024')
fixture = root/'source/tests/real-fixtures/search-core'
approved = {r['href']:r for r in json.loads((fixture/'oracle.json').read_text())}
report = {}
for variant in ('default', 'symbol', 'instance'):
    site = root/'search-sites'/variant
    authority = root/'search-sites/authority'
    config = load(authority, variant+'-search.toml')
    verify(config, site)
    before = hashes(site)
    second = root/('search-independent-'+variant); shutil.copytree(fixture/'pristine', second)
    enhance(config, second); verify(config, second); assert hashes(second) == before
    enhance(config, site); assert hashes(site) == before
    old = hashes(root/'compatibility'/('new-core-'+variant))
    added = sorted(set(before)-set(old))
    changed = sorted(p for p in before.keys() & old.keys() if before[p] != old[p])
    assert added == ['api/gnatdoc-search-index.json', 'api/gnatdoc-search.css']
    assert changed == ['api/gnatdoc-navigation.js', 'api/index.html', 'api/presentation.json']
    index = json.loads((site/'api/gnatdoc-search-index.json').read_text())
    counts = dict(Counter(r['kind'] for r in index['records']))
    assert counts == dict(package=195, symbol=215, operation=1047, guide=5)
    assert len(index['records']) == 1462
    for r in index['records']:
        if r['kind'] not in ('symbol', 'operation'): continue
        oracle = approved[r['href']]
        assert r['name'] == oracle['package']+'.'+oracle['name']
    theme = site/'api/gnatdoc-theme.css'
    assert theme.read_bytes() == (authority/'docs/assets/gnatdoc-theme.css').read_bytes()
    report[variant] = dict(status='passed', added_files=added, changed_files=changed,
        records=len(index['records']), counts=counts, deterministic=True, idempotent=True,
        native_preservation=preserve_native(identities(fixture/'pristine'), site,
                                            config=config, pristine=fixture/'pristine'),
        custom_theme_sha256=hashlib.sha256(theme.read_bytes()).hexdigest(),
        publication_sha256=before, index_native_oracle_verified=True)
(root/'search-publication.json').write_text(json.dumps(report, indent=2)+'\n')