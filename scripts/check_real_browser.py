#!/usr/bin/env python3
"""Optional Chromium qualification of an ALREADY enhanced isolated real site.

Does not enhance inputs. Records individual checks, including failures, instead
of treating browser availability or a structural assertion as a browser pass.
Playwright is an optional local test tool, not a runtime dependency.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import subprocess
import threading
import tomllib
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def generic_checks(browser, workspace, url, check, require):
    """Executed browser checks, separate from static source/native qualification."""
    from ada_gnatdoc_enhancer.config import load
    from ada_gnatdoc_enhancer.generic_instances import ANCHOR, summaries
    from ada_gnatdoc_enhancer.inventory import packages
    from ada_gnatdoc_enhancer.native_html import snapshot
    from ada_gnatdoc_enhancer.validation import Page
    config=load(workspace/'first','qualification.toml')
    # Original bytes are hash-bound by the trusted project qualification record;
    # the summary itself is reconstructed, never authorized by output metadata.
    from ada_gnatdoc_enhancer.pipeline import verify
    verify(config,workspace/'first/_site')
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        raw=Path(temp);(raw/'api').mkdir()
        data=json.loads((workspace/'first/_site/api/presentation.json').read_text())
        for name,text in data['original_api_html'].items():(raw/name).write_text(text)
        (raw/'api/gnatdoc.css').write_bytes((workspace/'first/_site/api/gnatdoc.css').read_bytes())
        native=snapshot(config,raw);sections,_=summaries(config,packages(config),native)
    selected=('opencv.core.uint8_vec2','opencv.core.float16_vec3','opencv.core.float32_vec4',
              'opencv.core.float64_vec2','opencv.core.float32_matx3x3')
    for width in (1280,390):
        for theme in ('light','dark'):
            for javascript in (True,False):
                context=browser.new_context(viewport={'width':width,'height':760},color_scheme=theme,
                                            java_script_enabled=javascript)
                page=context.new_page();page.set_default_timeout(5000)
                errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
                try:
                    for key in selected:
                        file=native.pages[key].path.name; summary=sections['api/'+file]
                        destination=urljoin(url,file)+'#'+ANCHOR
                        dimensions={'width':width,'theme':theme,'javascript':javascript,'package':key}
                        def visible():
                            page.goto(destination)
                            section=page.locator('.generic-instance-summary')
                            require(section.count()==1 and section.is_visible())
                            require(page.locator('h4').count()==0)
                            require(page.locator(':target').get_attribute('id')==ANCHOR)
                            require(section.locator('table').count()==2)
                            require(section.locator('th[scope="col"]').count()==4)
                        check('generic visible unique summary and presentation bookmark',visible,**dimensions)
                        def meanings():
                            text=' '.join(page.locator('.generic-instance-summary').inner_text().split())
                            def contains(phrase):
                                if phrase not in text:
                                    raise AssertionError('missing rendered phrase '+repr(phrase)+' in '+repr(text))
                            if key.endswith('matx3x3'):
                                contains('3 × 3 array of Float32_Value')
                                contains('Row_Count');contains('Column_Count')
                                contains('does not imply shared native storage')
                            else:
                                length=int(key[-1])
                                require(f'Natural range 0 .. {length-1}' in text)
                                require(f'Array of {length} ' in text)
                            contains('not additional source declarations')
                            if 'float16' in key:require('binary16 encodings' in text and 'numerical interpretation' in text)
                        check('generic dimensions member meanings ownership',meanings,**dimensions)
                        def layout():
                            require(page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth+2'))
                            require(page.locator('.generic-instance-summary table').evaluate_all(
                                '(es) => es.every(e => e.getBoundingClientRect().width <= innerWidth && e.scrollWidth <= e.clientWidth+2)'))
                            require(page.evaluate("() => matchMedia('(prefers-color-scheme: "+theme+")').matches"))
                        check('generic readable responsive tables and theme',layout,**dimensions)
                        for index,href in enumerate(Page(summary).links):
                            target=urljoin(destination,href);fragment=urlsplit(target).fragment
                            def navigation(index=index,href=href,target=target,fragment=fragment):
                                page.goto(destination)
                                link=page.locator('.generic-instance-summary a').nth(index)
                                require(link.get_attribute('href')==href)
                                link.click();page.wait_for_url(target)
                                if fragment:
                                    require(page.locator('h4[id="'+fragment+'"]').count()==1)
                                else:require(page.locator('h1').count()==1)
                                page.go_back();page.wait_for_url(destination)
                                page.go_forward();page.wait_for_url(target)
                                page.goto(target)
                                if fragment:require(page.locator(':target').get_attribute('id')==fragment)
                            check('generic hyperlink click direct bookmark Back Forward',navigation,
                                  hyperlink=href,**dimensions)
                        if javascript:
                            def keyboard():
                                page.goto(destination)
                                first=page.locator('.generic-instance-summary a').first
                                first.focus();page.keyboard.press('Tab')
                                second=page.locator('.generic-instance-summary a').nth(1)
                                require(second.evaluate('(e) => e === document.activeElement'))
                                require(second.evaluate('(e) => getComputedStyle(e).outlineStyle !== "none"'))
                                target=urljoin(destination,second.get_attribute('href'))
                                page.keyboard.press('Enter');page.wait_for_url(target)
                            check('generic keyboard activation and visible focus',keyboard,**dimensions)
                        check('generic no JavaScript errors',lambda:require(not errors),**dimensions)
                finally:context.close()


def expected_titles(workspace):
    """Verified document titles, reconstructed from the hash-bound native originals."""
    import tempfile
    from ada_gnatdoc_enhancer.config import load
    from ada_gnatdoc_enhancer.native_html import snapshot
    from ada_gnatdoc_enhancer.pipeline import document_titles
    config=load(workspace/'first','qualification.toml')
    with tempfile.TemporaryDirectory() as temp:
        raw=Path(temp);(raw/'api').mkdir()
        data=json.loads((workspace/'first/_site/api/presentation.json').read_text())
        for name,text in data['original_api_html'].items():(raw/name).write_text(text)
        (raw/'api/gnatdoc.css').write_bytes((workspace/'first/_site/api/gnatdoc.css').read_bytes())
        native=snapshot(config,raw)
        return document_titles(config,native),{p.package:'api/'+p.path.name for p in native.pages.values()}


def run(workspace, source_sha=None):
    from playwright.sync_api import sync_playwright
    from ada_gnatdoc_enhancer.util import digest
    titles,package_pages=expected_titles(workspace)
    configuration=tomllib.loads((workspace/'first/qualification.toml').read_text())
    navigation_mode=configuration['navigation']['mode']
    handler=functools.partial(Quiet,directory=str(workspace))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    report={'checks':[],'scope':'isolated real native API site; not consumer portal',
            'navigation_mode':navigation_mode,
            'consumer_source':source_sha,
            'navigation_asset_sha256':digest((workspace/'first/_site/api/gnatdoc-navigation.js').read_bytes()),
            'enhancer_source':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    # HTTPS interception is explicitly a local publication simulation, NOT
    # evidence of a remotely hosted deployment. First revalidate pinned inputs.
    external_proofs={}
    if configuration.get('external_dependencies'):
        from ada_gnatdoc_enhancer.config import load
        from ada_gnatdoc_enhancer.external_types import destinations, read_json
        from ada_gnatdoc_enhancer.util import inside, regular
        config=load(workspace/'first','qualification.toml')
        destinations(config)
        for dep in config.dependencies:
            manifest=read_json(inside(config.root,dep['manifest']))
            for identity in dep['types']:
                item=manifest['types'][identity.lower()]
                destination=dep['base_url']+item['page']+'#'+item['anchor']
                external_proofs[destination]={'revision':dep['revision'],**item,
                    'native_root':inside(config.root,dep['site'])/'api',
                    'base_url':dep['base_url']}
        report['external_publication']='intercepted reserved .invalid HTTPS test mapping; NOT actual HTTPS hosting'
        report['published_url_verified']=False
    url=f'http://127.0.0.1:{server.server_port}/first/_site/api/index.html'
    def check(name,action,**dimensions):
        try:
            action();result={'status':'pass'}
        except Exception as exc:result={'status':'fail','reason':str(exc)}
        report['checks'].append({'check':name,**dimensions,**result})
    def require(condition):
        if not condition:raise AssertionError('browser invariant failed')
    try:
        with sync_playwright() as playwright:
            opts={'headless':True}
            if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
            browser=playwright.chromium.launch(**opts)
            report['browser']='Chromium '+browser.version
            try:
                def intercept(route):
                    request=route.request.url
                    proof=next((p for p in external_proofs.values()
                                if request.startswith(p['base_url'])),None)
                    if proof is None:route.abort();return
                    filename=request.removeprefix(proof['base_url'])
                    if '/' in filename or '?' in filename or '%' in filename:
                        route.abort();return
                    path=regular(proof['native_root']/filename)
                    route.fulfill(status=200,body=path.read_bytes(),
                                  content_type='text/css' if path.suffix=='.css' else 'text/html')
                for width in (1280,390):
                    for theme in ('light','dark'):
                        context=browser.new_context(viewport={'width':width,'height':760},color_scheme=theme)
                        page=context.new_page()
                        if external_proofs:page.context.route('https://core.invalid/**',intercept)
                        page.set_default_timeout(5000)
                        dimensions={'width':width,'theme':theme}
                        errors=[]
                        page.on('pageerror',lambda err:errors.append(str(err)))
                        try:
                            page.goto(url,wait_until='networkidle')
                            links=page.locator('#compilation-units + ul a')
                            names=links.all_text_contents()
                            require(len(names)>=1)
                            first=names[0];second=names[1] if len(names)>1 else first
                            check('theme assets and color scheme',lambda:require(page.evaluate(
                                "() => document.styleSheets.length >= 2 && matchMedia('(prefers-color-scheme: "+theme+")').matches")),**dimensions)
                            def search():
                                box=page.locator('#package-search');box.fill(second)
                                require('result' in page.locator('#package-results').inner_text())
                                page.locator('#package-clear').click();require(box.input_value()=='')
                            check('search and clear',search,**dimensions)
                            def navigation():
                                if len(names)==1:
                                    # No second package exists in Imgproc's pinned
                                    # site. Exercise reloadable bookmark/history,
                                    # not a fictitious cross-package transition.
                                    page.goto(url+'?package='+first,wait_until='networkidle')
                                    page.goto(url+'?package='+first+'&bookmark=1',wait_until='networkidle')
                                    page.go_back();page.wait_for_url('**?package='+first)
                                    page.go_forward();page.wait_for_url('**&bookmark=1')
                                    require(page.locator('a[aria-current="page"]').inner_text()==first)
                                    page.frame_locator('iframe').get_by_role('heading',name=first,exact=True).wait_for()
                                    return
                                page.get_by_role('link',name=second,exact=True).click()
                                page.wait_for_url('**?package='+second)
                                page.frame_locator('iframe').get_by_role('heading',name=second,exact=True).wait_for()
                                page.go_back();page.wait_for_url('**?package='+first)
                                page.go_forward();page.wait_for_url('**?package='+second)
                                page.goto(url+'?package='+second,wait_until='networkidle')
                                require(page.locator('a[aria-current="page"]').inner_text()==second)
                            check('package bookmark direct link Back Forward' if len(names)>1 else
                                  'single-package bookmark reload Back Forward (no cross-package transition)',
                                  navigation,**dimensions)
                            def category():
                                link=page.locator('#operation-navigation a').first
                                href=link.get_attribute('href');link.click()
                                frame=page.frame(name='document-content')
                                frame.wait_for_url('**/'+href)
                                require(frame.locator('[id="'+href.split('#')[1]+'"]').count()==1)
                            if navigation_mode=='operations':
                                check('operation category real anchor',category,**dimensions)
                            else:
                                check('package-only policy has no operation categories',lambda:require(
                                    page.locator('#operation-navigation').count()==0),**dimensions)
                            check('syntax and local type links',lambda:require(
                                page.frame_locator('iframe').locator('.ada-keyword').count()>0 and
                                page.frame_locator('iframe').locator('a.type-reference').count()>0),**dimensions)
                            def type_destination():
                                frame=page.frame(name='document-content')
                                link=frame.locator('a.type-reference').first
                                href=link.get_attribute('href');destination=urljoin(frame.url,href)
                                link.click();frame.wait_for_url(destination)
                                anchor=urlsplit(destination).fragment
                                require(bool(anchor) and frame.locator('[id="'+anchor+'"]').count()==1)
                            check('follow local type link to unique native anchor',type_destination,**dimensions)
                            if external_proofs:
                                def external_destination():
                                    # Reset the API iframe; local navigation may
                                    # have changed its current declaration page.
                                    page.goto(url,wait_until='networkidle')
                                    frame=page.frame(name='document-content')
                                    link=frame.locator('a.type-reference[href^="https://"]').first
                                    destination=link.get_attribute('href');proof=external_proofs[destination]
                                    before=frame.url
                                    link.click();frame.wait_for_url(destination)
                                    anchor=proof['anchor']
                                    require('/'+proof['revision']+'/' in frame.url)
                                    require(frame.get_by_role('heading',name=proof['package'],exact=True).count()==1)
                                    heading=frame.locator('[id="'+anchor+'"]')
                                    require(heading.count()==1 and heading.inner_text()==proof['qualified_name'].rsplit('.',1)[1])
                                    from ada_gnatdoc_enhancer.util import digest
                                    require(digest(heading.locator('xpath=following-sibling::pre[1]/code').inner_text().encode())==proof['native_declaration_sha256'])
                                    # A child-frame history entry does not emit
                                    # a top-level load event. Trigger browser
                                    # history and assert the actual frame URL.
                                    page.evaluate('history.back()');frame.wait_for_url(before)
                                    page.evaluate('history.forward()');frame.wait_for_url(destination)
                                    direct=page.context.new_page()
                                    try:
                                        direct.goto(destination,wait_until='networkidle')
                                        require(direct.locator('[id="'+anchor+'"]').count()==1)
                                    finally:direct.close()
                                    report.setdefault('external_destinations',[]).append({
                                        'url':destination,'revision':proof['revision'],
                                        'type':proof['qualified_name'],'anchor':anchor,**dimensions,
                                        'transport':'local interception; not hosted'})
                                check('external pinned type click direct Back Forward',external_destination,**dimensions)
                            def keyboard():
                                page.locator('#package-search').focus();page.keyboard.press('Tab')
                                require(page.locator('#package-clear').evaluate('(e) => e === document.activeElement'))
                                require(page.locator('#package-clear').evaluate('(e) => getComputedStyle(e).outlineStyle !== "none"'))
                            check('keyboard focus and visible outline',keyboard,**dimensions)
                            check('responsive outer viewport',lambda:require(page.locator('body').evaluate(
                                '(e) => e.scrollWidth <= innerWidth+2')),**dimensions)
                            def document_metadata():
                                page.goto(url,wait_until='networkidle')
                                require(page.title()==titles['api/index.html'])
                                require(page.evaluate('() => [document.documentElement.lang, document.characterSet]')==['en','UTF-8'])
                                page.frame_locator('iframe').get_by_role('heading',name=first,exact=True).wait_for()
                                frame=page.frame(name='document-content')
                                require(frame.title()==titles['api/'+urlsplit(frame.url).path.rsplit('/',1)[1]])
                                require(frame.evaluate('() => document.documentElement.lang')=='en')
                                if len(names)>1:
                                    page.get_by_role('link',name=second,exact=True).click()
                                    page.frame_locator('iframe').get_by_role('heading',name=second,exact=True).wait_for()
                                    require(frame.title()==titles[package_pages[second]] and page.title()==titles['api/index.html'])
                                    page.go_back()
                                    page.frame_locator('iframe').get_by_role('heading',name=first,exact=True).wait_for()
                                    require(frame.title()==titles[package_pages[first]] and page.title()==titles['api/index.html'])
                            check('document title language charset and frame titles',document_metadata,**dimensions)
                            def title_history():
                                ordered=sorted(n for n in titles if n!='api/index.html')
                                one,two=ordered[0],(ordered[1] if len(ordered)>1 else 'api/index.html')
                                same=lambda target:(lambda current:urlsplit(current).path==urlsplit(target).path)
                                a=urljoin(url,one.split('/',1)[1]);b=urljoin(url,two.split('/',1)[1])
                                page.goto(a,wait_until='networkidle');require(page.title()==titles[one])
                                page.goto(b,wait_until='networkidle');require(page.title()==titles[two])
                                page.go_back();page.wait_for_url(same(a));require(page.title()==titles[one])
                                page.go_forward();page.wait_for_url(same(b));require(page.title()==titles[two])
                            check('document title Back Forward restoration',title_history,**dimensions)
                            check('no JavaScript errors',lambda:require(not errors),**dimensions)
                        finally:context.close()
                for width in (1280,390):
                    context=browser.new_context(java_script_enabled=False,viewport={'width':width,'height':760})
                    if external_proofs:context.route('https://core.invalid/**',intercept)
                    page=context.new_page()
                    page.set_default_timeout(5000)
                    try:
                        def fallback():
                            page.goto(url)
                            links=page.locator('#compilation-units + ul a[target="document-content"]')
                            require(links.count()>=1)
                            link=links.nth(1) if links.count()>1 else links.first
                            name=link.inner_text();link.click()
                            page.frame_locator('iframe').get_by_role('heading',name=name,exact=True).wait_for()
                        check('JavaScript-disabled native navigation',fallback,width=width)
                        def static_titles():
                            page.goto(url);require(page.title()==titles['api/index.html'])
                            link=page.locator('#compilation-units + ul a[target="document-content"]').first
                            name=link.inner_text();link.click()
                            page.frame_locator('iframe').get_by_role('heading',name=name,exact=True).wait_for()
                            require(page.frame(name='document-content').title()==titles[package_pages[name]])
                        check('JavaScript-disabled document titles',static_titles,width=width)
                        if external_proofs:
                            def external_fallback():
                                page.goto(url);page.locator('#compilation-units + ul a').first.click()
                                frame=page.frame(name='document-content')
                                link=frame.locator('a.type-reference[href^="https://"]').first
                                target=link.get_attribute('href');link.click();frame.wait_for_url(target)
                                require(frame.locator('[id="'+external_proofs[target]['anchor']+'"]').count()==1)
                            check('JavaScript-disabled pinned external link',external_fallback,width=width)
                    finally:context.close()
                if configuration.get('generic_instances'):
                    generic_checks(browser,workspace,url,check,require)
                if configuration.get('guides', {}).get('mode', '').startswith('authored-'):
                    authored_checks(browser, workspace, url, check, require)
            finally:browser.close()
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
    report['status']='pass' if all(x['status']=='pass' for x in report['checks']) else 'fail'
    report['not_qualified']=['screen-reader audit','touch-device interaction',
                             'real external HTTPS hosting','visual design review']
    return report


def authored_checks(browser, workspace, api_url, check, require):
    """Visit every authored page/fragment and every source-backed API target.

    The native publication verifier reconstructs all links before browser checks.
    These checks do not certify a screen reader or an actual hosted deployment.
    """
    from ada_gnatdoc_enhancer.config import load
    from ada_gnatdoc_enhancer.metadata import Document
    from ada_gnatdoc_enhancer.pipeline import verify
    from ada_gnatdoc_enhancer.validation import Page
    config = load(workspace/'first', 'qualification.toml')
    site = workspace/'first/_site'; verify(config, site)
    data = json.loads((config.root/config.guide_manifest).read_text())
    labels = {e['path']: e['label'] for e in data['guides']}
    root_url = urljoin(api_url, '../')
    pages = ['index.html', *(e['path'] for e in data['guides'])]
    for width in (1280, 390):
        for theme in ('light', 'dark'):
            for javascript in (True, False):
                context = browser.new_context(viewport={'width': width, 'height': 760},
                    color_scheme=theme, java_script_enabled=javascript)
                page = context.new_page(); page.set_default_timeout(5000)
                errors, assets = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: assets.append(response.url) if response.status >= 400 else None)
                try:
                    for path in pages:
                        destination = urljoin(root_url, path)
                        parsed = Page((site/path).read_text())
                        dimensions = {'width': width, 'theme': theme, 'javascript': javascript, 'page': path}
                        def visible():
                            response = page.goto(destination)
                            require(response.status == 200 and page.locator('h1').count() == 1)
                            require(page.locator('script').count() == 0)
                            require(page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth+2'))
                            require(page.locator('main').is_visible())
                        check('authored page visible no scripts or outer overflow', visible, **dimensions)
                        def document_metadata():
                            # The browser's title must equal the author-provided (or
                            # authored-Markdown generated) title parsed from the page.
                            document = Document((site/path).read_text())
                            page.goto(destination)
                            require(page.title() == document.titles[0] and bool(page.title().strip()))
                            if config.guides == 'authored-markdown' and path in labels:
                                require(page.title() == labels[path] + ' — ' + data['title_suffix'])
                            require(page.evaluate('() => [document.documentElement.lang, document.characterSet]') ==
                                    [document.langs[0][0], 'UTF-8'])
                        check('authored document title and language', document_metadata, **dimensions)
                        def navigation():
                            for entry in data['guides']:
                                target = urljoin(root_url, entry['path'])
                                links = page.locator('a').evaluate_all('(es) => es.map(e => e.href)')
                                require(target in links)
                            require(urljoin(root_url, 'api/index.html') in
                                    page.locator('a').evaluate_all('(es) => es.map(e => e.href)'))
                            if path == 'index.html':
                                for entry in data['guides']:
                                    page.goto(destination)
                                    link = page.locator('a[href="' + entry['path'] + '"]').first
                                    link.click(); page.wait_for_url(urljoin(root_url, entry['path']))
                                    require(page.locator('h1').count() == 1)
                                    page.go_back(); page.wait_for_url(destination)
                                    page.go_forward(); page.wait_for_url(urljoin(root_url, entry['path']))
                                page.goto(destination)
                        check('all approved guides and API browser navigable', navigation, **dimensions)
                        for fragment in parsed.ids:
                            def direct_fragment():
                                page.goto(destination + '#' + fragment)
                                require(page.locator('[id="' + fragment + '"]').count() == 1)
                                require(page.locator(':target').get_attribute('id') == fragment)
                            check('authored direct fragment', direct_fragment, fragment=fragment, **dimensions)
                        api_links = sorted(set(link for link in parsed.links if
                            __import__('re').fullmatch(r'(?:\.\./)?api/[a-f0-9]{64}\.html(?:#[a-f0-9]{64})?', link)))
                        for target in api_links:
                            def api_click():
                                page.goto(destination)
                                link = page.locator('a[href="' + target + '"]').first
                                link.click(); page.wait_for_url(urljoin(destination, target))
                                require(page.locator('h1').count() == 1)
                                fragment = urlsplit(target).fragment
                                if fragment:
                                    require(page.locator('h4[id="' + fragment + '"]').count() == 1)
                                page.go_back(); page.wait_for_url(destination)
                                page.go_forward(); page.wait_for_url(urljoin(destination, target))
                            check('authored source-verified API click anchor Back Forward', api_click,
                                  target=target, **dimensions)
                        def keyboard():
                            page.goto(destination)
                            link = page.locator('a').first; link.focus()
                            require(link.evaluate('(e) => e === document.activeElement'))
                            page.keyboard.press('Tab')
                            focused = page.locator(':focus')
                            require(focused.count() == 1 and focused.evaluate(
                                '(e) => getComputedStyle(e).outlineStyle !== "none"'))
                            target = focused.get_attribute('href')
                            if target and not urlsplit(target).scheme and urljoin(destination, target) != page.url:
                                with page.expect_navigation(wait_until='load'):
                                    page.keyboard.press('Enter')
                                expected = urljoin(destination, target)
                                if javascript and expected == urljoin(root_url, 'api/index.html'):
                                    # The API shell initializes its package query
                                    # before wait_for_url observes the destination.
                                    # Still require the exact initialized identity.
                                    from urllib.parse import urlencode
                                    first_package = page.locator('#compilation-units + ul a').first.inner_text()
                                    expected += '?' + urlencode({'package': first_package})
                                    require(page.locator('#package-navigation').is_visible())
                                page.wait_for_url(expected)
                                page.goto(destination)
                            for table in page.locator('.table-scroll').all():
                                require(table.evaluate('(e) => e.clientWidth <= innerWidth+2'))
                        check('authored keyboard focus and responsive tables', keyboard, **dimensions)
                        if parsed.package_entries:
                            def directory():
                                page.goto(destination)
                                entries = page.locator('[data-package-entry]')
                                require(entries.count() == sum(len(g['packages']) for g in data['groups']))
                                require([x.inner_text() for x in page.locator(
                                    'section[aria-label="Public package directory"] h3').all()] ==
                                    [g['label'] for g in data['groups']])
                            check('complete grouped package directory', directory, **dimensions)
                        check('authored no page errors or broken assets', lambda: require(not errors and not assets), **dimensions)
                finally:
                    context.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--source-sha', help='Exact pinned consumer source revision tested')
    args=parser.parse_args()
    result=run(args.workspace, args.source_sha)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    raise SystemExit(0 if result['status']=='pass' else 2)