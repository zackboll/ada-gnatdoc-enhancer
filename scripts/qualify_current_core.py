#!/usr/bin/env python3
"""Qualify the actual 1,487-record Core inventory in disposable copies only.

Source commit is supplied independently; native bytes must match its approved
authored manifest. This reuses a pinned acquisition, not a fresh GNATdoc build.
"""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.destinations import source_destinations
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import sorted_json

from compare_release_013_014 import compare


def run(repository, commit, native, workspace, official_python):
    def git(*words):
        return subprocess.check_output(['git', '-C', str(repository), *words])

    assert git('rev-parse', commit+'^{commit}').decode().strip() == commit
    tree = git('rev-parse', commit+'^{tree}').decode().strip()
    workspace.mkdir(parents=True, exist_ok=False)
    authority = workspace/'authority'; authority.mkdir()
    # Inspect all members before extracting even a trusted, pinned Git archive.
    with tarfile.open(fileobj=io.BytesIO(git('archive', commit))) as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            assert member.isdir() or member.isfile(), member.name
        for member in archive.getmembers():
            path = authority/member.name
            if member.isdir():path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(archive.extractfile(member).read())
    authored = json.loads((authority/'docs/enhancer-qualification/gnatdoc-authored.json').read_text())
    assert hashes(native) == authored['native_sha256'], 'unqualified native acquisition'
    # Mirror the pinned consumer's stage_gnatdoc_sources.py public-only boundary.
    # Its recursive scanner input excludes the separate src/internal project;
    # keep every public src/*.ads path/byte unchanged for qualification hashes.
    shutil.rmtree(authority/'src/internal')
    config_name = 'docs/gnatdoc-enhancer.toml'
    config = load(authority, config_name)
    original = snapshot(config, native)
    destinations = source_destinations(config, original, packages(config))
    expected_destinations = {(package.name+'.'+d.declaration.name, d.href)
                             for key, package in packages(config).items()
                             for d in destinations[key]}
    site = workspace/'candidate'; shutil.copytree(native, site)
    report = enhance(config, site); verify(config, site)
    before = hashes(site); enhance(config, site); assert before == hashes(site)
    second = workspace/'second'; shutil.copytree(native, second)
    enhance(config, second); assert before == hashes(second)
    baseline = workspace/'baseline'
    subprocess.run([str(official_python), '-c',
        'from pathlib import Path; import shutil,sys; '
        'from ada_gnatdoc_enhancer.config import load; '
        'from ada_gnatdoc_enhancer.pipeline import enhance,verify; '
        'root,name,raw,site=sys.argv[1:]; shutil.copytree(raw,site); '
        'c=load(Path(root),name); enhance(c,Path(site)); verify(c,Path(site))',
        str(authority), config_name, str(native), str(baseline)], cwd=workspace, check=True)
    comparison = compare(baseline, site)
    index_path = 'api/gnatdoc-search-index.json'
    index = json.loads((site/index_path).read_text())
    counts = dict(Counter(r['kind'] for r in index['records']))
    assert counts == dict(package=195, symbol=216, operation=1071, guide=5), counts
    assert len(index['records']) == 1487
    for record in index['records']:
        if record['kind'] in ('symbol', 'operation'):
            assert (record['name'], record['href']) in expected_destinations
    assert (site/index_path).read_bytes() == (baseline/index_path).read_bytes()
    text = (authority/config_name).read_text().replace('[guides]', '[guides]\n'
        'ada_example_highlighting = true\nada_example_api_links = true\n'
        'ada_landing_example_highlighting = true')
    enabled_config = authority/'docs/enabled.toml'; enabled_config.write_text(text)
    opted = load(authority, 'docs/enabled.toml')
    enabled = workspace/'enabled'; shutil.copytree(native, enabled)
    enabled_report = enhance(opted, enabled); verify(opted, enabled)
    after = hashes(enabled); enhance(opted, enabled); assert after == hashes(enabled)
    assert (enabled/index_path).read_bytes() == (site/index_path).read_bytes()
    added = sorted(set(after)-set(before)); removed = sorted(set(before)-set(after))
    changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
    assert added == ['assets/gnatdoc-examples.css'] and not removed
    assert all(p in ('index.html', 'api/presentation.json') or p.startswith('guides/') for p in changed)
    result = dict(source_commit=commit, source_tree=tree,
                  acquisition='existing approved native bytes, not fresh compiler/GNATdoc generation',
                  source_staging='pinned consumer public src/*.ads; excludes separate src/internal project',
                  native_sha256=hashes(native), publication=report, enabled_publication=enabled_report,
                  counts=counts, search_records=1487, source_native_destinations_verified=True,
                  search_index_bytes_preserved=True, comparison=comparison,
                  deterministic=True, idempotent=True, added_files=added, changed_files=changed,
                  publication_sha256=before, enabled_sha256=after)
    (workspace/'results.json').write_text(sorted_json(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repository', 'native', 'workspace', 'official-python'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    run(args.repository, args.commit, args.native, args.workspace, args.official_python)