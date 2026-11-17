#!/usr/bin/env python3
"""Reconstruct official v0.1.6 and candidate on identical retained inputs.

The official wheel interpreter runs baseline; candidate runs independently.
Source browsing is never enabled in the unsupported predecessor release.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer import __version__
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import require, sorted_json

import qualify_release_014_015 as profiles
from compare_release_016_017 import compare


def run(repository, workspace, variant):
    require(__version__ == ('0.1.6' if variant == 'baseline' else '0.1.7'),
            'wrong installed baseline/candidate version')
    profiles.compare = compare
    reports = profiles.run(repository, workspace, variant)
    for name, fixture, filename, native, options in (
            ('mel-search', 'search-mel', 'docs/gnatdoc-enhance.toml', 'pristine', {}),
            ('core-resize', 'search-core', 'default.toml', 'pristine',
             dict(search=True, resizable_sidebar=True)),
            ('mel-source-blocks', 'source-block-fixtures/mel', 'docs/gnatdoc-authored-pilot.toml', 'native', {})):
        base = repository/'tests'/fixture if name == 'mel-source-blocks' else repository/'tests/real-fixtures'/fixture
        folder = workspace/variant/name
        authority = folder/'authority'; site = folder/'site'
        shutil.copytree(base/'authority' if name != 'mel-source-blocks' else repository/'tests/source-block-fixtures/mel', authority)
        shutil.copytree(base/native, site)
        config = replace(load(authority, filename), **options)
        require(not getattr(config, 'source_view', {}), 'predecessor source view must remain disabled')
        enhance(config, site); verify(config, site)
        first = hashes(site); enhance(config, site)
        require(first == hashes(site), 'publication is not idempotent')
        record = dict(output_sha256=first)
        if variant == 'candidate':
            record['comparison'] = compare(workspace/'baseline'/name/'site', site)
        if name == 'mel-search':
            from qualify_search_scopes import oracle
            expected, _, inputs = oracle(authority, base/'pristine')
            actual = json.loads((site/'api/gnatdoc-search-index.json').read_bytes())['records']
            by_href = {r['href']: r for r in actual}
            require(len(by_href) == len(actual) and set(by_href) == {r['href'] for r in expected},
                    'independent complete source/native inventory differs')
            before = json.loads((base/'before.json').read_bytes())
            if isinstance(before, dict): before = before['records']
            require(all(by_href.get(r['href']) == r for r in before), 'old search record changed')
            recovered = set(by_href) - {r['href'] for r in before}
            require(len(before) == 1143 and len(recovered) == 348,
                    'pinned recovered-declaration regression')
            for declaration in expected:
                emitted = by_href[declaration['href']]
                require((emitted['kind'], emitted['name']) == (declaration['kind'], declaration['name']),
                        'independent declaration identity differs')
                require(not declaration['signature'] or
                        ' '.join(declaration['signature'].split()) in emitted['text'],
                        'independent declaration signature differs')
            record.update(records=len(actual), recovered_declarations=len(recovered), source_sha256=inputs)
        reports[name] = record
    (workspace/(variant+'.json')).write_text(sorted_json(reports))
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repository', 'workspace'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    args = parser.parse_args()
    run(args.repository.resolve(), args.workspace.resolve(), args.variant)