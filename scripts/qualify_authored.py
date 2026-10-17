#!/usr/bin/env python3
"""Build GNATDOC-007 contracts from isolated pinned reference renderers.

Consumes GNATDOC-002 acquisition and GNATDOC-006 workspaces. It never writes
consumer repositories or deploys. Original renderer modules execute only here,
in qualification tooling, never in the shared production implementation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

from ada_gnatdoc_enhancer.authored import render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import (hashes, check_snapshot, bind_pristine,
                                               identities, preserve_native)
from ada_gnatdoc_enhancer.util import digest, require, sorted_json
from ada_gnatdoc_enhancer.validation import Page

REPO = Path(__file__).resolve().parents[1]
NAMES = ('core', 'imgproc', 'geometry', 'mel')


def original(root, filename):
    # Separate process per consumer avoids same-named consumer import caches.
    sys.path.insert(0, str(root/'scripts'))
    spec = importlib.util.spec_from_file_location('reference', root/'scripts'/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def contract(name, root, native_root):
    if name == 'mel':
        module = original(root, 'build_docs_portal.py')
        site_map = module.manifest(root)
        guides = [{**e, 'source': 'docs/' + e['path'], 'entry_points': []} for e in site_map['guides']]
        groups = [{'label': label, 'packages': [p for p in sorted(module.package_map(native_root, root))
                   if module.group(p) == label]} for label in module.GROUPS]
    else:
        module = original(root, 'render_gnatdoc_guides.py')
        guides = [{'id': identity, 'label': title, 'path': f'guides/{identity}.html',
                   'source': f'docs/{"" if name == "core" else "guides/"}{identity}.md',
                   'entry_points': [p if name == 'core' else p + '/1' for p in entries]}
                  for identity, (title, entries) in module.GUIDES.items()]
        groups = []
    examples = sorted(p.relative_to(root).as_posix() for p in (root/'docs/examples').glob('*.adb'))
    data = {'schema_version': 2, 'home': {'source': 'docs/index.html', 'path': 'index.html'},
            'stylesheet': {'source': 'docs/assets/' + ('portal.css' if name == 'mel' else 'gnatdoc-guides.css'),
                           'path': 'assets/portal.css' if name == 'mel' else 'guides/gnatdoc-guides.css'},
            'guides': guides, 'inputs': {}, 'native_sha256': hashes(native_root),
            'site_map': 'docs/site-map.json' if name == 'mel' else None,
            'anchors': 'docs/gnatdoc-native-anchors.json' if name == 'mel' else None,
            'groups': groups, 'examples': examples,
            'languages': ['ada', 'sh', 'shell', 'text', ''] if name == 'core' else ['ada', 'sh', 'text'],
            'source_links': {}, 'attribution_base': getattr(module, 'GITHUB', 'https://github.com/'),
            'title_suffix': 'OpenCV ' + name.title() + ' Ada',
            'api_label': 'GNATdoc API browser' if name == 'core' else 'API browser',
            'source_inventory': 'docs/guides' if name in ('imgproc', 'geometry') else None,
            'landing_example': 'docs/example.adb' if name != 'mel' else None,
            'ada_policy': 'exact-examples' if name in ('imgproc', 'geometry') else 'source-text',
            'example_project': 'docs/examples/examples.gpr' if examples else None,
            'landing_project': 'docs/example.gpr' if name != 'mel' else None,
            'directory_pages': ['index.html', 'guides/api-map.html'] if name == 'mel' else [],
            'renderer_exceptions': ['AMS.MEL.IR.Health_Status.Metadata.Status'] if name == 'mel' else []}
    if name == 'core':
        from markdown_it import MarkdownIt
        parser = MarkdownIt('commonmark')
        for entry in guides:
            for token in parser.parse((root/entry['source']).read_text()):
                for child in token.children or []:
                    if child.type != 'link_open': continue
                    link = child.attrGet('href')
                    if link.startswith(('https:', '#')) or link.split('#')[0] in {e['id']+'.md' for e in guides}:
                        continue
                    target = (root/'docs'/link.split('#')[0]).resolve()
                    relative = target.relative_to(root).as_posix()
                    data['source_links'][link] = {'source': relative,
                        'url': module.resolve_link(root, entry['id'], link, module.heading_inventory(root))}
    paths = {data['home']['source'], data['stylesheet']['source'], *examples,
             *(e['source'] for e in guides), *(v['source'] for v in data['source_links'].values())}
    paths.update(data[k] for k in ('site_map', 'anchors', 'landing_example', 'example_project', 'landing_project') if data[k])
    data['inputs'] = {p: digest((root/p).read_bytes()) for p in sorted(paths)}
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', choices=NAMES, required=True)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--acquisition', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); name = args.name
    root = args.sources/name; native_root = args.acquisition/name/'pristine'
    spec = json.loads((REPO/f'docs/evidence/gnatdoc002/{name}-input.json').read_text())
    check_snapshot(root, spec['source_sha256'])
    require(hashes(native_root) == spec['pristine_sha256'], 'native acquisition mismatch')
    data = contract(name, root, native_root)
    args.workspace.mkdir(parents=True, exist_ok=False); args.output.mkdir(parents=True, exist_ok=True)
    reports = []
    for copy in ('first', 'second'):
        destination = args.workspace/copy
        shutil.copytree(args.previous/name/'first', destination, ignore=shutil.ignore_patterns('_site'))
        # Qualification inputs come only from the pinned export, not prior docs.
        shutil.rmtree(destination/'docs'); shutil.copytree(root/'docs', destination/'docs')
        for path in data['inputs']:
            (destination/path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root/path, destination/path)
        shutil.copytree(native_root, destination/'_site')
        payload = sorted_json(data).encode(); (destination/'authored.json').write_bytes(payload)
        config_path = destination/'qualification.toml'
        text = config_path.read_text().replace('external_hosts = ["core.invalid"]',
                     'external_hosts = ["core.invalid", "github.com", "zackboll.github.io"]')
        if '[security]' not in text:
            text += '\n[security]\nexternal_hosts = ["github.com", "zackboll.github.io"]\n'
        text += f'\n[guides]\nmode = "authored-{"html" if name == "mel" else "markdown"}"\nmanifest = "authored.json"\nsha256 = "{digest(payload)}"\n'
        config_path.write_text(text)
        config = load(destination, 'qualification.toml'); native = snapshot(config, destination/'_site')
        expected = render(config, native)
        parity = []
        for entry in data['guides']:
            path = entry['path']; reference = (args.reference/name/path).read_bytes()
            require(expected[path] == reference, f'reference byte parity failed: {path}')
            parity.append({'id': entry['id'], 'label': entry['label'], 'path': path,
                           'classification': 'Equivalent and verified', 'byte_identical': True,
                           'sha256': digest(reference), 'fragments': Page(reference.decode()).ids,
                           'links': Page(reference.decode()).links})
        reports.append(enhance(config, destination/'_site'))
        before = hashes(destination/'_site'); verify(config, destination/'_site')
        enhance(config, destination/'_site'); require(before == hashes(destination/'_site'), 'not byte-idempotent')
        bind_pristine(native_root, destination/'_site')
        preservation = preserve_native(identities(native_root), destination/'_site',
                                       config=config, pristine=native_root)
    require(hashes(args.workspace/'first/_site') == hashes(args.workspace/'second/_site'), 'not deterministic')
    record = {'revision': spec['revision'], 'contract': data, 'parity': parity, 'publication': reports[0],
              'deterministic': True, 'byte_idempotent': True, 'independent_reconstruction': True,
              'native_preservation': preservation,
              'output_sha256': hashes(args.workspace/'first/_site')}
    (args.output/f'{name}-report.json').write_text(sorted_json(record))
    (args.output/f'{name}-authored.json').write_text(sorted_json(data))
    print(name, 'PASS', flush=True)


if __name__ == '__main__': main()