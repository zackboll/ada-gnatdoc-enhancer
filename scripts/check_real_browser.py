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
import threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def run(workspace):
    from playwright.sync_api import sync_playwright
    handler=functools.partial(Quiet,directory=str(workspace))
    server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    report={'checks':[],'scope':'isolated real native API site; not consumer portal'}
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
                for width in (1280,390):
                    for theme in ('light','dark'):
                        page=browser.new_page(viewport={'width':width,'height':760},color_scheme=theme)
                        page.set_default_timeout(5000)
                        dimensions={'width':width,'theme':theme}
                        errors=[]
                        page.on('pageerror',lambda err:errors.append(str(err)))
                        try:
                            page.goto(url,wait_until='networkidle')
                            links=page.locator('#compilation-units + ul a')
                            names=links.all_text_contents()
                            require(len(names)>=2)
                            first,second=names[:2]
                            check('theme assets and color scheme',lambda:require(page.evaluate(
                                "() => document.styleSheets.length >= 2 && matchMedia('(prefers-color-scheme: "+theme+")').matches")),**dimensions)
                            def search():
                                box=page.locator('#package-search');box.fill(second)
                                require('result' in page.locator('#package-results').inner_text())
                                page.locator('#package-clear').click();require(box.input_value()=='')
                            check('search and clear',search,**dimensions)
                            def navigation():
                                page.get_by_role('link',name=second,exact=True).click()
                                page.wait_for_url('**?package='+second)
                                page.frame_locator('iframe').get_by_role('heading',name=second,exact=True).wait_for()
                                page.go_back();page.wait_for_url('**?package='+first)
                                page.go_forward();page.wait_for_url('**?package='+second)
                                page.goto(url+'?package='+second,wait_until='networkidle')
                                require(page.locator('a[aria-current="page"]').inner_text()==second)
                            check('package bookmark direct link Back Forward',navigation,**dimensions)
                            def category():
                                link=page.locator('#operation-navigation a').first
                                href=link.get_attribute('href');link.click()
                                frame=page.frame(name='document-content')
                                frame.wait_for_url('**/'+href)
                                require(frame.locator('[id="'+href.split('#')[1]+'"]').count()==1)
                            check('operation category real anchor',category,**dimensions)
                            check('syntax and local type links',lambda:require(
                                page.frame_locator('iframe').locator('.ada-keyword').count()>0 and
                                page.frame_locator('iframe').locator('a.type-reference').count()>0),**dimensions)
                            def keyboard():
                                page.locator('#package-search').focus();page.keyboard.press('Tab')
                                require(page.locator('#package-clear').evaluate('(e) => e === document.activeElement'))
                                require(page.locator('#package-clear').evaluate('(e) => getComputedStyle(e).outlineStyle !== "none"'))
                            check('keyboard focus and visible outline',keyboard,**dimensions)
                            check('responsive outer viewport',lambda:require(page.locator('body').evaluate(
                                '(e) => e.scrollWidth <= innerWidth+2')),**dimensions)
                            check('no JavaScript errors',lambda:require(not errors),**dimensions)
                        finally:page.close()
                for width in (1280,390):
                    context=browser.new_context(java_script_enabled=False,viewport={'width':width,'height':760})
                    page=context.new_page()
                    page.set_default_timeout(5000)
                    try:
                        def fallback():
                            page.goto(url)
                            links=page.locator('#compilation-units + ul a[target="document-content"]')
                            require(links.count()>=2)
                            name=links.nth(1).inner_text();links.nth(1).click()
                            page.frame_locator('iframe').get_by_role('heading',name=name,exact=True).wait_for()
                        check('JavaScript-disabled native navigation',fallback,width=width)
                    finally:context.close()
            finally:browser.close()
    finally:server.shutdown();server.server_close();thread.join(timeout=2)
    report['status']='pass' if all(x['status']=='pass' for x in report['checks']) else 'fail'
    report['not_qualified']=['screen-reader audit','touch-device interaction','consumer authored guides',
                             'external Core targets','visual design review']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=run(args.workspace)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    raise SystemExit(0 if result['status']=='pass' else 2)