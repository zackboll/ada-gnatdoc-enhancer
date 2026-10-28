#!/usr/bin/env python3
"""Read-only GNATDOC-018 consumer pilot using independently acquired inputs.

The authority root must already contain direct.toml and a separately reviewed
qualified.json publisher record. No consumer/source acquisition or approval is
inferred here. The original native input and consumer-owned occurrence oracle
are mandatory. Output is disposable; no consumer repository is modified.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.external_symbols import qualified
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json


def qualify(args):
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    consumer = args.consumer.resolve(); authority = args.authority.resolve()
    direct = load(authority, 'direct.toml')
    require((authority/'qualification-public/opencv-image_processing.ads').read_bytes() ==
            (consumer/'src/opencv-image_processing.ads').read_bytes(), 'consumer public source differs')
    proposal = json.loads((consumer/'docs/evidence/gnatdoc009/r1/core-destination-proposal.json').read_text())
    names = sorted(item['identity'] for item in proposal['types'].values())
    options = dict(qualification='qualified.json', sha256=digest((authority/'qualified.json').read_bytes()), types=names)
    stable = replace(direct, external_symbol_bookmarks=options)
    symbols = qualified(stable)
    require(all(name in symbols for name in names), 'pilot identity absent from qualified publisher')
    sys.path.insert(0, str(consumer/'scripts'))
    import probe_core_candidate as oracle
    import check_doc_coverage as coverage

    outputs = {}; results = {}; occurrences = {}
    for mode, config in [('disabled', direct), ('stable', stable), ('stable-second', stable),
                         ('mixed', replace(stable, external_symbol_bookmarks={**options, 'types': [names[0]]}))]:
        site = output/mode; shutil.copytree(args.native, site)
        results[mode] = enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site)
        require(before == hashes(site), 'enhancement is not byte-idempotent')
        outputs[mode] = before
        selected = config.external_symbol_bookmarks.get('types', [])
        ledger = json.loads(json.dumps(proposal))
        for item in ledger['occurrences']:
            name = proposal['types'][item['core_identity']]['identity']
            item['proposed_url'] = symbols[name]['stable'] if name in selected else direct.externals[item['core_identity']]
        reconciliation = oracle.reconcile(args.native, site, ledger)
        require(reconciliation['core_occurrences'] == 586 and reconciliation['core_distinct_types'] == 14 and
                reconciliation['local_occurrences'] == 350, 'consumer occurrence count changed')
        items, missing, errors = coverage.check_site(site, consumer)
        require(len(items) == 1596 and not missing and not errors, 'consumer documentation coverage changed')
        results[mode]['reconciliation'] = reconciliation
        occurrences[mode] = ledger['occurrences']
    require(outputs['stable'] == outputs['stable-second'], 'fresh enhancement is nondeterministic')
    # Completely independent official installation/process, same original native bytes.
    site = output/'official'; shutil.copytree(args.native, site)
    program = '''import sys
from pathlib import Path
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance,verify
c=load(Path(sys.argv[1]),'direct.toml');s=Path(sys.argv[2]);enhance(c,s);verify(c,s)
'''
    env = dict(os.environ); env.pop('PYTHONPATH', None)
    subprocess.run([str(args.official_python), '-c', program, str(authority), str(site)],
                   check=True, cwd=output, env=env)
    outputs['official'] = hashes(site)
    require(outputs['official'] == outputs['disabled'], 'official v0.1.1 default bytes changed')
    for mode in ('stable', 'mixed'):
        changes = sorted(n for n in outputs[mode] if outputs[mode][n] != outputs['disabled'][n])
        require(len(changes) == 2 and 'api/presentation.json' in changes,
                'stable selection changed unrelated publication files')
        for name in changes:
            if name == 'api/presentation.json':
                a = json.loads((output/mode/name).read_bytes()); b = json.loads((output/'disabled'/name).read_bytes())
                a.pop('external_symbol_bookmarks'); a['output_sha256'] = b['output_sha256']
                require(a == b, 'stable mode changed unrelated integrity metadata')
                continue
            data = (output/mode/name).read_text()
            selected = names if mode == 'stable' else [names[0]]
            for symbol in selected:
                data = data.replace('href="' + html.escape(symbols[symbol]['stable'], quote=True) + '"',
                                    'href="' + html.escape(symbols[symbol]['native'], quote=True) + '"')
            require(data.encode() == (output/'disabled'/name).read_bytes(), 'stable mode changed more than approved hrefs')
    ledger = {name.lower(): {**symbols[name], 'identity':name,
                           **proposal['types'][name.lower()]} for name in names}
    # Profiles/source hashes in the historical proposal are not silently treated
    # as current publisher proof: read exact current native profiles independently.
    from ada_gnatdoc_enhancer.qualification import identities
    publisher = json.loads((authority/'qualified.json').read_text())
    native_profiles = identities(authority/publisher['native'])
    for item in ledger.values():
        page, anchor = item['native'].rsplit('/',1)[-1].split('#')
        entries = native_profiles['api/'+page]
        index = [i for i, x in enumerate(entries['declarations']) if x[0] == anchor]
        require(len(index) == 1, 'nonunique pilot native declaration')
        item['native_snippet'] = entries['signatures'][index[0]]
        item['native_anchor'] = anchor
    (output/'browser-oracle.json').write_text(sorted_json(dict(types=ledger, occurrences=occurrences['stable'],
        publication_sha256=publisher['publication_sha256'], publisher_base=publisher['base_url'].removesuffix('api/'))))
    report = dict(status='pass', source_revision=args.consumer_revision, consumer_modified=False,
                  migration_approved=False, official_default_byte_identical=True,
                  only_approved_href_and_integrity_changes=True, deterministic=True, byte_idempotent=True,
                  native_sha256=hashes(args.native), source_sha256=hashes(authority/'qualification-public'),
                  results=results, outputs=outputs)
    (output/'qualification.json').write_text(sorted_json(report))
    (output/'occurrences.json').write_text(sorted_json(occurrences))
    print(sorted_json({k:v for k,v in report.items() if k not in ('results','outputs')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('consumer', 'authority', 'native', 'official-python', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--consumer-revision', required=True)
    qualify(parser.parse_args())