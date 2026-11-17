#!/usr/bin/env python3
"""Complete retained GNATdoc 26 MEL/Core source publications and Chromium gates.

No consumer changes or fresh compiler/GNATdoc acquisition. --baseline-source
must name an independently checked-out starting implementation for byte parity.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import functools
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading

from ada_gnatdoc_enhancer import __version__
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.inventory import packages
from ada_gnatdoc_enhancer.inventory import mask_ada
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json


class SourceText(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.in_code = False; self.text = ''; self.anchors = []
        self.feed(value)

    def handle_starttag(self, tag, attrs):
        if tag == 'code': self.in_code = True
        if tag == 'span': self.anchors.append(dict(attrs)['id'])

    def handle_endtag(self, tag):
        if tag == 'code': self.in_code = False

    def handle_data(self, data):
        if self.in_code: self.text += data


def prepare(repository, workspace, baseline, baseline_python=None):
    inventory = {}
    for name, filename in (('mel', 'docs/gnatdoc-enhance.toml'), ('core', 'default.toml')):
        print('Qualifying '+name, flush=True)
        fixture = repository/'tests/real-fixtures'/('search-' + name)
        provenance = json.loads((fixture/'provenance.json').read_text())
        for path, sha in provenance['files'].items():
            require(digest((fixture/path).read_bytes()) == sha, 'retained official fixture fingerprint mismatch')
        root = workspace/(name+'-authority'); shutil.copytree(fixture/'authority', root)
        config = load(root, filename)
        disabled = workspace/(name+'-disabled'); shutil.copytree(fixture/'pristine', disabled)
        enhance(config, disabled); verify(config, disabled)
        parity = None
        if baseline or baseline_python:
            old = workspace/(name+'-baseline'); shutil.copytree(fixture/'pristine', old)
            code = ('from pathlib import Path; from ada_gnatdoc_enhancer.config import load; '
                    'from ada_gnatdoc_enhancer.pipeline import enhance; '
                    f'enhance(load(Path({str(root)!r}), {filename!r}), Path({str(old)!r}))')
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            if baseline:
                env['PYTHONPATH'] = str(baseline/'src')
            subprocess.run([str(baseline_python or os.sys.executable), '-c', code],
                           cwd=workspace, env=env, check=True)
            if baseline_python:
                from compare_release_016_017 import compare
                require(__version__ == '0.1.7', 'wrong candidate source-view version')
                parity = compare(old, disabled)
            else:
                require(hashes(old) == hashes(disabled), 'complete disabled output byte parity failed')
                parity = hashes(disabled)
        evidence = dict(schema_version=1, files={n: d for n, d in hashes(fixture/'pristine').items()
                        if n.endswith('.html') or n == 'api/gnatdoc.css'}, sources={
                        p.path.relative_to(root).as_posix(): digest(p.path.read_bytes())
                        for p in packages(config).values()})
        raw = sorted_json(evidence).encode(); (root/'source-native.json').write_bytes(raw)
        options = dict(schema_version=1, mode='public-specifications', native_manifest='source-native.json',
                       native_manifest_sha256=digest(raw))
        # Keep the existing custom-theme config identity unchanged. This
        # qualification uses the same validated contract as the TOML loader.
        config = replace(config, source_view=options, search=True, resizable_sidebar=True)
        site = workspace/name; shutil.copytree(fixture/'pristine', site)
        stats = enhance(config, site); verify(config, site)
        original = hashes(site); enhance(config, site)
        require(hashes(site) == original, 'source-view idempotence failed')
        second = workspace/(name+'-second'); shutil.copytree(fixture/'pristine', second)
        enhance(config, second); require(hashes(second) == original, 'source-view determinism failed')
        data = json.loads((site/'api/presentation.json').read_text())['source_view']
        source_packages = packages(config)
        # Independently retained/flat-source oracles do not call the destination
        # collector or boundary walker used by the implementation under test.
        actual = {}
        for record in data['files']:
            page_name = next(p.name for p in (site/'api').glob('*.html')
                             if '<h1>'+record['package']+'</h1>' in p.read_text())
            for entry in record['declarations']:
                if entry['anchor']:
                    actual[page_name+'#'+entry['anchor']] = entry
        if name == 'core':
            oracle = json.loads((fixture/'oracle.json').read_text())
            for entry in oracle:
                require(entry['href'] in actual, 'retained Core oracle source link missing')
                observed = actual[entry['href']]
                signature = entry['source_profile']
                import re
                token = re.search(r'\S', mask_ada(signature))
                record = next(f for f in data['files'] if f['package'] == entry['package'])
                raw_source = (root/record['source']).read_text()
                require(raw_source.count(signature) == 1, 'Core oracle full source profile not unique')
                expected_line = raw_source.count('\n', 0, raw_source.index(signature) + token.start()) + 1
                require(observed['name'] == entry['package']+'.'+entry['name'] and
                        observed['line'] == expected_line, 'Core oracle identity/line mismatch')
        else:
            from qualify_search_scopes import oracle as mel_oracle
            oracle, _, _ = mel_oracle(root, fixture/'pristine')
            for entry in oracle:
                if entry['kind'] == 'package': continue
                require(entry['href'] in actual, 'independent MEL oracle source link missing')
                observed = actual[entry['href']]
                import re
                signature = entry['signature']
                token = re.search(r'\S', mask_ada(signature))
                original_source = (root/entry['source']).read_text()
                require(original_source.count(signature) == 1, 'MEL oracle full source profile not unique')
                expected_line = original_source.count('\n', 0, original_source.index(signature) + token.start()) + 1
                require(observed['name'] == entry['name'] and observed['line'] == expected_line,
                        'MEL independent oracle identity/line mismatch')
        for record in data['files']:
            raw_source = (root/record['source']).read_bytes()
            parsed = SourceText((site/record['page']).read_text())
            require(parsed.text.encode('utf-8') == raw_source, 'source-page text byte identity failed')
            require(parsed.anchors == ['L'+str(i) for i in range(1, record['lines']+1)],
                    'source-page complete ordered line anchors failed')
            # Validate each recorded line against the already source-bound
            # signature slice, not by searching for a declaration name.
            pkg = source_packages[record['package'].lower()]
            for entry in record['declarations']:
                if entry['kind'] == 'package': continue
                candidates = [d for d in pkg.declarations if d.kind == entry['kind'] and
                              pkg.name+'.'+d.name == entry['name'] and d.source_line == entry['line']]
                if entry['kind'] == 'constant': continue  # Existing narrow destination extension.
                require(len(candidates) == 1, 'declaration-to-source record is not unique')
                declaration = candidates[0]
                token_text = pkg.source.splitlines()[entry['line']-1].lstrip()
                require(token_text.lower().startswith((entry['kind'], 'overriding ', 'not overriding ')),
                        'recorded source line does not start the actual declaration')
        # Isolate the source-only delta from other existing opt-ins.
        control = workspace/(name+'-control'); shutil.copytree(fixture/'pristine', control)
        enhance(replace(config, source_view={}), control)
        before = hashes(control)
        changed = sorted(n for n in before if before[n] != original[n])
        expected_changed = {'api/presentation.json'} | {
            'api/'+p.name for p in (site/'api').glob('*.html') if p.name != 'index.html'}
        require(set(changed) == expected_changed, 'unrelated output changed')
        require(set(original)-set(before) == {'api/gnatdoc-source.css'} | {
            f['page'] for f in data['files']}, 'source-page output inventory differs')
        inventory[name] = dict(counts=stats, disabled_upstream_parity=parity,
            disabled_sha256=hashes(disabled), enabled_sha256=original,
            pristine_sha256=hashes(fixture/'pristine'), source_view=data,
            changed=changed, added=sorted(set(original)-set(before)),
            deterministic=True, idempotent=True, exact_source_text=True)
        print(name+' publication verified: '+str(stats['source_pages'])+' pages, '+
              str(stats['source_links'])+' links', flush=True)
    (workspace/'publication.json').write_text(sorted_json(inventory))
    return inventory


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def browser(workspace, inventory):
    from playwright.sync_api import sync_playwright, expect
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    result = dict(checks=[], navigation=[], external_requests=[], runtime_errors=[])
    try:
        with sync_playwright() as p:
            opts = {'headless': True}
            if os.environ.get('CHROMIUM_PATH'): opts['executable_path'] = os.environ['CHROMIUM_PATH']
            b = p.chromium.launch(**opts)
            try:
                for name in inventory:
                    for width in (1280, 390):
                        for theme in ('light', 'dark'):
                            for js in (True, False):
                                context = b.new_context(viewport=dict(width=width, height=900),
                                    color_scheme=theme, java_script_enabled=js)
                                def offline(route):
                                    if not route.request.url.startswith(base+'/'):
                                        result['external_requests'].append(route.request.url); route.abort()
                                    else: route.continue_()
                                context.route('**/*', offline)
                                page = context.new_page()
                                page.on('pageerror', lambda e: result['runtime_errors'].append(str(e)))
                                shell = base+'/'+name+'/api/index.html'
                                page.goto(shell)
                                symbols = ('Navigation_Report', 'Submit_Navigation_Report') if name == 'mel' else ('Create',)
                                if js:
                                    if width == 1280:
                                        expect(page.locator('#navigation-resize')).to_be_visible()
                                    else:
                                        expect(page.locator('#navigation-resize')).to_be_hidden()
                                for symbol in symbols:
                                    if js:
                                        query = 'Navigation Report' if symbol == 'Navigation_Report' else symbol
                                        page.locator('#package-search').fill(query)
                                        candidates = page.locator('#documentation-search-results a').filter(
                                            has_text=('AMS.MEL.IR.Image.'+symbol if name == 'mel' else 'OpenCV.Core.Create (overload'))
                                        expect(candidates.first).to_be_visible()
                                        # Exercise multiple actual overloads for Core.
                                        indexes = [0] if name == 'mel' else list(range(min(3, candidates.count())))
                                        targets = []
                                        for index in indexes:
                                            candidates.nth(index).click()
                                            frame = page.frame_locator('iframe')
                                            heading = frame.get_by_role('heading', name=symbol, exact=True)
                                            # Multiple overload headings: router's query supplies the exact anchor.
                                            from urllib.parse import parse_qs, urlsplit
                                            query_params = parse_qs(urlsplit(page.url).query)
                                            anchor = query_params.get('declaration', [None])[0]
                                            if anchor: heading = frame.locator('[id="'+anchor+'"]')
                                            elif name == 'mel':
                                                heading = heading.first
                                            link = heading.locator('xpath=following-sibling::a[1]')
                                            href = link.get_attribute('href'); targets.append(href)
                                            if name == 'mel':
                                                expected = 663 if symbol == 'Navigation_Report' else 775
                                                require(href.endswith('ams-mel-ir-image.ads.html#L'+str(expected)),
                                                        'mandatory MEL source link has wrong file/line')
                                            api_url = page.url
                                            link.click(); page.wait_for_url('**/source/**')
                                            expect(page.locator(':target')).to_contain_text(symbol)
                                            require(page.locator(':target').is_visible(), 'source line not visible')
                                            direct = page.url
                                            result['navigation'].append(dict(site=name, symbol=symbol,
                                                api_url=api_url.replace(base, ''), source_url=direct.replace(base, ''),
                                                visible_text=page.locator(':target').inner_text(),
                                                width=width, theme=theme))
                                            page.reload(); expect(page.locator(':target')).to_contain_text(symbol)
                                            fresh = context.new_page(); fresh.goto(direct)
                                            expect(fresh.locator(':target')).to_contain_text(symbol); fresh.close()
                                            page.go_back(); page.wait_for_url(api_url)
                                            page.go_forward(); page.wait_for_url(direct)
                                            page.go_back(); page.wait_for_url(api_url)
                                            page.locator('#package-search').fill('Navigation Report' if symbol == 'Navigation_Report' else symbol)
                                        require(len(targets) == len(set(targets)), 'overloads share source line')
                                    else:
                                        package = 'AMS.MEL.IR.Image' if name == 'mel' else 'OpenCV.Core'
                                        page.get_by_role('link', name=package, exact=True).click()
                                        frame = page.frame_locator('iframe')
                                        heading = frame.get_by_role('heading', name=package, exact=True)
                                        heading.locator('xpath=following-sibling::a[1]').click()
                                        page.wait_for_url('**/source/**')
                                        expect(page.locator(':target')).to_contain_text('package '+package)
                                        page.goto(shell)
                                # A complete source page remains readable without JS and fits the viewport.
                                record = next(f for f in inventory[name]['source_view']['files']
                                              if f['package'] == ('AMS.MEL.IR.Image' if name == 'mel' else 'OpenCV.Core'))
                                page.goto(base+'/'+name+'/'+record['page']+'#L1')
                                expect(page.get_by_role('link', name='Line 1', exact=True)).to_be_visible()
                                page.get_by_role('link', name='Line 1', exact=True).focus()
                                page.keyboard.press('Enter')
                                require(page.locator('body').evaluate('(e)=>e.scrollWidth <= innerWidth+2'),
                                        'source page overflows viewport')
                                require(page.locator('code').text_content().encode() ==
                                        (workspace/(name+'-authority')/record['source']).read_bytes(),
                                        'browser source text identity failed')
                                selected = page.locator('code').evaluate('''(e) => {
                                    const r = document.createRange(); r.selectNodeContents(e);
                                    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
                                    const value = s.toString(); s.removeAllRanges(); return value;
                                }''')
                                dom_text = page.locator('code').text_content()
                                # Chromium's visual selection omits a terminal LF
                                # at the end of PRE. DOM byte fidelity is checked
                                # above; permit only this observed UI conversion.
                                require(selected == dom_text or
                                        (dom_text.endswith('\n') and selected == dom_text[:-1]),
                                        'line numbers contaminated selected/copied source text')
                                if js:
                                    page.screenshot(path=str(workspace/f'{name}-{width}-{theme}.png'))
                                result['checks'].append(dict(site=name, width=width, theme=theme,
                                    javascript=js, status='passed', symbols=list(symbols)))
                                context.close()
            finally: b.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    require(not result['external_requests'] and not result['runtime_errors'], 'browser offline/runtime failure')
    (workspace/'browser.json').write_text(sorted_json(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--baseline-source', type=Path)
    parser.add_argument('--baseline-python', type=Path,
                        help='interpreter with the independently verified official v0.1.6 wheel')
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--browser-only', action='store_true')
    args = parser.parse_args()
    require(not (args.baseline_source and args.baseline_python), 'choose one baseline authority')
    if args.browser_only:
        inventory = json.loads((args.workspace/'publication.json').read_text())
    else:
        args.workspace.mkdir(parents=True, exist_ok=False)
        inventory = prepare(args.repository, args.workspace, args.baseline_source, args.baseline_python)
    if args.browser or args.browser_only: browser(args.workspace, inventory)
    print(json.dumps({name: data['counts'] for name, data in inventory.items()}))