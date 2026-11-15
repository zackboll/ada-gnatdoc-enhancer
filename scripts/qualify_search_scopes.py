#!/usr/bin/env python3
"""Independent flat-with-instances MEL oracle and complete search qualification.

Read-only consumer inputs; generates disposable sites, never a publication.
The oracle deliberately does not call public_declarations/packages/destinations.
It accepts only independently checked flat specs with package instantiations or
renamings, the shape of the MEL reproduction. Other shapes require another
oracle rather than trusting the implementation under test.
"""
from __future__ import annotations

import argparse
from collections import Counter
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import threading

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import HEADER, TYPE, SUBPROGRAM, mask_ada, last_semicolon
from ada_gnatdoc_enhancer.native_html import HEADING, SECTION
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.profiles import reconcile
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.search import INDEX
from ada_gnatdoc_enhancer.util import digest, require, sorted_json
import html


def oracle(root, native):
    pages = {}
    for path in sorted((native/'api').glob('*.html')):
        if path.name == 'index.html': continue
        raw = path.read_text()
        name, = HEADING.findall(raw)
        pages[html.unescape(name).lower()] = (path.name, [
            (html.unescape(m[3]), html.unescape(m[4]), m[1] or m[2]) for m in SECTION.finditer(raw)])
    result = []; excluded = []; inputs = {}
    for path in sorted((root/'ada/src').glob('*.ads')):
        raw = path.read_text(); masked = mask_ada(raw); h = HEADER.search(masked)
        if not h or h[1]: continue
        name = h[2]; inputs[path.relative_to(root).as_posix()] = digest(path.read_bytes())
        require(name.lower() in pages, 'oracle missing native package')
        page, sections = pages[name.lower()]
        public = masked[h.end():]
        # Independently constrain the reproduction to a flat declarative part.
        cut = re.search(r'(?im)^\s*private\s*$', public)
        if cut: public = public[:cut.start()]
        for m in re.finditer(r'\b(package|generic|task|protected|begin|declare)\b', public, re.I):
            require(m[1].lower() == 'package' and re.match(
                r'package\s+[\w.]+\s+(?:is\s+new|renames)\b', public[m.start():], re.I),
                'oracle does not support this source shape: ' + name)
        if 'internal' in name.lower().split('.'):
            excluded.append(dict(package=name, reason='Internal package component')); continue
        result.append(dict(kind='package', name=name, href=page, signature=''))
        callables = tuple(raw[h.end()+m.start():h.end()+last_semicolon(public, m.start())].strip()
                          for m in SUBPROGRAM.finditer(public))
        for pattern in (TYPE, SUBPROGRAM):
            for m in pattern.finditer(public):
                end = last_semicolon(public, m.start())
                signature = raw[h.end()+m.start():h.end()+end].strip()
                found = [s for s in sections if s[0].lower() == m[2].lower() and
                         reconcile(signature, s[1], callables) is not None]
                require(len(found) == 1, 'oracle ambiguous or missing native signature: ' + name + '.' + m[2])
                result.append(dict(kind='symbol' if m[1].lower() in ('type','subtype') else 'operation',
                    name=name+'.'+m[2], package=name, signature=signature,
                    line=raw.count('\n', 0, h.end()+m.start())+1,
                    source=path.relative_to(root).as_posix(), href=page+'#'+found[0][2]))
        eligible = {r['href'] for r in result}
        excluded.extend(dict(package=name, name=s[0], native_signature=s[1], href=page+'#'+s[2],
                             reason='outside supported direct public type/subprogram inventory')
                        for s in sections if page+'#'+s[2] not in eligible)
    require(len({r['href'] for r in result}) == len(result), 'oracle duplicate destinations')
    return result, excluded, inputs


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def browser(site, added, output):
    from playwright.sync_api import sync_playwright, expect
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    visited = []; queries = []; errors = []; external = []
    try:
        with sync_playwright() as p:
            options = dict(headless=True)
            if os.environ.get('CHROMIUM_PATH'): options['executable_path'] = os.environ['CHROMIUM_PATH']
            b = p.chromium.launch(**options)
            try:
                page = b.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: external.append(r.url) if not r.url.startswith(base+'/') else None)
                page.goto(base+'/api/index.html')
                expect(page.locator('#package-results')).to_contain_text('Search public API')
                for record in added:
                    page.locator('#package-search').fill(record['name'])
                    target = page.locator('#documentation-search-results').get_by_role(
                        'link', name=record['label'], exact=True)
                    target.click()
                    anchor = record['href'].split('#')[1]
                    expect(page.frame_locator('iframe').locator('[id="'+anchor+'"]')).to_be_visible()
                    visited.append(dict(name=record['name'], href=record['href'], url=page.url))
                for query in ('Navigation Report', 'Navigation_Report', 'Submit Navigation Report', 'Submit_Navigation_Report'):
                    page.locator('#package-search').fill(query)
                    expect(page.locator('#documentation-search-results a').first).to_be_visible()
                    queries.append(dict(query=query, results=page.locator('#documentation-search-results a').count()))
                page.screenshot(path=str(output/'mel-search.png'), full_page=True)
                context = b.new_context(java_script_enabled=False); native_page = context.new_page()
                native_page.goto(base+'/api/index.html')
                native_page.get_by_role('link', name='AMS.MEL.Status', exact=True).click()
                expect(native_page.frame_locator('iframe').get_by_role('heading',name='AMS.MEL.Status',exact=True)).to_be_visible()
                context.close()
            finally: b.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    require(not errors and not external, 'browser errors or external requests')
    return dict(status='passed', visited=visited, queries=queries, runtime_errors=errors,
                external_requests=external, javascript_disabled='passed')


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    expected, excluded, inputs = oracle(args.source_root, args.native)
    before = json.loads(args.before.read_text())
    if isinstance(before, dict): before = before['records']
    config = load(args.source_root, 'docs/gnatdoc-enhance.toml')
    for variant in ('first', 'second'):
        # MEL owns its portal/guides separately; this config enhances only API.
        site = args.output/variant
        shutil.copytree(args.native/'api', site/'api')
        enhance(config, site); verify(config, site)
    require(hashes(args.output/'first') == hashes(args.output/'second'), 'complete outputs differ')
    actual = json.loads((args.output/'first'/INDEX).read_text())['records']
    by_href = {r['href']:r for r in actual}
    require(len(by_href) == len(actual), 'duplicate emitted destination')
    require(set(by_href) == {r['href'] for r in expected}, 'complete eligible inventory mismatch')
    for record in expected:
        emitted = by_href[record['href']]
        require((emitted['name'], emitted['kind']) == (record['name'], record['kind']), 'wrong identity')
        if record['signature']:
            require(' '.join(record['signature'].split()) in emitted['text'], 'wrong signature text')
    old = {r['href']:r for r in before}
    added = [r for r in actual if r['href'] not in old]
    changed = [dict(before=old[r['href']], after=r) for r in actual if r['href'] in old and r != old[r['href']]]
    removed = [r for r in before if r['href'] not in by_href]
    require(not changed and not removed, 'existing records changed or removed')
    report = dict(status='passed', before=len(before), after=len(actual), added=len(added),
                  added_by_package=dict(Counter(r['name'].rsplit('.',1)[0] for r in added)),
                  changed=changed, removed=removed, eligible_inventory=expected,
                  excluded_native_sections=excluded, new_records=added, source_sha256=inputs,
                  native_sha256=hashes(args.native), output_sha256=hashes(args.output/'first'),
                  index_sha256=digest((args.output/'first'/INDEX).read_bytes()),
                  byte_reproducible=True)
    (args.output/'inventory.json').write_text(sorted_json(report))
    if args.browser:
        (args.output/'browser.json').write_text(sorted_json(browser(args.output/'first', added, args.output)))
    print(json.dumps({k:report[k] for k in ('status','before','after','added','added_by_package','byte_reproducible')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source-root', 'native', 'before', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--browser', action='store_true')
    run(parser.parse_args())