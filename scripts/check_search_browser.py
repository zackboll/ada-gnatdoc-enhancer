#!/usr/bin/env python3
"""Chromium qualification against pinned actual Core HTML; local HTTP only.

Run with the separately installed Playwright test tool, never a runtime dep.
Builds disposable default, symbol and instance router sites with Core's custom
theme. No consumer checkout, publication, or release is modified.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import parse_qs, urlsplit

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.search import INDEX
from ada_gnatdoc_enhancer.util import sorted_json


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def run(fixture, workspace, output):
    from playwright.sync_api import sync_playwright, expect
    workspace.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture/'authority', workspace/'authority')
    authority = workspace/'authority'
    sites = {}
    for variant in ('default', 'symbol', 'instance'):
        config = load(authority, 'qualification.toml' if variant == 'instance' else 'default.toml')
        if variant == 'symbol':
            # Reload the edited disposable config so the custom-theme identity
            # binds the exact symbol configuration, too.
            path = authority/'symbol.toml'
            path.write_text((authority/'default.toml').read_text().replace(
                'mode = "packages"', 'mode = "packages"\nsymbol_bookmarks = true\ndefault_package = "OpenCV.Core"'))
            config = load(authority, 'symbol.toml')
        path = authority/(variant+'-search.toml')
        source_path = 'qualification.toml' if variant == 'instance' else 'symbol.toml' if variant == 'symbol' else 'default.toml'
        path.write_text((authority/source_path).read_text() + '\n[search]\nschema_version = 1\nmode = "documentation"\n')
        config = load(authority, path.name)
        site = workspace/variant
        shutil.copytree(fixture/'pristine', site)
        report = enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); assert hashes(site) == before
        sites[variant] = dict(config=config, site=site, report=report)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    results = dict(variants={}, external_requests=[], runtime_errors=[])
    queries = ('Sparse', 'Mat', 'Create', 'Clone', 'OpenCV.Core.Mat', 'ownership', 'unknown-gnatdoc023')
    try:
        with sync_playwright() as p:
            opts = {'headless': True}
            if os.environ.get('CHROMIUM_PATH'): opts['executable_path'] = os.environ['CHROMIUM_PATH']
            browser = p.chromium.launch(**opts)
            try:
                for variant in sites:
                    demonstrations = []
                    for width in (1280, 390):
                        for theme in ('light', 'dark'):
                            context = browser.new_context(viewport={'width':width, 'height':900}, color_scheme=theme)
                            def offline(route):
                                if not route.request.url.startswith(base+'/'):
                                    results['external_requests'].append(route.request.url); route.abort()
                                else: route.continue_()
                            context.route('**/*', offline)
                            page = context.new_page()
                            page.on('pageerror', lambda error: results['runtime_errors'].append(str(error)))
                            url = base+f'/{variant}/api/index.html'
                            page.goto(url)
                            status = page.locator('#package-results')
                            expect(status).to_have_text('Search public API names, signatures, and developer guides.')
                            search = page.locator('#package-search')
                            links = page.locator('#documentation-search-results a')
                            initial = page.url
                            selected = page.locator('a[aria-current="page"]').inner_text()
                            for q in queries:
                                search.fill(q)
                                if q == 'unknown-gnatdoc023':
                                    expect(status).to_have_text('No matching documentation.'); assert links.count() == 0
                                else:
                                    assert links.count() > 0, (variant, q, status.inner_text())
                                    if q == 'Sparse': assert 'OpenCV.Core.Sparse' in links.all_text_contents()
                                    if q in ('Mat','OpenCV.Core.Mat'): assert 'OpenCV.Core.Mat' in links.all_text_contents()
                                    if q == 'Create':
                                        names = links.all_text_contents()
                                        assert all(f'OpenCV.Core.Create (overload {i}/3)' in names for i in range(1,4))
                                        assert len({links.filter(has_text=f'OpenCV.Core.Create (overload {i}/3)').get_attribute('href') for i in range(1,4)}) == 3
                                    if q == 'Clone': assert any(name.startswith('OpenCV.Core.Clone') for name in links.all_text_contents())
                                    if q == 'ownership': assert 'Ownership and views' in links.all_text_contents()
                                    if width == 390:
                                        box = links.first.bounding_box()
                                        assert box and box['y'] + box['height'] < 495
                                assert page.url == initial
                                assert page.locator('a[aria-current="page"]').inner_text() == selected
                                if width == 1280 and theme == 'light':
                                    demonstrations.append(dict(query=q, status=status.inner_text(), results=links.all_text_contents()))
                                if variant == 'default' and q in ('Create','ownership','unknown-gnatdoc023'):
                                    page.screenshot(path=str(output/f'after-{q}-{width}-{theme}.png'))
                                assert page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth + 2')
                                assert page.locator('.side-navigation').evaluate('(e) => e.scrollWidth <= e.clientWidth + 2')
                            # Fast, mixed-case, partial and fully-qualified input.
                            for q in ('create', 'zzzzz', 'CLoNe', 'OpenCV.Core.Mat', 'Mat'):
                                search.fill(q)
                            assert 'OpenCV.Core.Mat' in links.all_text_contents()
                            for q in ('<img src=x onerror=alert(1)>', 'javascript:alert(1)', '../secret', '%00', '"</script>', 'x'*257):
                                search.fill(q); assert links.count() == 0; assert page.url == initial
                            assert page.locator('#documentation-search-results img, #documentation-search-results script').count() == 0
                            search.fill('Create'); search.press('ArrowDown')
                            assert page.locator('#documentation-search-results a').first.evaluate('(e) => e === document.activeElement')
                            page.keyboard.press('End'); assert links.last.evaluate('(e) => e === document.activeElement')
                            page.keyboard.press('Home'); page.keyboard.press('ArrowDown'); page.keyboard.press('ArrowUp')
                            page.keyboard.press('Escape'); expect(search).to_be_focused()
                            page.locator('#package-clear').click(); expect(search).to_have_value(''); expect(search).to_be_focused()
                            expect(page.locator('#documentation-search-results')).to_be_hidden()
                            assert not page.locator('body').evaluate('(e) => e.classList.contains("documentation-search-active")')
                            search.fill('Clone'); search.press('Escape'); expect(search).to_have_value('')
                            # Enter from input focuses the first native link; Enter
                            # on it uses the same router as normal mouse clicks.
                            search.fill('OpenCV.Core.Mat'); search.press('Enter')
                            destination = links.first.get_attribute('href'); page.keyboard.press('Enter')
                            page.wait_for_url(destination)
                            state = parse_qs(urlsplit(page.url).query)
                            if variant == 'default': assert 'declaration' in state and 'symbol' not in state
                            else: assert state['symbol'] == ['OpenCV.Core.Mat']
                            index_records = json.loads((sites[variant]['site']/INDEX).read_text())['records']
                            mat_anchor = next(r['href'].split('#')[1] for r in index_records if r['name'] == 'OpenCV.Core.Mat')
                            target = page.frame_locator('iframe').locator('[id="'+mat_anchor+'"]')
                            def settled(anchor):
                                # Outer reload/history and iframe replacement
                                # complete independently. Observe the new native
                                # document after both acknowledgements, rather
                                # than racing an old same-URL execution context.
                                for attempt in range(20):
                                    page.wait_for_timeout(100)
                                    frame = page.frame(name='document-content')
                                    try:
                                        frame.wait_for_url('**#'+anchor, timeout=1000)
                                        frame.wait_for_load_state('load', timeout=1000)
                                        frame.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                                        if frame.url.endswith('#'+anchor): return
                                    except Exception:
                                        if attempt == 19: raise
                                raise AssertionError('native destination never settled')
                            target.wait_for(); settled(mat_anchor)
                            assert target.evaluate('(e) => {const r=e.getBoundingClientRect();return r.top >= -2 && r.top < innerHeight;}')
                            page.reload(); page.wait_for_url(destination); settled(mat_anchor)
                            page.go_back(); page.wait_for_url(initial)
                            page.go_forward(); page.wait_for_url(destination); settled(mat_anchor)
                            assert target.evaluate('(e) => {const r=e.getBoundingClientRect();return r.top >= -2 && r.top < innerHeight;}')
                            fresh = context.new_page(); fresh.goto(destination)
                            expect(fresh.locator('a[aria-current="page"]')).to_have_text('OpenCV.Core'); fresh.close()
                            # An operation uses native declaration routing in all
                            # variants; no operation can borrow type symbol authority.
                            search.fill('Create')
                            create = links.filter(has_text='OpenCV.Core.Create (overload 2/3)')
                            create_url = create.get_attribute('href'); create.click(); page.wait_for_url(create_url)
                            operation_query = parse_qs(urlsplit(page.url).query)
                            assert 'declaration' in operation_query and 'symbol' not in operation_query
                            operation_anchor = operation_query['declaration'][0]
                            operation = page.frame_locator('iframe').locator('[id="'+operation_anchor+'"]')
                            expect(operation).to_have_text('Create')
                            settled(operation_anchor)
                            assert 'Dimensions' in operation.locator('xpath=following-sibling::pre[1]').inner_text()
                            page.reload(); page.wait_for_url(create_url)
                            expect(page.frame_locator('iframe').locator('[id="'+operation_anchor+'"]')).to_have_text('Create')
                            settled(operation_anchor)
                            page.go_back(); page.wait_for_url(destination); settled(mat_anchor)
                            page.go_forward(); page.wait_for_url(create_url); settled(operation_anchor)
                            # Exact package result also navigates via the shell.
                            search.fill('OpenCV.Core.Sparse')
                            package = links.filter(has_text='OpenCV.Core.Sparse').first
                            package_url = package.get_attribute('href'); package.click(); page.wait_for_url(package_url)
                            assert parse_qs(urlsplit(page.url).query) == {'package':['OpenCV.Core.Sparse']}
                            # A guide is a verified top-level page, never iframe input.
                            search.fill('ownership')
                            guide = links.filter(has_text='Ownership and views')
                            href = guide.get_attribute('href'); assert '/guides/ownership-and-views.html' in href
                            guide.click(); page.wait_for_url(href); expect(page.get_by_role('heading', name='Ownership and views', exact=True)).to_be_visible()
                            context.close()
                    results['variants'][variant] = dict(layouts=[1280,390], themes=['light','dark'], demonstrations=demonstrations)
                # Index caches fail closed on any independent missing/modified/
                # duplicated/forged payload. Search must not hide native links.
                payload = json.loads((sites['default']['site']/INDEX).read_text())
                modified = json.loads(json.dumps(payload)); modified['records'][0]['name'] = 'Forged.Public'
                forged = json.loads(json.dumps(payload)); forged['records'][0]['href'] = 'https://evil.invalid/'
                duplicated = dict(payload, records=payload['records']+[payload['records'][0]])
                mutations = [None, {}, modified, forged, duplicated, dict(payload, records=payload['records'][:-1]),
                             'malformed-json']
                for index, value in enumerate(mutations):
                    context = browser.new_context()
                    def corrupt(payload):
                        def respond(route):
                            route.fulfill(status=404 if payload is None else 200,
                                          content_type='application/json', body='{' if payload == 'malformed-json' else json.dumps(payload))
                        return respond
                    context.route('**/gnatdoc-search-index.json', corrupt(value))
                    page = context.new_page(); page.goto(base+'/default/api/index.html')
                    expect(page.locator('#package-results')).to_contain_text('Documentation search unavailable.')
                    original = page.url; page.locator('#package-search').fill('Create')
                    assert page.locator('#documentation-search-results a').count() == 0
                    assert page.locator('.side-navigation li a:visible').count() > 0
                    assert page.url == original; context.close()
                # Even a replaced cache digest cannot confer new destinations,
                # duplicate records, or public identities. This simulates a
                # corrupted digest attribute, not an approved publisher change.
                original_shell = (sites['default']['site']/'api/index.html').read_text()
                original_hash = hashlib.sha256((sites['default']['site']/INDEX).read_bytes()).hexdigest()
                for value in (modified, forged, duplicated):
                    body = json.dumps(value).encode()
                    shell = original_shell.replace(original_hash, hashlib.sha256(body).hexdigest())
                    context = browser.new_context()
                    def responses(html_body, json_body):
                        def respond(route):
                            if route.request.url.split('?')[0].endswith('/index.html'):
                                route.fulfill(content_type='text/html', body=html_body)
                            elif route.request.url.endswith('/gnatdoc-search-index.json'):
                                route.fulfill(content_type='application/json', body=json_body)
                            else: route.continue_()
                        return respond
                    context.route('**/*', responses(shell, body))
                    page = context.new_page(); page.goto(base+'/default/api/index.html')
                    expect(page.locator('#package-results')).to_contain_text('Documentation search unavailable.')
                    assert page.locator('#documentation-search-results a').count() == 0
                    context.close()
                # Tampered generated result links cannot be used to steer the
                # router, including a plausible same-origin but unapproved hash.
                context = browser.new_context(); page = context.new_page()
                page.goto(base+'/default/api/index.html'); expect(page.locator('#package-results')).to_contain_text('Search public API')
                page.locator('#package-search').fill('Create'); link = page.locator('#documentation-search-results a').first
                original = page.url; link.evaluate('(e) => e.href="https://evil.invalid/"'); link.click()
                assert page.url == original
                page.goto(base+'/default/api/index.html?package=OpenCV.Core&declaration='+'f'*64)
                assert 'declaration=' not in page.url
                page.wait_for_timeout(100)
                # A foreign frame does not acquire search/router authority.
                page.evaluate('document.querySelector("iframe").src="data:text/html,foreign"')
                page.locator('#package-search').fill('Create')
                page.locator('#documentation-search-results a').first.click()
                expected = parse_qs(urlsplit(page.url).query)['declaration'][0]
                expect(page.frame_locator('iframe').locator('[id="'+expected+'"]')).to_have_text('Create')
                context.close()
                context = browser.new_context(java_script_enabled=False); page = context.new_page()
                page.goto(base+'/default/api/index.html'); page.get_by_role('link',name='OpenCV.Core',exact=True).click()
                expect(page.frame_locator('iframe').get_by_role('heading',name='OpenCV.Core',exact=True)).to_be_visible(); context.close()
                assert not results['runtime_errors'], results['runtime_errors']
                assert not results['external_requests'], results['external_requests']
                results['index_tampering'] = len(mutations)
                results['rehashed_index_tampering'] = 3
                results['javascript_disabled'] = 'passed'
                results['status'] = 'passed'
            finally: browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    (output/'browser-search.json').write_text(sorted_json(results))
    print(json.dumps(dict(status=results['status'], variants=list(results['variants']), index_tampering=len(mutations))))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=Path(__file__).resolve().parents[1]/'tests/real-fixtures/search-core')
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); run(args.fixture, args.workspace, args.output)