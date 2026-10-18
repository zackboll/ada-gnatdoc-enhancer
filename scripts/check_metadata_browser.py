#!/usr/bin/env python3
"""Optional Chromium qualification of document metadata below a project prefix.

Serves an ALREADY enhanced site below a non-root prefix (a GitHub project site
such as /opencv_features_ada/) and checks, for every HTML page, the browser
title, language and character set against verified identities: generated
pages from the hash-bound native originals, author pages from their own
validated metadata. Also checks title restoration on Back/Forward, API frame
titles, deep-linked declarations, search, keyboard focus, JavaScript-disabled
pages, and that no request leaves the prefix. Not a screen-reader, cross-browser
or hosted-deployment certification. Playwright is an optional test tool.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.metadata import Document
from ada_gnatdoc_enhancer.native_html import snapshot
from ada_gnatdoc_enhancer.pipeline import MANIFEST, document_titles, verify


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def expected(config, site: Path) -> tuple[dict, dict, dict]:
    """Titles and languages of every page, and package name -> API page."""
    with tempfile.TemporaryDirectory() as temp:
        raw = Path(temp); (raw/'api').mkdir()
        for name, text in json.loads((site/MANIFEST).read_text())['original_api_html'].items():
            (raw/name).write_text(text)
        (raw/'api/gnatdoc.css').write_bytes((site/'api/gnatdoc.css').read_bytes())
        native = snapshot(config, raw)
        titles = document_titles(config, native)
        packages = {p.package: 'api/' + p.path.name for p in native.pages.values()}
    languages = {}
    for path in sorted(site.rglob('*.html')):
        name = path.relative_to(site).as_posix()
        document = Document(path.read_text(encoding='utf-8'))
        titles.setdefault(name, document.titles[0])
        languages[name] = document.langs[0][0]
    return titles, languages, packages


def run(root: Path, configuration: str, site: Path, prefix: str) -> dict:
    from playwright.sync_api import sync_playwright
    config = load(root, configuration)
    verify(config, site)
    titles, languages, packages = expected(config, site)
    pages = sorted(titles)
    report = {'checks': [], 'prefix': prefix, 'pages': len(pages),
              'scope': 'local Chromium below a project prefix; not hosted, cross-browser or screen-reader'}
    with tempfile.TemporaryDirectory() as temp:
        serving = Path(temp)/'serve'
        shutil.copytree(site, serving/prefix.strip('/'))
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(serving)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        base = origin + prefix

        def check(name, action, **dimensions):
            try:
                action(); result = {'status': 'pass'}
            except Exception as exc:
                result = {'status': 'fail', 'reason': str(exc)[:500]}
            report['checks'].append({'check': name, **dimensions, **result})

        def require(condition, detail='browser invariant failed'):
            if not condition:
                raise AssertionError(detail)

        def under(url):
            return url.startswith(base) or url.startswith('data:') or url == 'about:blank'

        def frame_heading(page, name):
            page.frame_locator('iframe').get_by_role('heading', name=name, exact=True).wait_for()

        try:
            with sync_playwright() as playwright:
                options = {'headless': True}
                if os.environ.get('CHROMIUM_PATH'):
                    options['executable_path'] = os.environ['CHROMIUM_PATH']
                browser = playwright.chromium.launch(**options)
                report['browser'] = 'Chromium ' + browser.version
                try:
                    for width, height in ((1280, 900), (390, 844)):
                        for theme in ('light', 'dark'):
                            context = browser.new_context(viewport={'width': width, 'height': height},
                                                          color_scheme=theme)
                            page = context.new_page(); page.set_default_timeout(8000)
                            seen = {'requests': [], 'failures': [], 'errors': []}
                            page.on('request', lambda r: seen['requests'].append(r.url))
                            page.on('requestfailed', lambda r: seen['failures'].append(r.url))
                            page.on('response', lambda r: seen['failures'].append(f'{r.status} {r.url}') if r.status >= 400 else None)
                            page.on('pageerror', lambda e: seen['errors'].append(str(e)))
                            page.on('console', lambda m: seen['errors'].append(m.text) if m.type == 'error' else None)
                            dimensions = {'width': width, 'theme': theme}
                            try:
                                for name in pages:
                                    def metadata(name=name):
                                        for value in seen.values():
                                            value.clear()
                                        response = page.goto(base + name, wait_until='networkidle')
                                        require(response.status == 200, f'HTTP {response.status}')
                                        require(page.title() == titles[name], f'title {page.title()!r}')
                                        state = page.evaluate('() => [document.documentElement.lang, document.characterSet,'
                                                              ' document.documentElement.scrollWidth - innerWidth]')
                                        require(state[:2] == [languages[name], 'UTF-8'], f'language/charset {state}')
                                        require(state[2] <= 2, f'horizontal page overflow {state[2]}')
                                        require(all(under(u) for u in seen['requests']),
                                                f'request outside prefix {[u for u in seen["requests"] if not under(u)]}')
                                        require(not seen['failures'] and not seen['errors'], f'{seen}')
                                    check('page title language charset below prefix', metadata, page=name, **dimensions)
                                guides = [n for n in pages if n.startswith('guides/')]
                                if 'index.html' in pages and guides:
                                    def portal():
                                        for guide in guides:
                                            page.goto(base, wait_until='networkidle')
                                            require(page.title() == titles['index.html'])
                                            page.locator(f'header a[href$="{guide}"]').first.click()
                                            page.wait_for_url(base + guide)
                                            require(page.title() == titles[guide], guide)
                                            page.go_back(); page.wait_for_url(base)
                                            require(page.title() == titles['index.html'])
                                            page.go_forward(); page.wait_for_url(base + guide)
                                            require(page.title() == titles[guide], guide)
                                    check('portal guide navigation and Back Forward titles', portal, **dimensions)
                                    def keyboard():
                                        page.goto(base + guides[0], wait_until='networkidle')
                                        page.keyboard.press('Tab')
                                        focused = page.evaluate('() => [document.activeElement.tagName,'
                                                                ' getComputedStyle(document.activeElement).outlineStyle]')
                                        require(focused[0] == 'A' and focused[1] != 'none', f'{focused}')
                                    check('guide keyboard focus is visible', keyboard, **dimensions)
                                names = sorted(packages)
                                def frames():
                                    page.goto(base + 'api/index.html', wait_until='networkidle')
                                    first = page.locator('#compilation-units + ul a').first.inner_text()
                                    frame_heading(page, first)
                                    frame = page.frame(name='document-content')
                                    require(page.title() == titles['api/index.html'] and frame.title() == titles[packages[first]])
                                    other = next((n for n in names if n != first), None)
                                    if other:
                                        page.get_by_role('link', name=other, exact=True).click(); frame_heading(page, other)
                                        require(frame.title() == titles[packages[other]] and page.title() == titles['api/index.html'])
                                        page.go_back(); frame_heading(page, first)
                                        require(frame.title() == titles[packages[first]])
                                        page.go_forward(); frame_heading(page, other)
                                        require(frame.title() == titles[packages[other]])
                                check('API frame titles follow package navigation and history', frames, **dimensions)
                                def search():
                                    page.goto(base + 'api/index.html', wait_until='networkidle')
                                    page.fill('#package-search', names[-1])
                                    require('result' in page.locator('#package-results').inner_text())
                                    page.click('#package-clear')
                                    require(page.locator('#package-search').input_value() == '')
                                check('API search and clear', search, **dimensions)
                                def deep_link():
                                    target = packages[names[0]]
                                    anchor = page.context.request.get(base + target).text().split('<h4 id=', 1)[1][:64]
                                    page.goto(base + target + '#' + anchor, wait_until='networkidle')
                                    require(page.title() == titles[target])
                                    require(page.locator(':target').get_attribute('id') == anchor)
                                check('deep-linked native declaration keeps its title', deep_link, **dimensions)
                            finally:
                                context.close()
                    context = browser.new_context(java_script_enabled=False, viewport={'width': 1280, 'height': 900})
                    page = context.new_page(); page.set_default_timeout(8000)
                    try:
                        for name in pages:
                            def static(name=name):
                                page.goto(base + name)
                                require(page.title() == titles[name])
                            check('JavaScript-disabled page title', static, page=name)
                        def native_navigation():
                            page.goto(base + 'api/index.html')
                            link = page.locator('#compilation-units + ul a[target="document-content"]').last
                            name = link.inner_text(); link.click(); frame_heading(page, name)
                            require(page.frame(name='document-content').title() == titles[packages[name]])
                        check('JavaScript-disabled native navigation frame title', native_navigation)
                    finally:
                        context.close()
                finally:
                    browser.close()
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)
    report['status'] = 'pass' if all(c['status'] == 'pass' for c in report['checks']) else 'fail'
    report['passed'] = sum(c['status'] == 'pass' for c in report['checks'])
    report['titles'] = titles
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='project root of the configuration')
    parser.add_argument('--config', required=True, help='configuration path relative to --root')
    parser.add_argument('--site', type=Path, required=True, help='enhanced site to check (not modified)')
    parser.add_argument('--prefix', default='/opencv_features_ada/')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not (args.prefix.startswith('/') and args.prefix.endswith('/') and args.prefix != '/'):
        parser.error('--prefix must be a non-root path ending in /')
    result = run(args.root.resolve(), args.config, args.site.resolve(), args.prefix)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(result['status'], f"{result['passed']}/{len(result['checks'])}", result.get('browser'))
