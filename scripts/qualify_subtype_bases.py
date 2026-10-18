#!/usr/bin/env python3
"""Audit subtype-only deltas on pinned real sites; never write consumer inputs.

The previous workspace is evidence to revalidate, not an input authority.
Native/source hashes come from unchanged historical acquisition records.
Geometry's new dependency allowlist is explicitly reviewed here: Point_Array.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import html
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.external_types import destinations, inventory
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.profiles import reconcile
from ada_gnatdoc_enhancer.qualification import hashes, identities, preserve_native
from ada_gnatdoc_enhancer.syntax import TYPE_LINK, highlighted
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

REPO = Path(__file__).resolve().parents[1]
GEOMETRY_PR = '12e6b8549dd1859aab1526be9bf778e0da60d7f0'
GEOMETRY_BASE = '8690927853ffa74729206d8997b09046ad3d2246'
CORE = 'f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'
SECTIONS = re.compile(r'<h4 id=([^ >]+)>([^<]+)</h4>'
                      r'<pre class=ada-code-snippet><code>(.*?)</code></pre>', re.S)


def write(path, data):
    path.write_text(sorted_json(data))


class Occurrences(HTMLParser):
    """Decoded token offsets, independent of the production matcher/resolver."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.text = ''
        self.links = []
        self.active = None
        self.feed(raw)
        self.close()
        require(self.active is None, 'unclosed reference')

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            require(attrs.get('class') == 'type-reference', 'unexpected snippet link')
            self.active = {'offset': len(self.text), 'identity': attrs['data-type'].lower(),
                           'href': html.unescape(attrs['href'])}

    def handle_data(self, text):
        self.text += text

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            self.active['end'] = len(self.text)
            self.links.append(self.active)
            self.active = None


def occurrence_map(text):
    return {m[1]: (m[2], Occurrences(m[3])) for m in SECTIONS.finditer(text)}


def audit(old, new, config, pristine):
    """Every addition must own a real subtype base and real type destination."""
    source = packages(config)
    native = snapshot(config, pristine)
    external = destinations(config)
    local = {}
    for key, pkg in source.items():
        for name, decl in pkg.public_types.items():
            matches = [s for s in native.pages[key].sections
                       if s.name.lower() == name and reconcile(decl.signature, s.code)]
            require(len(matches) == 1, 'type owner/profile not uniquely native')
            local[key + '.' + name] = (native.pages[key].path.name, matches[0], decl)
    additions = []
    old_hashes, new_hashes = hashes(old), hashes(new)
    require(set(old_hashes) == set(new_hashes), 'published file inventory changed')
    changed = []
    for name in old_hashes:
        if old_hashes[name] == new_hashes[name]:
            continue
        changed.append(name)
        if name == 'api/presentation.json':
            continue
        require(name.startswith('api/') and name.endswith('.html') and
                name != 'api/index.html', f'unrelated output changed: {name}')
        before, after = (old/name).read_text(), (new/name).read_text()
        owners = [p for p in native.pages.values() if p.path.name == Path(name).name]
        require(len(owners) == 1, 'changed file is not a native package')
        page = owners[0]
        pkg = source[page.package.lower()]
        previous, current = occurrence_map(before), occurrence_map(after)
        require(set(previous) == set(current), 'declaration anchor changed')
        remove = set()
        for anchor, (label, snippet) in current.items():
            old_snippet = previous[anchor][1]
            require(snippet.text == old_snippet.text, 'native declaration text changed')
            old_links = {(x['offset'], x['end']): x for x in old_snippet.links}
            new_links = {(x['offset'], x['end']): x for x in snippet.links}
            require(all(new_links.get(pos) == val for pos, val in old_links.items()),
                    'old source-backed reference disappeared or changed')
            for pos in new_links.keys() - old_links.keys():
                link = new_links[pos]
                # Independent explicit syntax assertion, not production TYPE_MARK.
                base = re.match(r'^\s*subtype\s+\w+\s+is\s+([\w.]+)', snippet.text, re.I)
                require(base and base.span(1) == pos, 'new link outside ordinary subtype base')
                declarations = [d for d in pkg.declarations if d.name == label and
                                reconcile(d.signature, snippet.text)]
                require(len(declarations) == 1, 'subtype lacks unique source declaration')
                identity = link['identity']
                if identity in local:
                    dest_page, section, decl = local[identity]
                    require(link['href'] == dest_page + '#' + section.anchor,
                            'wrong local source/native type destination')
                    proof = {'package': identity.rpartition('.')[0], 'page': dest_page,
                             'anchor': section.anchor, 'source_profile': decl.signature,
                             'native_profile': section.code}
                else:
                    require(identity in external and link['href'] == external[identity],
                            'unapproved external type destination')
                    dep = next(d for d in config.dependencies if any(
                        t.lower() == identity for t in d['types']))
                    manifest = json.loads((config.root/dep['manifest']).read_text())
                    proof = manifest['types'][identity]
                additions.append({'package': page.package, 'declaration': label,
                                  'source_profile': declarations[0].signature,
                                  'native_anchor': anchor, **link, 'destination_proof': proof})
                remove.add((anchor, link['href'], identity))
        def strip_added(section):
            anchor = section[1]
            # Previously unlinked qualified marks had lexical coloring of dots.
            # Restore that existing coloring when removing only the new link.
            code = TYPE_LINK.sub(lambda m: highlighted(m[3]) if
                (anchor, html.unescape(m[1]), m[2]) in remove else m[0], section[3])
            return section[0].replace(section[3], code, 1)
        require(SECTIONS.sub(strip_added, after) == before,
                'non-link native bytes changed')
    return {'added_occurrences': additions, 'removed_occurrences': [], 'changed_files': changed,
            'unaffected_bytes_preserved': True}


def geometry_ledger(consumer, site, output):
    """Re-use PR #48's unchanged independent parsers and original source matcher."""
    relative = 'scripts/investigate_shared_gnatdoc_types.py'
    expected = subprocess.check_output(['git', '-C', str(consumer), 'show', GEOMETRY_PR+':'+relative])
    require((consumer/relative).read_bytes() == expected, 'consumer comparator modified')
    module_spec = importlib.util.spec_from_file_location('geometry009_oracle', consumer/relative)
    oracle = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(oracle)
    rows = json.loads((consumer/'docs/evidence/gnatdoc009/type-link-occurrences.json').read_text())
    require(digest((consumer/'docs/evidence/gnatdoc009/type-link-occurrences.json').read_bytes()) ==
            '944c44d8147a53f4508db28c7c204c2a03989a748de33b9c8c48f34566ddab93',
            'original occurrence authority changed')
    require(Counter(r['classification'] for r in rows) == {
        'equivalent-verified-native-destination': 262, 'shared-only-reference': 4,
        'BLOCKED-source-backed-reference-lost': 1}, 'old blocked ledger changed')
    actual = oracle.sections(site)
    for row in rows:
        snippet = actual[(row['package'], row['native_anchor'])][2]
        links = [x for x in snippet.links if (x['offset'], x['end']) == (row['offset'], row['end'])]
        require(len(links) == 1 and links[0]['identity'] == row['referenced_type'],
                'missing or changed source-backed Geometry reference')
        row['shared'] = links[0]
        row['classification'] = ('equivalent-verified-native-destination' if row['legacy']
                                 else 'shared-only-reference')
    require(Counter(r['classification'] for r in rows) == {
        'equivalent-verified-native-destination': 263, 'shared-only-reference': 4},
        'corrected 263/4/0 ledger mismatch')
    sys.path.insert(0, str(consumer/'scripts'))
    from enhance_gnatdoc_navigation import entries
    expected_nav = entries(output/'geometry-pristine/api', consumer/'src', consumer/'docs/api-categories.json')
    expected_entries = [[category, item['href'], item['name'] +
                        (f' ({item["overload"]})' if item['overload'] else '')]
                        for _, _, groups in expected_nav for category, _, items in groups for item in items]
    require(oracle.Navigation((site/'api/index.html').read_text()).entries == expected_entries,
            'unchanged two-package navigation oracle failed')
    write(output/'geometry-occurrences.json', rows)
    return {'equivalent': 263, 'shared_only': 4, 'missing': 0, 'navigation': 130}


def run(args):
    require(not args.workspace.exists(), 'workspace must be new')
    args.workspace.mkdir(parents=True)
    result = {}
    for name in ('core', 'imgproc', 'geometry', 'mel'):
        previous = args.previous/name/'first'
        spec = json.loads((REPO/f'docs/evidence/gnatdoc002/{name}-input.json').read_text())
        pristine = args.previous/name/'pristine'
        require(hashes(pristine) == spec['pristine_sha256'], 'historical native hashes changed')
        config = load(previous, 'qualification.toml')
        for pkg in packages(config).values():
            relative = pkg.path.relative_to(previous/'qualification-public').as_posix()
            require(digest(pkg.path.read_bytes()) == spec['source_sha256'][relative], 'historical source changed')
        # Old output is checked by the actual baseline installed CLI, not trusted metadata.
        subprocess.run([args.baseline_python, '-m', 'ada_gnatdoc_enhancer', 'verify',
                        '--source-root', str(previous), '--config', 'qualification.toml',
                        '--site', str(previous/'_site')], check=True,
                       env={k:v for k,v in os.environ.items() if k != 'PYTHONPATH'})
        copies = []
        for ordinal in ('first', 'second'):
            root = args.workspace/name/ordinal
            shutil.copytree(previous, root, ignore=shutil.ignore_patterns('_site', '__pycache__'))
            shutil.copytree(pristine, root/'_site')
            config = load(root, 'qualification.toml')
            before = hashes(root/'_site')
            enhance(config, root/'_site', dry_run=True)
            require(hashes(root/'_site') == before, 'dry-run mutated native')
            publication = enhance(config, root/'_site')
            verify(config, root/'_site')
            state = hashes(root/'_site')
            enhance(config, root/'_site')
            require(hashes(root/'_site') == state, 'not byte-idempotent')
            preserved = preserve_native(identities(pristine), root/'_site', config=config, pristine=pristine)
            copies.append(root/'_site')
        require(hashes(copies[0]) == hashes(copies[1]), 'nondeterministic output')
        require(preserved['declarations'] == {'core':1268,'imgproc':314,'geometry':130,'mel':1237}[name],
                'native section count changed')
        result[name] = {'publication': publication, 'native_preservation': preserved,
                        'deterministic': True, 'byte_idempotent': True,
                        **audit(previous/'_site', copies[0], config, pristine)}
        write(args.workspace/'four-site.json', result)
        print(name, 'PASS', len(result[name]['added_occurrences']), flush=True)
    # Current Geometry source and reviewed PR #48 bundle, not the older four-site export.
    root = args.workspace/'geometry-current'
    shutil.copytree(args.geometry_inputs, root)
    pristine = args.geometry_pristine
    shutil.copytree(pristine, args.workspace/'geometry-pristine')
    config = load(root, 'qualification.toml')
    original_report = args.consumer/'docs/evidence/gnatdoc009/report.json'
    require(digest(original_report.read_bytes()) ==
            '135204cc2702dcef99076f2350a290d5bfab908c09bb38818d367ad3b210ab28',
            'Geometry acquisition authority changed')
    original = json.loads(original_report.read_text())
    require(hashes(pristine) == original['pristine_sha256'] and
            hashes(args.geometry_baseline) == original['shadow_sha256'] and
            digest((root/'qualification.toml').read_bytes()) == original['configuration_sha256'],
            'Geometry acquisition/configuration substitution')
    require('OpenCV.Point_Array' in config.dependencies[0]['types'], 'Point_Array not explicitly reviewed')
    for pkg in packages(config).values():
        relative = pkg.path.relative_to(root/'qualification-public').as_posix()
        expected = subprocess.check_output(['git','-C',str(args.consumer),'show',GEOMETRY_BASE+':'+relative])
        require(pkg.path.read_bytes() == expected, 'current Geometry source substitution')
    sites = []
    for ordinal in ('first', 'second'):
        site = root/ordinal
        shutil.copytree(pristine, site)
        before = hashes(site)
        enhance(config, site, dry_run=True)
        require(before == hashes(site), 'Geometry dry-run mutated')
        report = enhance(config, site)
        verify(config, site)
        state = hashes(site)
        enhance(config, site)
        require(state == hashes(site), 'Geometry not idempotent')
        preserve_native(identities(pristine), site)
        sites.append(site)
    require(hashes(sites[0]) == hashes(sites[1]), 'Geometry nondeterministic')
    require((report['linked_local_types'], report['linked_external_types']) == (171,96), 'Geometry counts')
    ledger = geometry_ledger(args.consumer, sites[0], args.workspace)
    changes = audit(args.geometry_baseline, sites[0], config, pristine)
    require(len(changes['added_occurrences']) == 1, 'unexpected current Geometry changes')
    result['geometry_current'] = {'publication': report, 'ledger': ledger, **changes,
                                  'site_sha256': hashes(sites[0]), 'core_publication': 'offline-test'}
    write(args.workspace/'four-site.json', result)
    print('current Geometry PASS 263/4/0', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('previous','workspace','consumer','geometry-inputs','geometry-pristine','geometry-baseline'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--baseline-python', required=True)
    run(parser.parse_args())