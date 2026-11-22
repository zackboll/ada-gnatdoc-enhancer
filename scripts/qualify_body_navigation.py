#!/usr/bin/env python3
"""Starting-main byte parity, authentic body reconstruction and Chromium gates."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import functools
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
import threading

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance, verify
from ada_gnatdoc_enhancer.qualification import hashes
from ada_gnatdoc_enhancer.util import digest, require, sorted_json
from pin_source_view import pin
from qualify_source_view import Quiet, SourceText, check_source_page


START = '624c02e3b08198e77d3e126f745431af1b6dc8b0'
TREE = '8a722d7708a4e219354f50bc284cd3202e561bba'
MANIFEST = 'api/presentation.json'
ANCHOR = r'<a class="view-source" target="_top" href="source/[A-Za-z0-9_.\-/]+\.{}\.html#L[1-9][0-9]*">{}</a>'
BASELINE = {'mel': 'docs/gnatdoc-enhance.toml', 'core': 'default.toml'}


def baseline(start, root, filename, site, options):
    code = ('from pathlib import Path; from dataclasses import replace; '
            'from ada_gnatdoc_enhancer.config import load; '
            'from ada_gnatdoc_enhancer.pipeline import enhance, verify; '
            f'c=replace(load(Path({str(root)!r}), {filename!r}), source_view={options!r}, '
            'search=True, resizable_sidebar=True); '
            f'p=Path({str(site)!r}); enhance(c,p); verify(c,p)')
    subprocess.run([sys.executable, '-c', code], cwd=site.parent, check=True,
                   env=os.environ | {'PYTHONPATH': str(start/'src')})


def compare(schema1, schema2):
    """Byte-compare unchanged content; classify only the body/navigation delta."""
    old, new = hashes(schema1), hashes(schema2)
    first = json.loads((schema1/MANIFEST).read_bytes()); second = json.loads((schema2/MANIFEST).read_bytes())
    identity = second['source_view']; spec_pages = {f['page'] for f in identity['files']}
    bodies = {f['page'] for f in identity['bodies']}
    native = set(first['original_api_html']) - {'api/index.html'}
    require(set(new) == set(old) | bodies and not set(old) & bodies, 'body-mode inventory delta')
    for name in old:
        if name in native:
            rendered = (schema2/name).read_text()
            rendered = re.sub(' ' + ANCHOR.format('adb', 'View body'), '', rendered)
            rendered = re.sub('(' + ANCHOR.format('ads', 'View specification') + ')',
                              lambda m: m[0].replace('>View specification</a>', '>View source</a>'), rendered)
            require(rendered.encode() == (schema1/name).read_bytes(), 'unclassified API delta: ' + name)
        elif name in spec_pages:
            rendered = re.sub(rb'<nav aria-label="Ada source correspondence">.*?</nav>', b'',
                              (schema2/name).read_bytes())
            require(rendered == (schema1/name).read_bytes(), 'unclassified specification delta: ' + name)
        elif name != MANIFEST:
            require(old[name] == new[name], 'unrelated body-mode publication delta: ' + name)
    records = [{**f, 'declarations': [{k: v for k, v in e.items() if k not in
               ('body_source', 'body_line', 'body_omission')} for e in f['declarations']]}
               for f in identity['files']]
    require(records == first['source_view']['files'], 'specification inventory changed')
    keys = ('body_pages', 'body_operation_links', 'body_operation_omissions')
    current_counts = {k: v for k, v in second['counts'].items() if k not in keys}
    current_counts.update({k: first['counts'][k] for k in ('files', 'html_pages', 'links') if k in first['counts']})
    require(current_counts == first['counts'], 'unrelated presentation counts changed')
    require(second['output_sha256'] == {n: new[n] for n in set(first['output_sha256']) | bodies},
            'body-mode output hashes differ from complete inventory')
    for key in set(first) | set(second):
        if key not in ('source_view', 'output_sha256', 'counts'):
            require(first[key] == second[key], 'unclassified presentation metadata: ' + key)
    return dict(added=sorted(bodies), changed=sorted(n for n in old if old[n] != new[n]),
                schema1_sha256=old, schema2_sha256=new)


def commands_overlay(fixtures, root, site, provenance):
    for kind, dest, key in (('authority', root, 'source_files'), ('pristine', site, 'native_files')):
        for path, sha in provenance[key].items():
            data = (fixtures/'commands'/kind/path).read_bytes()
            require(digest(data) == sha, 'Commands acquisition fingerprint mismatch')
            (dest/path).write_bytes(data)


def prepare(repository, start, workspace):
    for expression, expected in (('HEAD', START), ('HEAD^{tree}', TREE)):
        require(subprocess.check_output(['git', '-C', str(start), 'rev-parse', expression],
                                        text=True).strip() == expected, 'wrong starting main')
    fixtures = repository/'tests/real-fixtures'; body_fixtures = fixtures/'body-navigation'
    provenance = json.loads((body_fixtures/'provenance.json').read_bytes()); results = {}
    for name in ('mel', 'core', 'commands'):
        print('Qualifying schema 2:', name, flush=True)
        kind = 'mel' if name == 'commands' else name
        fixture = fixtures/('search-'+kind); filename = BASELINE[kind]
        for path, sha in json.loads((fixture/'provenance.json').read_bytes())['files'].items():
            require(digest((fixture/path).read_bytes()) == sha, 'baseline fixture fingerprint mismatch')
        root = workspace/(name+'-authority'); shutil.copytree(fixture/'authority', root)
        pristine = workspace/(name+'-pristine'); shutil.copytree(fixture/'pristine', pristine)
        for path, sha in provenance[kind]['source_files'].items():
            raw = (body_fixtures/kind/'authority'/path).read_bytes()
            require(digest(raw) == sha, 'body acquisition fingerprint mismatch')
            (root/path).write_bytes(raw)
        if name == 'commands':
            commands_overlay(body_fixtures, root, pristine, provenance[name])
        config = replace(load(root, filename), search=True, resizable_sidebar=True)
        before = hashes(root)
        disabled = workspace/(name+'-disabled'); shutil.copytree(pristine, disabled)
        old = workspace/(name+'-start-disabled'); shutil.copytree(pristine, old)
        enhance(config, disabled); verify(config, disabled); baseline(start, root, filename, old, {})
        require(hashes(disabled) == hashes(old), 'disabled publication not byte-identical to starting main')
        options = {}
        for schema in (1, 2):
            filename_pin = f'source-native-{schema}.json'
            path = root/filename_pin
            pin(root, filename, pristine, path, schema)
            options[schema] = dict(schema_version=schema, native_manifest=filename_pin,
                                   native_manifest_sha256=digest(path.read_bytes()), mode=(
                'public-specifications' + ('-and-bodies' if schema == 2 else '')))
        schema1 = workspace/(name+'-schema1'); shutil.copytree(pristine, schema1)
        old1 = workspace/(name+'-start-schema1'); shutil.copytree(pristine, old1)
        baseline(start, root, filename, old1, options[1])
        settings = replace(config, source_view=options[1]); enhance(settings, schema1); verify(settings, schema1)
        require(hashes(schema1) == hashes(old1), 'schema 1 not byte-identical to starting main')
        settings = replace(config, source_view=options[2])
        site = workspace/name; shutil.copytree(pristine, site)
        counts = enhance(settings, site); verify(settings, site)
        initial = hashes(site); enhance(settings, site)
        repeat = workspace/(name+'-repeat'); shutil.copytree(pristine, repeat); enhance(settings, repeat)
        require(hashes(site) == hashes(repeat) == initial, 'schema-2 determinism/idempotence failure')
        require(before.items() <= hashes(root).items(), 'original source changed')
        data = json.loads((site/MANIFEST).read_bytes()); identity = data['source_view']
        require({n: digest(v.encode()) for n, v in data['original_api_html'].items()} ==
                {n: h for n, h in hashes(pristine).items() if n.endswith('.html')},
                'native HTML not preserved byte-for-byte')
        for record in identity['files'] + identity['bodies']:
            raw = (root/record['source']).read_bytes()
            parsed = SourceText((site/record['page']).read_text())
            require(parsed.text.encode() == raw and record['sha256'] == digest(raw) and
                    parsed.anchors == [f'L{i}' for i in range(1, record['lines']+1)],
                    'body-mode complete source/line fidelity failure')
        journeys = oracle(name, root, data)
        omissions = Counter(e.get('body_omission') for f in identity['files'] for e in f['declarations']
                            if 'body_omission' in e)
        results[name] = dict(counts=counts, disabled_parity=len(hashes(disabled)), schema1_parity=len(hashes(schema1)),
                             comparison=compare(schema1, site), source_view=identity, journeys=journeys,
                             omissions=dict(omissions), deterministic=True, idempotent=True)
        print(name, counts, dict(omissions), flush=True)
    (workspace/'body-publication.json').write_text(sorted_json(results))
    return results


def oracle(name, root, data):
    """Independent full-header oracle for mandatory journeys; never uses the walker."""
    specs = {
        'mel': ('AMS.MEL.IR.Image', [
            ('Submit_Navigation_Report', r'function Submit_Navigation_Report\s+\(Object : AMS\.MEL\.IR\.Image_Stream; Report : Navigation_Report\) return Navigation_Request')]),
        'core': ('OpenCV.Core', [
            ('Create', r'function Create\s+\(Rows, Columns : Natural; Element_Type : Mat_Type\) return Mat'),
            ('Create', r'function Create\s+\(Shape : Dimension_Array; Element_Type : Mat_Type\) return Mat')]),
        'commands': ('AMS.MEL.IR.Scheduling.Commands', [
            ('Exec_Stare', r'function Exec_Stare\s*\(Channel : Scheduling_Channel; Value : Stare_Task\) return Stare_Request'),
            ('Wait', r'function Wait\s*\(Request : Abort_Request; Timeout_Milliseconds : Natural\) return Abort_Result')]),
    }
    owner, profiles = specs[name]; identity = data['source_view']
    spec = next(f for f in identity['files'] if f['package'] == owner)
    body = next(f for f in identity['bodies'] if f['package'] == owner)
    api = next(n for n, html in data['original_api_html'].items() if '<h1>'+owner+'</h1>' in html)
    spec_text = (root/spec['source']).read_text(); body_text = (root/body['source']).read_text()
    def locate(text, pattern, end):
        found = list(re.finditer(r'(?m)^[ \t]*(' + pattern + r')(?=\s*' + end + ')', text))
        require(len(found) == 1, 'independent full header oracle not unique: ' + pattern)
        return text.count('\n', 0, found[0].start(1)) + 1, found[0][1]
    out = []
    for symbol, pattern in profiles:
        spec_line, _ = locate(spec_text, pattern, r'(?:;|with\s+Pre\b)')
        body_line, header = locate(body_text, pattern, r'is\b(?!\s*\()')
        found = [e for e in spec['declarations'] if e['name'] == owner+'.'+symbol and e['line'] == spec_line]
        require(len(found) == 1 and found[0].get('body_line') == body_line and
                found[0].get('body_source') == body['source'], 'wrong oracle implementation destination: '+symbol)
        out.append(dict(api=api, package=owner, symbol=symbol, anchor=found[0]['anchor'], spec=spec['page'],
                        body=body['page'], spec_line=spec_line, body_line=body_line, profile=header))
    if name in ('commands', 'core'):
        omitted = (r'function Wait \(Request : Stare_Request; Timeout_Milliseconds : Natural\) return Stare_Result'
                   if name == 'commands' else r'function Create \(Dimensions : Size; Element_Type : Mat_Type\) return Mat')
        spec_line, _ = locate(spec_text, omitted, ';')
        locate(body_text, omitted, r'is\s*\(')
        require([e.get('body_omission') for e in spec['declarations'] if e['line'] == spec_line] ==
                ['implementation-expression'], 'expression completion must have no direct-body link')
    return out


def browser(workspace, results):
    from playwright.sync_api import expect, sync_playwright
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(workspace)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    origin = f'http://127.0.0.1:{server.server_port}/'
    checks, journeys, external, errors = [], [], [], []
    try:
        with sync_playwright() as p:
            options = {'executable_path': os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
            chromium = p.chromium.launch(headless=True, **options)
            for width in (1280, 390):
                for theme in ('light', 'dark'):
                    for js in (True, False):
                        context = chromium.new_context(viewport=dict(width=width, height=900),
                            color_scheme=theme, java_script_enabled=js,
                            permissions=['clipboard-read', 'clipboard-write'])
                        context.on('page', lambda page: page.on('pageerror', lambda err: errors.append(str(err))))
                        def offline(route):
                            if route.request.url.startswith(origin):
                                route.continue_()
                            else:
                                external.append(route.request.url); route.abort()
                        context.route('**/*', offline)
                        page = context.new_page(); page.set_default_timeout(10000)
                        for name, result in results.items():
                            base = origin+name+'/'
                            def go(link, url):
                                page.keyboard.press('Tab'); link.focus(); expect(link).to_be_focused()
                                require(link.evaluate('(e)=>getComputedStyle(e).outlineStyle') != 'none',
                                        'source navigation keyboard focus outline missing')
                                page.keyboard.press('Enter'); page.wait_for_url(url)
                            for j in result['journeys']:
                                page.goto(base+j['api'])
                                heading = page.get_by_role('heading', name=j['package'], exact=True)
                                spec_link = heading.locator('xpath=following-sibling::a[1]')
                                expect(spec_link).to_have_text('View specification')
                                spec_package = base+'api/'+spec_link.get_attribute('href')
                                go(spec_link, spec_package)
                                expect(page.locator(':target')).to_contain_text('package '+j['package'])
                                package_body = page.get_by_role('link', name='View body', exact=True)
                                body_package = base+posixpath.join(posixpath.dirname(j['body']), package_body.get_attribute('href'))
                                go(package_body, body_package)
                                expect(page.locator(':target')).to_contain_text('package body '+j['package'])
                                go(page.get_by_role('link', name='View specification', exact=True), spec_package)
                                api = base+j['api']+'#'+j['anchor']; page.goto(api)
                                native_body = page.locator('[id="'+j['anchor']+'"]').locator('xpath=following-sibling::a[2]')
                                expect(native_body).to_have_text('View body')
                                target = base+j['body']+'#L'+str(j['body_line'])
                                go(native_body, target)
                                expect(page.locator(':target')).to_have_attribute('id', 'L'+str(j['body_line']))
                                length = j['profile'].count('\n') + 1
                                actual = ''.join(page.locator(f'#L{i}').text_content() for i in
                                                 range(j['body_line'], j['body_line']+length))
                                require(actual.lstrip().startswith(j['profile']), 'browser wrong overload profile')
                                page.reload(); expect(page.locator(':target')).to_be_visible()
                                fresh = context.new_page(); fresh.goto(target)
                                expect(fresh.locator(':target')).to_have_attribute('id', 'L'+str(j['body_line'])); fresh.close()
                                page.go_back(); page.wait_for_url(api); page.go_forward(); page.wait_for_url(target)
                                page.get_by_text('Corresponding operations', exact=True).click()
                                row = page.locator('nav li').filter(has=page.get_by_role('link', name=
                                    j['package']+'.'+j['symbol']+' (line '+str(j['body_line'])+')', exact=True))
                                destination = base+j['spec']+'#L'+str(j['spec_line'])
                                go(row.get_by_role('link', name='View specification at line '+str(j['spec_line'])), destination)
                                page.get_by_text('Corresponding operations', exact=True).click()
                                row = page.locator('nav li').filter(has=page.get_by_role('link', name=
                                    j['package']+'.'+j['symbol']+' (line '+str(j['spec_line'])+')', exact=True))
                                go(row.get_by_role('link', name='View body at line '+str(j['body_line'])), target)
                                journeys.append(dict(site=name, width=width, theme=theme, javascript=js, **j))
                            # Check the whole body inventory in every browser configuration.
                            for record in result['source_view']['bodies']:
                                page.goto(base+record['page'])
                                raw = (workspace/(name+'-authority')/record['source']).read_bytes()
                                checks.append(dict(site=name, page=record['page'], width=width, theme=theme,
                                    javascript=js, **check_source_page(page, raw, record['lines'])))
                        context.close()
            chromium.close()
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    require(not external and not errors, 'body navigation offline/runtime failure')
    (workspace/'body-browser.json').write_text(sorted_json(dict(checks=checks, journeys=journeys,
                                                               external_requests=external, runtime_errors=errors)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--starting-main', type=Path)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--browser', action='store_true')
    parser.add_argument('--browser-only', action='store_true')
    args = parser.parse_args()
    if args.browser_only:
        results = json.loads((args.workspace/'body-publication.json').read_bytes())
    else:
        require(args.starting_main is not None, 'starting main required for compatibility check')
        args.workspace.mkdir(parents=True, exist_ok=False)
        results = prepare(args.repository, args.starting_main.resolve(), args.workspace.resolve())
    if args.browser or args.browser_only:
        browser(args.workspace, results)