#!/usr/bin/env python3
"""Chromium localhost-only qualification of generated, pinned consumer examples.

Requires qualify_examples.py baseline/candidate outputs. Playwright is a test
tool only, never an enhancer dependency. Screenshots/results are retained.
"""
from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import urljoin, urlsplit


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run(workspace, output):
    from playwright.sync_api import sync_playwright
    output.mkdir(parents=True, exist_ok=True)
    results = dict(cases=[], runtime_errors=[], unexpected_requests=[])
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as playwright:
            options = dict(headless=True)
            if os.environ.get('CHROMIUM_PATH'):
                options['executable_path'] = os.environ['CHROMIUM_PATH']
            browser = playwright.chromium.launch(**options)
            try:
                for width in (1280, 390):
                    for theme in ('light', 'dark'):
                        for javascript in (True, False):
                            context = browser.new_context(viewport=dict(width=width, height=900),
                                                          color_scheme=theme, java_script_enabled=javascript,
                                                          permissions=['clipboard-read', 'clipboard-write'])
                            def request(route):
                                if not route.request.url.startswith(base + '/'):
                                    results['unexpected_requests'].append(route.request.url); route.abort()
                                else:
                                    route.continue_()
                            context.route('**/*', request)
                            page = context.new_page()
                            page.on('pageerror', lambda error: results['runtime_errors'].append(str(error)))
                            for name, relative in (('landing', 'index.html'), ('guide', 'guides/ownership-and-views.html'),
                                                   ('literals', 'guides/sparse-and-persistence-guide.html')):
                                url = base + '/candidate/core-search/enabled/' + relative
                                baseline = context.new_page()
                                assert baseline.goto(base + '/baseline/core-search/site/' + relative).status == 200
                                expected = baseline.locator('pre').all_text_contents(); baseline.close()
                                assert page.goto(url).status == 200
                                assert page.locator('pre').all_text_contents() == expected
                                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, relative)
                                colors = {}
                                for token in ('keyword', 'comment', 'string', 'character', 'attribute'):
                                    locator = page.locator('.ada-example .ada-' + token)
                                    if locator.count():
                                        locator.first.scroll_into_view_if_needed()
                                        assert locator.first.is_visible()
                                        colors[token] = locator.first.evaluate('(e) => getComputedStyle(e).color')
                                        assert colors[token] != locator.first.evaluate('(e) => getComputedStyle(e.closest("pre")).color')
                                block = page.locator('pre.ada-example').first
                                original = block.text_content()
                                # Browser selection, then actual keyboard/clipboard copy.
                                block.evaluate('(e) => {const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r)}')
                                assert page.evaluate('getSelection().toString()') == original
                                page.keyboard.press('Control+c')
                                assert page.evaluate('navigator.clipboard.readText()') == original
                                link = page.locator('.ada-example a.ada-api-reference').first
                                destination = None
                                if link.count():
                                    destination = urljoin(url, link.get_attribute('href'))
                                    link.focus(); assert link.evaluate('(e) => document.activeElement === e')
                                    assert link.evaluate('(e) => getComputedStyle(e).outlineStyle') != 'none'
                                    page.keyboard.press('Enter'); page.wait_for_url(destination)
                                    fragment = urlsplit(destination).fragment
                                    assert page.locator('[id="' + fragment + '"]').count() == 1
                                    page.goto(url)
                                screenshot = f'{name}-{width}-{theme}-js{int(javascript)}.png'
                                page.screenshot(path=str(output/screenshot), full_page=False)
                                results['cases'].append(dict(page=name, width=width, height=900, theme=theme,
                                                             javascript=javascript, colors=colors,
                                                             destination=destination, exact_text=True, clipboard=True,
                                                             no_page_overflow=True, screenshot=screenshot))
                            # Feature-off visual parity: independent official and candidate rendering.
                            for relative in ('index.html', 'guides/typed-access-guide.html', 'api/index.html'):
                                page.goto(base + '/baseline/core-search/site/' + relative)
                                before = page.screenshot(animations='disabled')
                                page.goto(base + '/candidate/core-search/site/' + relative)
                                assert page.screenshot(animations='disabled') == before, ('legacy presentation', relative)
                            context.close()
            finally:
                browser.close()
        assert not results['runtime_errors'], results['runtime_errors']
        assert not results['unexpected_requests'], results['unexpected_requests']
        observed = {token for case in results['cases'] for token in case['colors']}
        assert {'keyword', 'comment', 'string', 'attribute'} <= observed
    finally:
        server.shutdown(); thread.join(); server.server_close()
        (output/'results.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.workspace.resolve(), args.output.resolve())