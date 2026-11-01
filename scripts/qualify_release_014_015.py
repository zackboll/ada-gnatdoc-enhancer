#!/usr/bin/env python3
"""Reconstruct pinned consumers against official v0.1.4, verification disabled.

Run once with the official wheel and --variant baseline, then with this source
and --variant candidate. No consumer checkout is changed. The Core search
fixture is the full 195-package native site, not a fabricated declaration site.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import sorted_json

from compare_release_014_015 import compare


def run(repository, workspace, variant):
    reports = {}
    for name in ('core', 'imgproc', 'geometry', 'mel', 'core-search'):
        folder = workspace/variant/name
        fixture = repository/('tests/real-fixtures/search-core' if name == 'core-search' else 'tests/authored-fixtures/' + name)
        authority = folder/'authority'; site = folder/'site'
        if name == 'core-search':
            shutil.copytree(fixture/'authority', authority)
            shutil.copytree(fixture/'pristine', site)
            text = (authority/'default.toml').read_text() + '\n[search]\nschema_version = 1\nmode = "documentation"\n'
            (authority/'example.toml').write_text(text)
            config = load(authority, 'example.toml')
        else:
            shutil.copytree(fixture, authority)
            shutil.copytree(fixture/'native', site)
            config = load(authority, 'project.toml')
        report = enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); assert before == hashes(site)
        record = dict(disabled=report, disabled_hashes=before)
        if variant == 'candidate':
            baseline = workspace/'baseline'/name/'site'
            record['release_comparison'] = compare(baseline, site)
            record['official_disabled_byte_parity'] = True
        if name != 'mel':
            enabled = folder/'enabled'
            shutil.copytree(fixture/('pristine' if name == 'core-search' else 'native'), enabled)
            if name == 'core-search':
                # Reload to bind the actual opt-in config to custom-theme identity.
                text = text.replace('[guides]', '[guides]\nada_example_highlighting = true\nada_example_api_links = true\nada_landing_example_highlighting = true')
                (authority/'enabled.toml').write_text(text)
                opted = load(authority, 'enabled.toml')
            else:
                opted = replace(config, ada_example_highlighting=True, ada_example_api_links=True,
                                ada_landing_example_highlighting=True)
            record['enabled'] = enhance(opted, enabled); verify(opted, enabled)
            after = hashes(enabled); enhance(opted, enabled); assert after == hashes(enabled)
            record['changed_files'] = sorted(p for p in before if before[p] != after[p])
            record['added_files'] = sorted(set(after) - set(before))
            assert record['added_files'] == ['assets/gnatdoc-examples.css']
            assert all(p == 'index.html' or p == 'api/presentation.json' or p.startswith('guides/')
                       for p in record['changed_files'])
            if variant == 'candidate':
                record['existing_examples_comparison'] = compare(
                    workspace/'baseline'/name/'enabled', enabled)
            if name == 'core-search' and variant == 'candidate':
                search = json.loads((enabled/'api/gnatdoc-search-index.json').read_text())
                baseline_search = json.loads((baseline/'api/gnatdoc-search-index.json').read_text())
                assert search == baseline_search
                assert len(search['records']) == 1462  # Pinned official fixture; see test_search.py.
                record['search_records'] = len(search['records'])
                record['baseline_kind'] = 'historical 1462-record fixture with official v0.1.4, not current production Core'
            record['enabled_hashes'] = after
        if name == 'core':
            record['navigation_profiles'] = {}
            for profile, options in (
                    ('none', dict(navigation='none')),
                    ('symbol', dict(symbol_bookmarks=True, default_package='OpenCV.Core')),
                    ('no-theme', dict(theme=False))):
                output = folder/profile
                shutil.copytree(fixture/'native', output)
                profiled = replace(config, **options)
                enhance(profiled, output); verify(profiled, output)
                record['navigation_profiles'][profile] = (
                    compare(workspace/'baseline'/name/profile, output)
                    if variant == 'candidate' else dict(files=len(hashes(output))))
        reports[name] = record
    # Use the existing qualified fixture for each profile. Authored Core's
    # generic native sections are not a complete operation inventory and its
    # configuration does not authorize incoming-instance references.
    for name, fixture, config_name, native_name, options in (
            ('operations', 'tests/fixtures/imgproc', 'project.toml', '_site', {}),
            ('incoming-instance', 'tests/real-fixtures/generic-core', 'enhancer.toml', 'pristine',
             dict(instance_references=True, symbol_bookmarks=True, default_package='OpenCV.Core'))):
        folder = workspace/variant/name
        authority = folder/'authority'; site = folder/'site'
        shutil.copytree(repository/fixture, authority)
        shutil.copytree(authority/native_name, site)
        config = replace(load(authority, config_name), **options)
        report = enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); assert before == hashes(site)
        reports[name] = dict(disabled=report, disabled_hashes=before)
        if variant == 'candidate':
            reports[name]['release_comparison'] = compare(workspace/'baseline'/name/'site', site)
    (workspace/(variant + '.json')).write_text(sorted_json(reports))
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    args = parser.parse_args()
    run(args.repository.resolve(), args.workspace.resolve(), args.variant)