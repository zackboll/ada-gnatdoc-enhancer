#!/usr/bin/env python3
"""Reconstruct official v0.1.5 and candidate publications on identical inputs.

Run baseline with the independently hash-verified official wheel interpreter,
then candidate with v0.1.6. No consumer checkout is edited. Schema-3 is qualified
separately against its independent nine-output oracle, not against v0.1.5.
"""
import argparse
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer import __version__
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import require, sorted_json

import qualify_release_014_015 as profiles
from compare_release_015_016 import compare


def run(repository, workspace, variant):
    require(__version__ == ('0.1.5' if variant == 'baseline' else '0.1.6'),
            'wrong installed baseline/candidate version')
    # Reuse all established navigation/theme/guide/lexical-example profiles,
    # without editing the historical 014/015 comparator or historical tests.
    profiles.compare = compare
    reports = profiles.run(repository, workspace, variant)
    fixture = repository / 'tests/real-fixtures/search-mel'
    folder = workspace / variant / 'mel-search'
    authority = folder / 'authority'
    site = folder / 'site'
    shutil.copytree(fixture / 'authority', authority)
    shutil.copytree(fixture / 'pristine/api', site / 'api')
    config = load(authority, 'docs/gnatdoc-enhance.toml')
    enhance(config, site)
    verify(config, site)
    first = hashes(site)
    enhance(config, site)
    require(first == hashes(site), 'MEL publication is not idempotent')
    record = dict(output_sha256=first)
    if variant == 'baseline':
        actual = json.loads((site / 'api/gnatdoc-search-index.json').read_bytes())['records']
        retained = json.loads((fixture / 'before.json').read_bytes())
        if isinstance(retained, dict):
            retained = retained['records']
        require(actual == retained, 'official release differs from retained old-record evidence')
    else:
        from qualify_search_scopes import oracle
        expected, excluded, inputs = oracle(authority, fixture / 'pristine')
        baseline = workspace / 'baseline/mel-search/site'
        record['comparison'] = compare(baseline, site, config=config)
        actual = json.loads((site / 'api/gnatdoc-search-index.json').read_bytes())['records']
        by_href = {r['href']: r for r in actual}
        require(len(by_href) == len(actual) and set(by_href) == {r['href'] for r in expected},
                'independent complete source/native inventory differs')
        for declaration in expected:
            emitted = by_href[declaration['href']]
            require((emitted['kind'], emitted['name']) == (declaration['kind'], declaration['name']),
                    'independent declaration identity differs')
            require(not declaration['signature'] or
                    ' '.join(declaration['signature'].split()) in emitted['text'],
                    'independent declaration signature differs')
        record.update(source_sha256=inputs, excluded_native_sections=excluded,
                      eligible_inventory=expected, records=len(actual))
    reports['mel-search'] = record
    (workspace / (variant + '.json')).write_text(sorted_json(reports))
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repository', 'workspace'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    args = parser.parse_args()
    run(args.repository.resolve(), args.workspace.resolve(), args.variant)