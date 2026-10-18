#!/usr/bin/env python3
"""Executed Chromium source-profile/fragment/history assertions for GNATDOC-008A/B.

The oracle proof is produced by qualify_operation_navigation.py. This checks
actual clicks and rendered declarations, not merely matching link labels.
"""
import argparse
import functools
import json
import os
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from ada_gnatdoc_enhancer.inventory import normalized
from ada_gnatdoc_enhancer.util import digest


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def run(workspace, proof, history_only=False, geometry=None):
    from playwright.sync_api import sync_playwright
    selected = [d for d in proof if d['name'] in ('Filter_2D', 'Get_Gaussian_Kernel')]
    assert len(selected) == 4
    serving = Path(os.path.commonpath([workspace.resolve(), geometry.resolve()])) if geometry else workspace
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(serving)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    host = f'http://127.0.0.1:{server.server_port}/'
    base = host + (workspace.resolve().relative_to(serving.resolve())/'first/_site/api').as_posix()+'/'
    report = {'checks': [], 'traces': [], 'scope': 'real pinned Imgproc; local Chromium, no production publication',
              'consumer_source': '9ce22ae5ab70008e1147475a9e6d7baef82f1df0',
              'navigation_asset_sha256': digest((workspace/'first/_site/api/gnatdoc-navigation.js').read_bytes()),
              'enhancer_source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}

    def check(name, action, **dimensions):
        try:
            action(); result = {'status': 'pass'}
        except Exception as exc:
            result = {'status': 'fail', 'reason': str(exc)}
        report['checks'].append({'check': name, **dimensions, **result})

    def require(condition, reason):
        if not condition: raise AssertionError(reason)

    def declaration(page, d):
        require(urlsplit(page.url).fragment == urlsplit(d['href']).fragment, 'wrong native fragment')
        heading = page.locator('h4[id="'+urlsplit(d['href']).fragment+'"]')
        # A reload can already expose its destination URL before the new native
        # DOM exists. Wait for that heading, then still require exact uniqueness.
        heading.wait_for(state='attached')
        require(heading.count() == 1, 'native heading not unique')
        code = heading.locator('xpath=following-sibling::pre[1]').inner_text()
        require(normalized(code) == normalized(d['native_profile']), 'wrong rendered declaration profile')

    def outer(d=None):
        query = {'package': d['package'] if d else selected[0]['package']}
        if d: query['declaration'] = urlsplit(d['href']).fragment
        return base+'index.html?'+urlencode(query)

    def restored(page, d):
        # Wait for outer state first; never hold a Frame across document traversal.
        page.wait_for_url(outer(d))
        require(urlsplit(page.url).path.endswith('/api/index.html'), 'history left API browser')
        frame = page.frame(name='document-content')
        require(frame is not None, 'API iframe missing')
        frame.wait_for_url(base+d['href']); declaration(frame, d)
        require(page.locator('a[aria-current="location"]').get_attribute('href') == d['href'], 'wrong active declaration')
        report['traces'].append({'outer': page.url.replace(host, 'http://local/'),
                                 'native': frame.url.replace(host, 'http://local/'),
                                 'label': d['name']+f" ({d['ordinal']})"})

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            report['browser'] = 'Chromium '+browser.version
            for width in (1280, 390):
                for javascript in (True, False):
                    for theme in ('light', 'dark'):
                        context = browser.new_context(viewport={'width': width, 'height': 800},
                            java_script_enabled=javascript, color_scheme=theme)
                        page = context.new_page(); page.set_default_timeout(6000)
                        dimensions = {'width': width, 'javascript': javascript, 'theme': theme}
                        for d in (() if history_only else selected):
                            label = d['name']+f" ({d['ordinal']})"
                            target = base+d['href']

                            def click():
                                page.goto(base+'index.html')
                                link = page.get_by_role('link', name=label, exact=True)
                                require(link.get_attribute('href') == d['href'], 'wrong href')
                                link.click()
                                frame = page.frame(name='document-content'); frame.wait_for_url(target)
                                declaration(frame, d)
                                require(link.is_visible(), 'navigation entry not usable')
                            check('operation click exact fragment and rendered full profile', click,
                                  label=label, href=d['href'], **dimensions)

                            def keyboard():
                                page.goto(base+'index.html')
                                link = page.get_by_role('link', name=label, exact=True)
                                link.focus(); require(link.evaluate('e => e === document.activeElement'), 'focus lost')
                                page.keyboard.press('Enter')
                                frame = page.frame(name='document-content'); frame.wait_for_url(target)
                                declaration(frame, d)
                            check('keyboard Enter exact overload profile', keyboard, label=label, **dimensions)

                            def bookmark():
                                page.goto(target); declaration(page, d)
                                page.goto(base+'index.html')
                                if javascript: page.locator('#package-navigation').wait_for(state='visible')
                                index_url = page.url
                                page.go_back(); page.wait_for_url(target)
                                declaration(page, d)
                                page.go_forward(); page.wait_for_url(index_url)
                            check('direct native bookmark Back Forward exact overload', bookmark, label=label, **dimensions)

                        def layout():
                            page.goto(base+'index.html')
                            require(page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth+2'), 'outer overflow')
                            require(page.locator('.operation-group a').count() == 314, 'wrong entry inventory')
                            require(page.locator('.operation-group').count() > 1, 'categories missing')
                        if not history_only: check('responsive category navigation inventory', layout, **dimensions)
                        if javascript:
                            def frame_history():
                                history_sequence('Filter_2D')
                            def history_sequence(name, filtered=False):
                                page.goto(outer())
                                page.locator('#package-navigation').wait_for(state='visible')
                                if filtered: page.locator('#package-search').fill(name)
                                initial_length = page.evaluate('history.length')
                                first, second = [d for d in selected if d['name'] == name]
                                for d in (first, second):
                                    page.locator('.operation-group a[href="'+d['href']+'"]').click()
                                    restored(page, d)
                                expected_length = page.evaluate('history.length')
                                # Fresh contexts below test exact +2; this page may have
                                # a forward stack from preceding bookmark assertions.
                                require(expected_length <= initial_length+2, 'extra joint frame history entries')
                                page.locator('.operation-group a[href="'+second['href']+'"]').click()
                                require(page.evaluate('history.length') == expected_length, 'selected declaration duplicated history')
                                for _ in range(3):
                                    page.evaluate('history.back()'); restored(page, first)
                                    page.evaluate('history.forward()'); restored(page, second)
                                    require(page.evaluate('history.length') == expected_length, 'restoration wrote history')
                                page.evaluate('history.back()'); restored(page, first)
                                page.evaluate('history.back()'); page.wait_for_url(outer())
                                frame = page.frame(name='document-content')
                                frame.wait_for_url(base+urlsplit(first['href']).path)
                                page.evaluate('history.forward()'); restored(page, first)
                                page.evaluate('history.forward()'); restored(page, second)
                                if filtered:
                                    page.locator('#package-clear').click()
                                    require(page.locator('#package-search').input_value() == '', 'search reset failed')
                                    require(page.evaluate('history.length') == expected_length, 'search reset wrote history')
                            check('API frame overload Back Forward (existing UI, not changed here)', frame_history, **dimensions)
                            if not history_only:
                                check('Gaussian overload repeated Back Forward exact profiles', lambda: history_sequence('Get_Gaussian_Kernel'), **dimensions)
                                check('filtered operation history and search reset', lambda: history_sequence('Filter_2D', True), **dimensions)

                                def initial_and_reload():
                                    d = selected[0]
                                    page.goto(outer()); page.locator('#package-navigation').wait_for(state='visible')
                                    page.frame(name='document-content').wait_for_url(base+urlsplit(d['href']).path)
                                    page.goto(outer(d)); restored(page, d)
                                    before = page.evaluate('history.length'); page.reload(); restored(page, d)
                                    require(page.evaluate('history.length') == before, 'reload added history')
                                check('package initial state declaration deep link reload', initial_and_reload, **dimensions)

                                def invalid_states():
                                    package = selected[0]['package']; anchor = urlsplit(selected[0]['href']).fragment
                                    for query in ('package=Unknown', 'package='+package+'&declaration='+'f'*64,
                                        'package='+package+'&declaration=%ZZ', 'package='+package+'&declaration=%23'+anchor,
                                        'package='+package+'&package='+package,
                                        'package='+package+'&declaration='+anchor+'&declaration='+anchor,
                                        'package=javascript%3Aalert(1)&declaration=%3Cscript%3E'):
                                        page.goto(base+'index.html?'+query); page.wait_for_url(outer())
                                        frame = page.frame(name='document-content')
                                        frame.wait_for_url(base+urlsplit(selected[0]['href']).path)
                                        require(frame.locator('h1').inner_text() == package, 'invalid state escaped package')
                                check('invalid and duplicate initial state exact canonical fallback', invalid_states, **dimensions)

                                def fresh_history():
                                    fresh = context.new_page(); fresh.set_default_timeout(6000)
                                    try:
                                        fresh.goto(outer()); fresh.locator('#package-navigation').wait_for(state='visible')
                                        n = fresh.evaluate('history.length')
                                        for d in selected[:2]:
                                            link = fresh.locator('.operation-group a[href="'+d['href']+'"]')
                                            link.focus(); fresh.keyboard.press('Enter'); restored(fresh, d)
                                        require(fresh.evaluate('history.length') == n+2, 'not exactly one entry per declaration')
                                    finally: fresh.close()
                                check('fresh keyboard selections add exactly two history entries', fresh_history, **dimensions)

                                def external_frame():
                                    d = selected[0]; page.goto(outer(d)); restored(page, d)
                                    page.route('https://outside.invalid/**', lambda route: route.fulfill(
                                        status=200, content_type='text/html', body='<h1>Untracked external document</h1>'))
                                    try:
                                        page.evaluate("document.querySelector('iframe').contentWindow.location.replace('https://outside.invalid/untracked')")
                                        f = page.frame(name='document-content'); f.wait_for_url('https://outside.invalid/untracked')
                                        require(f.locator('h1').inner_text() == 'Untracked external document', 'cross-origin simulation failed')
                                        require(page.url == outer(d), 'external load changed tracked state')
                                        # Recovery uses the approved URL, not any external return URL.
                                        page.locator('.operation-group a[href="'+d['href']+'"]').click(); restored(page, d)
                                    finally: page.unroute('https://outside.invalid/**')
                                check('cross-origin iframe load untracked and approved recovery', external_frame, **dimensions)

                                def adversarial_links():
                                    d = selected[0]; page.goto(outer(d)); restored(page, d)
                                    link = page.locator('.operation-group a').first
                                    href = link.get_attribute('href'); before = page.evaluate('history.length')
                                    try:
                                        for bad in ('javascript:alert(1)', 'https://outside.invalid/escape.html',
                                                    '../escape.html', 'data:text/html,<h1>Injected</h1>',
                                                    base+href, urlsplit(href).path+'#'+'f'*64):
                                            link.evaluate('(e, href) => e.setAttribute("href", href)', bad)
                                            link.click()
                                            require(page.url == outer(d), 'unapproved link changed outer state')
                                            require(page.evaluate('history.length') == before, 'unapproved link added history')
                                            declaration(page.frame(name='document-content'), d)
                                    finally: link.evaluate('(e, href) => e.setAttribute("href", href)', href)
                                check('mutated unapproved links blocked without navigation', adversarial_links, **dimensions)

                                if geometry:
                                    def cross_package():
                                        geometry_base = host+(geometry.resolve().relative_to(serving.resolve())/'first/_site/api').as_posix()+'/'
                                        page.goto(geometry_base+'index.html')
                                        page.locator('#package-navigation').wait_for(state='visible')
                                        links = page.locator('#compilation-units + ul a')
                                        packages = [(links.nth(i).inner_text(), links.nth(i).get_attribute('href')) for i in range(2)]
                                        require(len(packages) == 2, 'missing real packages')
                                        def package_state(i):
                                            name, href = packages[i]
                                            page.wait_for_url(geometry_base+'index.html?'+urlencode({'package': name}))
                                            f = page.frame(name='document-content'); f.wait_for_url(geometry_base+href)
                                            require(f.locator('h1').inner_text() == name, 'wrong native package')
                                        package_state(0)
                                        n = page.evaluate('history.length')
                                        links.nth(1).click(); package_state(1)
                                        length = page.evaluate('history.length'); require(length <= n+1, 'duplicate package history')
                                        links.nth(1).click(); require(page.evaluate('history.length') == length, 'selected package duplicate')
                                        for _ in range(3):
                                            page.evaluate('history.back()'); package_state(0)
                                            page.evaluate('history.forward()'); package_state(1)
                                        require(page.evaluate('history.length') == length, 'package restoration wrote history')
                                        # A real anchor from the other package is not authority for this package.
                                        operation = page.locator('.operation-group a').first.get_attribute('href')
                                        owner = next(name for name, href in packages if href == operation.split('#')[0])
                                        wrong = next(name for name, _ in packages if name != owner)
                                        page.goto(geometry_base+'index.html?'+urlencode({'package':wrong,'declaration':operation.split('#')[1]}))
                                        page.wait_for_url(geometry_base+'index.html?'+urlencode({'package':wrong}))
                                        f = page.frame(name='document-content')
                                        f.wait_for_url(geometry_base+next(h for name,h in packages if name==wrong))
                                        require(f.locator('h1').inner_text() == wrong, 'cross-package anchor accepted')
                                        # Distinct real declaration destinations across both owners.
                                        chosen = []
                                        for name, href in packages:
                                            link = page.locator('.operation-group a[href^="'+href+'#"]').first
                                            native_href = link.get_attribute('href')
                                            link.click()
                                            f = page.frame(name='document-content'); f.wait_for_url(geometry_base+native_href)
                                            anchor = native_href.split('#')[1]
                                            profile = f.locator('h4[id="'+anchor+'"]').locator('xpath=following-sibling::pre[1]').inner_text()
                                            require(bool(profile.strip()), 'empty cross-package native profile')
                                            chosen.append((name, native_href, profile))
                                        def operation_state(d):
                                            name, href, profile = d
                                            page.wait_for_url(geometry_base+'index.html?'+urlencode({'package':name,'declaration':href.split('#')[1]}))
                                            f = page.frame(name='document-content'); f.wait_for_url(geometry_base+href)
                                            require(f.locator('h1').inner_text() == name, 'wrong declaration owner')
                                            require(f.locator('h4[id="'+href.split('#')[1]+'"]').locator(
                                                'xpath=following-sibling::pre[1]').inner_text() == profile, 'wrong restored cross-package profile')
                                        length = page.evaluate('history.length')
                                        for _ in range(3):
                                            page.evaluate('history.back()'); operation_state(chosen[0])
                                            page.evaluate('history.forward()'); operation_state(chosen[1])
                                        require(page.evaluate('history.length') == length, 'declaration restoration wrote history')
                                    check('real Geometry cross-package history and wrong-owner rejection', cross_package, **dimensions)
                            def search():
                                page.goto(base+'index.html'); page.locator('#package-search').fill('Filter_2D')
                                for d in (d for d in selected if d['name'] == 'Filter_2D'):
                                    require(page.get_by_role('link', name=d['name']+f" ({d['ordinal']})", exact=True).is_visible(), 'search lost overload')
                                require(page.get_by_role('link', name='Get_Gaussian_Kernel (1)', exact=True).is_hidden(), 'search failed to hide unrelated')
                                page.locator('#package-clear').click()
                                require(page.get_by_role('link', name='Get_Gaussian_Kernel (1)', exact=True).is_visible(), 'clear failed')
                            if not history_only: check('operation search and clear', search, **dimensions)
                        context.close()
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    report['status'] = 'pass' if all(c['status'] == 'pass' for c in report['checks']) else 'fail'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--history-only', action='store_true', help='Reproduce API frame history independently on baseline output')
    parser.add_argument('--geometry', type=Path, help='Qualified real multi-package Geometry workspace')
    args = parser.parse_args()
    result = run(args.workspace, json.loads(args.proof.read_text()), args.history_only, args.geometry)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    raise SystemExit(0 if result['status'] == 'pass' else 2)