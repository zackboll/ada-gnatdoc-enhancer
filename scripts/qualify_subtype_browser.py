#!/usr/bin/env python3
"""Real Contour -> hash-verified Core Point_Array Chromium qualification."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json

CORE = 'f8aef00c5366b4275ccd3d934f9c73ea5b83cd4f'
BASE = 'https://core.invalid/' + CORE + '/api/'
PAGE = 'ea2ebcbc108269c77d7c6d44d2dabdfb5f6d0179ad5622b1be3cbceaee5c44aa.html'
ANCHOR = 'da696e09a1f1b297516365244e16533e23cca626f26df4bb3f727a64beb697b0'
GEOMETRY_PAGE = '4f90dae6ae3d13b7eca2073a4084d7aafc29ca4b1a5df10de478124a1cd77135.html'
CONTOUR = '0c3fbeacf849b3776f9533db4d982b2125bc49319590c9215acbc2ffaff07503'


def run(workspace, output):
    root = workspace / 'geometry-current'
    site = root / 'first'
    core = root / 'dependency/native'
    spec = json.loads((root / 'core-0.5.0-input.json').read_text())
    require(hashes(core) == spec['pristine_sha256'], 'Core native bytes changed')
    expected_profile = ('type Point_Array is array (Natural range <>) of Point;')
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
        SimpleHTTPRequestHandler, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    records = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width in (1280, 390):
                    for javascript in (True, False):
                        context = browser.new_context(viewport={'width': width, 'height': 900},
                                                      java_script_enabled=javascript)
                        served = []
                        errors = []
                        def route_core(route):
                            url = urlsplit(route.request.url)
                            require(url.scheme == 'https' and url.netloc == 'core.invalid',
                                    'unexpected intercepted host')
                            require(url.path.startswith('/'+CORE+'/api/'), 'wrong offline revision')
                            filename = url.path.rsplit('/', 1)[-1]
                            require(filename not in ('', '.', '..') and '/' not in filename,
                                    'unsafe native filename')
                            path = core / 'api' / filename
                            require('api/'+filename in spec['pristine_sha256'], 'unapproved Core asset')
                            payload = path.read_bytes()
                            require(digest(payload) == spec['pristine_sha256']['api/'+filename],
                                    'intercepted bytes not independently hash-verified')
                            served.append({'url': route.request.url, 'sha256': digest(payload)})
                            route.fulfill(status=200, body=payload, content_type=(
                                'text/css' if filename.endswith('.css') else 'text/html'))
                        context.route(BASE+'**', route_core)
                        context.route('**/favicon.ico', lambda route: route.fulfill(status=204))
                        page = context.new_page()
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        geometry = f'http://127.0.0.1:{server.server_port}/api/{GEOMETRY_PAGE}#{CONTOUR}'
                        target = BASE + PAGE + '#' + ANCHOR
                        def expect_geometry():
                            page.locator('h4:target').wait_for()
                            require(page.locator('h4:target').inner_text() == 'Contour', 'wrong Geometry heading')
                            snippet = page.locator('h4:target + pre')
                            require(snippet.inner_text().strip() == 'subtype Contour is OpenCV.Point_Array;',
                                    'wrong Geometry source profile')
                            links = snippet.locator('a.type-reference')
                            require(links.count() == 1, 'Contour must have exactly one base link')
                            require(links.get_attribute('href') == target and
                                    links.get_attribute('data-type') == 'opencv.point_array',
                                    'wrong qualified type identity/destination')
                            return links
                        def expect_core():
                            page.locator('h4:target').wait_for()
                            require(page.url == target, 'wrong Core fragment')
                            require(page.locator('h1').inner_text() == 'OpenCV', 'wrong native owner')
                            require(page.locator('h4:target').inner_text() == 'Point_Array', 'wrong native type')
                            profile = ' '.join(page.locator('h4:target + pre').inner_text().split())
                            require(profile == expected_profile, f'wrong Core profile: {profile}')
                        page.goto(geometry)
                        expect_geometry().click()
                        expect_core()
                        page.reload()
                        expect_core()
                        page.go_back()
                        expect_geometry()
                        page.go_forward()
                        expect_core()
                        require(any(x['url'] == BASE+PAGE for x in served), 'real native page not requested')
                        require(not errors, f'browser errors: {errors}')
                        records.append({'width': width, 'javascript': javascript, 'status': 'pass',
                                        'exact_native_profile': expected_profile, 'target': target,
                                        'verified_native_requests': served})
                        output.write_text(sorted_json({'checks': records, 'production_hosting_verified': False}))
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print('PASS: four real Chromium desktop/mobile JavaScript on/off cases')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.workspace, args.output)