#!/usr/bin/env python3
"""Executed Chromium source-profile/fragment assertions for GNATDOC-008A.

The oracle proof is produced by qualify_operation_navigation.py. This checks
actual clicks and rendered declarations, not merely matching link labels.
"""
import argparse
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from ada_gnatdoc_enhancer.inventory import normalized


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def run(workspace, proof, history_only=False):
    from playwright.sync_api import sync_playwright
    selected = [d for d in proof if d['name'] in ('Filter_2D', 'Get_Gaussian_Kernel')]
    assert len(selected) == 4
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}/first/_site/api/'
    report = {'checks': [], 'scope': 'real pinned Imgproc; local Chromium, no production publication'}

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
        require(heading.count() == 1, 'native heading not unique')
        code = heading.locator('xpath=following-sibling::pre[1]').inner_text()
        require(normalized(code) == normalized(d['native_profile']), 'wrong rendered declaration profile')

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
                                page.goto(base+'index.html')
                                first, second = [d for d in selected if d['name'] == 'Filter_2D']
                                for d in (first, second):
                                    page.locator('.operation-group a[href="'+d['href']+'"]').click()
                                    page.frame(name='document-content').wait_for_url(base+d['href'])
                                page.evaluate('history.back()')
                                frame = page.frame(name='document-content')
                                require(frame is not None, 'Back left the API browser instead of selecting the previous overload')
                                frame.wait_for_url(base+first['href']); declaration(frame, first)
                                page.evaluate('history.forward()')
                                frame.wait_for_url(base+second['href']); declaration(frame, second)
                            check('API frame overload Back Forward (existing UI, not changed here)', frame_history, **dimensions)
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
    args = parser.parse_args()
    result = run(args.workspace, json.loads(args.proof.read_text()), args.history_only)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    raise SystemExit(0 if result['status'] == 'pass' else 2)