#!/usr/bin/env python3
"""Chromium checks on a complete source-block candidate, with no fallback pages."""
from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run(repository, workspace):
    if workspace.exists():
        raise ValueError('browser workspace must be fresh')
    root = workspace / 'source'
    shutil.copytree(repository / 'tests/source-block-fixtures/mel', root)
    config = load(root, 'docs/gnatdoc-authored-pilot.toml')
    site = root / 'native'
    enhance(config, site); verify(config, site)
    contract = json.loads((root / 'docs/gnatdoc-authored.json').read_bytes())
    examples = json.loads((root / 'docs/examples/manifest.json').read_bytes())['examples']
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    url = f'http://127.0.0.1:{server.server_port}/'
    contexts = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width in (1280, 390):
                for theme in ('light', 'dark'):
                    for js in (True, False):
                        context = browser.new_context(viewport={'width': width, 'height': 800},
                                                      color_scheme=theme, java_script_enabled=js)
                        page = context.new_page(); page.set_default_timeout(8000)
                        errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
                        checks = 0

                        def check(value, label):
                            nonlocal checks
                            if not value:
                                raise ValueError((width, theme, js, page.url, label))
                            checks += 1

                        for name in ['index.html', *(e['path'] for e in contract['guides'])]:
                            check(page.goto(url + name).status == 200, 'page response')
                            check(page.locator('h1').is_visible(), 'heading')
                            check(page.locator('body').evaluate('(e)=>e.scrollWidth<=innerWidth+2'), 'overflow')
                        page.goto(url + 'guides/examples.html')
                        for entry in examples:
                            section = page.locator('section[id="' + entry['id'] + '"]')
                            listing = section.locator('code[data-example-source="' + entry['main'] + '"]')
                            check(listing.text_content() == (root / 'docs/examples' / entry['main']).read_text(),
                                  'complete main roundtrip')
                        disclosure = page.locator('details').first
                        disclosure.locator('summary').click()
                        check(disclosure.get_attribute('open') is not None, 'inert disclosure open')
                        check(disclosure.locator('code[data-example-source]').is_visible(), 'support source visible')
                        page.goto(url + 'guides/api-map.html')
                        rows = page.locator('li[data-catalog-entry]')
                        check(rows.count() > 0, 'catalog rows')
                        row = rows.first
                        href = row.locator('a').first.get_attribute('href')
                        row.locator('a').first.click()
                        check(page.locator('[id="' + href.split('#')[1] + '"]').is_visible(), 'native anchor')
                        page.goto(url + 'api/index.html')
                        if js:
                            frame = page.frame_locator('iframe[name="document-content"]')
                            frame.get_by_role('heading', name='AMS.MEL', exact=True).wait_for()
                            check('package=AMS.MEL' in page.url, 'default package')
                        check(not errors, 'script errors')
                        contexts.append(dict(width=width, theme=theme, javascript=js, checks=checks, passed=True))
                        context.close()
            browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join()
    report = dict(candidate_complete=True, fallback=False, contexts=contexts,
                  checks=sum(c['checks'] for c in contexts))
    (workspace / 'browser.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    run(args.repository.absolute(), args.workspace.absolute())