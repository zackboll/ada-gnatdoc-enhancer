#!/usr/bin/env python3
"""Chromium checks on real authored Core output and its native Mat anchor."""
from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import threading

from ada_gnatdoc_enhancer.authored import render
from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.examples import Resolver
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.util import require, sorted_json


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def run(workspace):
    from playwright.sync_api import sync_playwright
    root = Path(__file__).resolve().parents[1] / 'tests/verified-fixtures/core'
    config = load(root, 'project.toml'); native = snapshot(config, root / 'native')
    resolver = Resolver(config, native, ['docs/example.adb'])
    clone = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : Mat)' in d.declaration.signature)
    umat = next(d for d in resolver.symbols['opencv.core.clone'] if 'Self : UMat)' in d.declaration.signature)
    create_mapping = next(m for m in json.loads((root / 'mapping.json').read_text())['mappings']
                          if m['occurrence']['text'] == 'Create')
    create = next(d for d in resolver.symbols['opencv.core.create']
                  if d.declaration.signature.strip().endswith(create_mapping['profile']))
    workspace.mkdir(parents=True)
    site = workspace / 'site'; shutil.copytree(root / 'native', site)
    for name, payload in render(config, native).items():
        path = site / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
    expected = (root / 'docs/example.adb').read_bytes().decode()
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    results = []
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if os.environ.get('CHROMIUM_PATH'): options['executable_path'] = os.environ['CHROMIUM_PATH']
            browser = playwright.chromium.launch(**options)
            try:
                for javascript in (True, False):
                    for theme in ('light', 'dark'):
                        context = browser.new_context(java_script_enabled=javascript, color_scheme=theme,
                            permissions=['clipboard-read', 'clipboard-write'])
                        page = context.new_page(); errors = []; requests = []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        def route(request):
                            if not request.request.url.startswith(base + '/'):
                                requests.append(request.request.url); request.abort()
                            else: request.continue_()
                        context.route('**/*', route)
                        response = page.goto(base + '/guides/verified.html')
                        require(response.status == 200, 'guide navigation failed')
                        require(page.locator('pre.ada-example').text_content() == expected, 'browser example bytes changed')
                        require(page.locator('a.ada-api-reference a').count() == 0, 'nested generated hyperlinks')
                        require(page.locator('.ada-keyword').count() > 0 and page.locator('.ada-number').count() > 0,
                                'syntax colors missing')
                        colors = {kind: page.locator('.ada-' + kind).first.evaluate('(e) => getComputedStyle(e).color')
                                  for kind in ('keyword', 'number')}
                        require(len(set(colors.values())) == 2, 'syntax coloring not applied')
                        pre = page.locator('pre.ada-example'); pre.focus()
                        require(pre.evaluate('(e) => document.activeElement === e'), 'example focus failed')
                        page.evaluate('''() => {const r = document.createRange();
                            r.selectNodeContents(document.querySelector('pre.ada-example'));
                            getSelection().removeAllRanges(); getSelection().addRange(r);}''')
                        page.keyboard.press('Control+c')
                        copied = page.evaluate('navigator.clipboard.readText()')
                        require(copied.encode() == expected.encode(), 'clipboard bytes changed')
                        page.evaluate('getSelection().removeAllRanges()')
                        link = page.locator('a.ada-api-reference').filter(has_text='Clone')
                        require(link.count() == 1 and link.get_attribute('href') == '../api/' + clone.href,
                                'wrong Mat Clone hyperlink')
                        link.focus(); require(link.evaluate('(e) => document.activeElement === e'), 'link focus failed')
                        link.click(); page.wait_for_url(base + '/api/' + clone.href)
                        heading = page.locator('[id="' + clone.section.anchor + '"]')
                        require(heading.is_visible(), 'Mat native anchor invisible')
                        require('Self : Mat' in heading.evaluate('(e) => e.nextElementSibling.textContent'),
                                'Mat Clone click opened wrong overload')
                        require(page.url != base + '/api/' + umat.href, 'UMat destination selected')
                        page.goto(base + '/guides/verified.html')
                        create_link = page.locator('a.ada-api-reference').filter(has_text='Create')
                        require(create_link.get_attribute('href') == '../api/' + create.href, 'wrong Create destination')
                        create_link.click(); page.wait_for_url(base + '/api/' + create.href)
                        require('return Mat' in page.locator('[id="' + create.section.anchor + '"]').evaluate(
                            '(e) => e.nextElementSibling.textContent'), 'Create click opened wrong return overload')
                        require(not errors and not requests, 'browser errors/external requests')
                        results.append(dict(javascript=javascript, theme=theme, destination=clone.href,
                                            native_profile=clone.section.code, exact_text=True,
                                            clipboard=True, focus=True, syntax=colors, create_destination=create.href))
                        context.close()
            finally: browser.close()
    finally:
        server.shutdown(); thread.join(); server.server_close()
        (workspace / 'results.json').write_text(sorted_json(results))
    print(json.dumps({'cases': len(results), 'status': 'PASS'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    run(parser.parse_args().workspace)