#!/usr/bin/env python3
"""Local Chromium qualification: real Core/custom theme and synthetic shell modes.

All sites are disposable. Optional --baseline-source compares every disabled
published byte against an independently checked-out upstream implementation.
"""
from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from urllib.parse import urlsplit

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import sorted_json


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def run(repository, workspace, baseline_source=None, browser_only=False):
    from playwright.sync_api import sync_playwright, expect
    workspace.mkdir(parents=True, exist_ok=browser_only)
    results = {'sites': {}, 'checks': [], 'runtime_errors': [], 'external_requests': []}
    sites = {}
    for name in ('bundled', 'custom', 'symbol', 'instance', 'operations', 'native'):
        if browser_only:
            site = workspace/name
            verify(load(workspace/(name+'-authority'), 'enabled.toml'), site)
            sites[name] = site
            results['sites'][name] = json.loads((workspace/'publication.json').read_text())[name]
            continue
        real = name not in ('operations', 'native')
        fixture = repository/'tests/real-fixtures/search-core' if real else repository/'tests/fixtures'/(
            'imgproc' if name == 'operations' else 'core')
        root = workspace/(name+'-authority')
        shutil.copytree(fixture/'authority' if real else fixture, root)
        source = (root/('qualification.toml' if name == 'instance' else 'default.toml' if real else 'project.toml')).read_text()
        if name == 'symbol':
            source = source.replace('mode = "packages"',
                'mode = "packages"\nsymbol_bookmarks = true\ndefault_package = "OpenCV.Core"')
        if name == 'native': source = source.replace('mode = "packages"', 'mode = "none"')
        if name == 'bundled': source = source.split('[presentation]')[0]
        if real: source += '\n[search]\nschema_version = 1\nmode = "documentation"\n'
        config_path = root/'resize.toml'; config_path.write_text(source)
        pristine = fixture/'pristine' if real else fixture/'_site'
        disabled = workspace/(name+'-disabled'); shutil.copytree(pristine, disabled)
        config = load(root, config_path.name)
        enhance(config, disabled); verify(config, disabled)
        parity = None
        if baseline_source:
            baseline = workspace/(name+'-baseline'); shutil.copytree(pristine, baseline)
            env = {**os.environ, 'PYTHONPATH': str(baseline_source/'src')}
            subprocess.run([os.sys.executable, '-c',
                'from pathlib import Path; from ada_gnatdoc_enhancer.config import load; '
                'from ada_gnatdoc_enhancer.pipeline import enhance; '
                f'enhance(load(Path({str(root)!r}), "resize.toml"), Path({str(baseline)!r}))'],
                cwd=workspace, env=env, check=True, capture_output=True)
            assert hashes(baseline) == hashes(disabled), name+' disabled byte parity'
            parity = hashes(disabled)
        # Keep disabled configuration identity stable for the independent comparison.
        path = root/'enabled.toml'
        path.write_text(source.replace('[navigation]', '[navigation]\nresizable_sidebar = true'))
        config = load(root, path.name)
        site = workspace/name; shutil.copytree(pristine, site)
        enhance(config, site); verify(config, site)
        before = hashes(site); enhance(config, site); assert before == hashes(site)
        second = workspace/(name+'-second'); shutil.copytree(pristine, second)
        enhance(config, second); assert before == hashes(second)
        old = hashes(disabled)
        # Custom theme identity includes the enabled configuration, so metadata
        # changes are expected; all old assets/declarations/guides remain exact.
        assert {n for n in old if old[n] != before[n]} == {'api/index.html', 'api/presentation.json'}
        assert set(before)-set(old) == {'api/gnatdoc-resize.css', 'api/gnatdoc-resize.js'}
        sites[name] = site
        results['sites'][name] = {'disabled_upstream_parity': parity,
            'enabled_sha256': before, 'deterministic': True, 'idempotent': True,
            'native_and_router_bytes_preserved': True}

    (workspace/'publication.json').write_text(sorted_json(results['sites']))

    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def record(name, **dimensions): results['checks'].append({'check': name, **dimensions, 'status': 'passed'})
    def width(page): return round(page.locator('.side-navigation').bounding_box()['width'])
    def clean(page):
        assert not page.locator('body').evaluate('(e) => e.classList.contains("navigation-resizing")')
        assert page.locator('iframe').evaluate('(e) => getComputedStyle(e).pointerEvents') != 'none'
        assert not page.locator('#navigation-resize').evaluate('(e) => e.hasPointerCapture(1)')
    def start(page):
        box = page.locator('#navigation-resize').bounding_box()
        page.mouse.move(box['x']+box['width']/2, box['y']+100); page.mouse.down()
    def drag(page, x):
        start(page); page.mouse.move(x, 200, steps=12); page.mouse.up(); clean(page)
    def viewport(page, value, height=900):
        page.set_viewport_size({'width':value, 'height':height})
        # Resize events are queued by the browser, not synchronous with CDP.
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')

    try:
        with sync_playwright() as p:
            options = {'headless': True}
            if os.environ.get('CHROMIUM_PATH'): options['executable_path'] = os.environ['CHROMIUM_PATH']
            browser = p.chromium.launch(**options)
            results['browser'] = 'Chromium '+browser.version
            try:
                for name in sites:
                    url = base+'/'+name+'/api/index.html'
                    for theme in ('light', 'dark'):
                        context = browser.new_context(viewport={'width':1280, 'height':900}, color_scheme=theme)
                        context.on('request', lambda request: results['external_requests'].append(request.url)
                                   if not request.url.startswith(base) else None)
                        page = context.new_page(); page.set_default_timeout(10000)
                        page.on('pageerror', lambda error: results['runtime_errors'].append(str(error)))
                        page.goto(url)
                        results['current_case'] = {'site':name, 'theme':theme}
                        divider = page.get_by_role('separator', name='Navigation width')
                        expect(divider).to_be_visible()
                        initial = width(page)
                        key = page.evaluate('Object.keys(localStorage).find(k => k.startsWith("gnatdoc:sidebar-width:"))')
                        assert key is None
                        # A real drag well inside the content iframe then back.
                        drag(page, 700); wide = width(page); assert wide > initial+200
                        assert page.locator('.document-content').bounding_box()['width'] >= 320
                        assert divider.get_attribute('aria-valuenow') == str(wide)
                        page.reload(); expect(divider).to_be_visible(); assert width(page) == wide
                        key = page.evaluate('Object.keys(localStorage).find(k => k.startsWith("gnatdoc:sidebar-width:"))')
                        assert key.endswith('/'+name+'/api/')
                        drag(page, 300); assert width(page) < wide
                        divider.focus(); before = width(page)
                        page.keyboard.press('ArrowRight'); assert width(page) == before+16
                        page.keyboard.press('ArrowLeft'); assert width(page) == before
                        page.keyboard.press('Home'); assert width(page) == 240
                        page.keyboard.press('End'); assert width(page) == 952
                        assert divider.get_attribute('aria-valuetext') == '952 pixels'
                        divider.dblclick(); assert width(page) == initial, (name, theme, 'reset', width(page), initial)
                        assert page.evaluate('(k) => localStorage.getItem(k)', key) is None
                        page.reload(); expect(divider).to_be_visible(); assert width(page) == initial
                        # In-flight cancellation, lost capture, blur and window changes
                        # must remove both capture and the iframe shield, without save.
                        record('pointer dragging across iframe, persistence, keyboard/ARIA and reset', site=name, theme=theme)
                        for event in ('pointercancel', 'lostpointercapture', 'blur', 'resize', 'mobile-resize'):
                            start(page); page.mouse.move(700, 200, steps=3)
                            if event == 'resize': viewport(page, 1100, 850)
                            elif event == 'mobile-resize': viewport(page, 390)
                            elif event == 'blur': page.evaluate('window.dispatchEvent(new Event("blur"))')
                            elif event == 'lostpointercapture': divider.evaluate('(e) => e.releasePointerCapture(1)')
                            else:
                                divider.evaluate('(e, t) => e.dispatchEvent(new PointerEvent(t, {pointerId:1}))', event)
                            page.mouse.up(); clean(page)
                            assert page.evaluate('(k) => localStorage.getItem(k)', key) is None
                            viewport(page, 1280)
                        # Bounds are recomputed; a constrained viewport does not
                        # overwrite the user's wider desktop preference.
                        divider.focus(); page.keyboard.press('End')
                        viewport(page, 900)
                        assert width(page) == 572
                        assert page.locator('.document-content').bounding_box()['width'] >= 320
                        viewport(page, 1280); assert width(page) == 952
                        # Each theme owns its breakpoint (Core custom:800, bundled:810).
                        breakpoint = 800 if name in ('custom', 'symbol', 'instance') else 810
                        for size in (breakpoint+1, breakpoint, 390):
                            viewport(page, size)
                            if size > breakpoint:
                                expect(divider).to_be_visible()
                            else:
                                expect(divider).to_be_hidden(); clean(page)
                                nav = page.locator('.side-navigation').bounding_box()
                                doc = page.locator('.document-content').bounding_box()
                                assert doc['y'] >= nav['y']+nav['height']-1
                            assert page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth+1')
                        viewport(page, 1280); assert width(page) == 952
                        divider.dblclick()
                        record('cancellation/lost capture/blur/desktop-mobile resize cleanup and bounds', site=name, theme=theme)
                        for raw, expected in (('NaN', initial), ('Infinity', initial), ('-20', initial),
                                              ('{}', initial), ('1e3', initial), ('0', initial),
                                              ('9999999', 952), ('1', 240), ('320.5', 321)):
                            page.evaluate('([k,v]) => localStorage.setItem(k,v)', [key,raw])
                            page.reload(); expect(divider).to_be_visible(); assert width(page) == expected, raw
                        divider.dblclick()
                        record('malformed storage validation and clamping', site=name, theme=theme)
                        # Isolated GitHub Pages project directories on one origin.
                        drag(page, 600); selected = width(page)
                        other = 'custom' if name != 'custom' else 'bundled'
                        page.goto(base+'/'+other+'/api/index.html')
                        assert width(page) != selected
                        page.goto(url); assert width(page) == selected
                        # Native links, router history, direct declarations and full
                        # search operate while the chosen width remains untouched.
                        if name in ('bundled', 'custom', 'symbol', 'instance'):
                            expect(page.locator('#package-results')).to_contain_text('Search public API')
                            page.locator('#package-search').fill('Create')
                            link = page.locator('#documentation-search-results a').first
                            label = link.inner_text()
                            records = json.loads((sites[name]/'api/gnatdoc-search-index.json').read_text())['records']
                            href = next(r['href'] for r in records if r['label'] == label)
                            anchor = urlsplit(href).fragment
                            link.click()
                            expect(page.frame_locator('iframe').locator('[id="'+anchor+'"]')).to_be_visible()
                            bookmark = page.url
                            page.locator('#package-clear').click()
                            page.get_by_role('link', name='OpenCV.Core.Sparse', exact=True).click()
                            expect(page.frame_locator('iframe').get_by_role('heading', name='OpenCV.Core.Sparse', exact=True)).to_be_visible()
                            page.go_back(); page.wait_for_url(bookmark)
                            expect(page.frame_locator('iframe').locator('[id="'+anchor+'"]')).to_be_visible()
                            page.reload(); expect(page.frame_locator('iframe').locator('[id="'+anchor+'"]')).to_be_visible()
                            page.goto(base+'/'+name+'/api/'+href)
                            expect(page.locator('[id="'+anchor+'"]')).to_be_visible()
                            page.goto(bookmark); expect(divider).to_be_visible(); assert width(page) == selected
                        elif name == 'operations':
                            link = page.locator('.operation-group a').first
                            anchor = urlsplit(link.get_attribute('href')).fragment
                            link.click()
                            expect(page.frame_locator('iframe').locator('[id="'+anchor+'"]')).to_be_visible()
                        else:
                            page.get_by_role('link', name='OpenCV.Core.Sparse', exact=True).click()
                            expect(page.frame_locator('iframe').get_by_role('heading', name='OpenCV.Core.Sparse', exact=True)).to_be_visible()
                        page.screenshot(path=str(workspace/(name+'-'+theme+'-desktop.png')))
                        viewport(page, 390)
                        page.screenshot(path=str(workspace/(name+'-'+theme+'-mobile.png')))
                        record('path isolation, search, bookmarks, navigation/history/direct links and responsive themes', site=name, theme=theme)
                        context.close()
                    for javascript in (False, True):
                        context = browser.new_context(java_script_enabled=javascript)
                        if javascript:
                            context.add_init_script('Object.defineProperty(window, "localStorage", {get() {throw new Error("denied");}})')
                        page = context.new_page(); page.goto(url)
                        if javascript:
                            expect(page.locator('#navigation-resize')).to_be_visible()
                            drag(page, 650); assert width(page) > 600
                            page.locator('#navigation-resize').dblclick()
                        else: expect(page.locator('#navigation-resize')).to_be_hidden()
                        package = 'OpenCV.Image_Processing' if name == 'operations' else 'OpenCV.Core.Sparse'
                        page.get_by_role('link', name=package, exact=True).click()
                        expect(page.frame_locator('iframe').get_by_role('heading', name=package, exact=True)).to_be_visible()
                        record('storage denied' if javascript else 'JavaScript-disabled native fallback', site=name)
                        context.close()
                assert not results['runtime_errors'], results['runtime_errors']
                assert not results['external_requests'], results['external_requests']
                results['status'] = 'passed'
                results.pop('current_case', None)
            finally: browser.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
        (workspace/'browser.json').write_text(sorted_json(results))
    print(json.dumps({'status':results['status'], 'checks':len(results['checks']), 'browser':results['browser']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--baseline-source', type=Path)
    parser.add_argument('--browser-only', action='store_true', help='reuse and independently verify generated sites')
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.workspace, args.baseline_source, args.browser_only)