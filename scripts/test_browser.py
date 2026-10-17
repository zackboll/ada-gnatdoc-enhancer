#!/usr/bin/env python3
"""Optional real-browser synthetic-site qualification, using local HTTP only.

Install Playwright separately and provide a browser binary (CHROMIUM_PATH).
This is not part of the minimal package or mandatory test dependency.
"""
from __future__ import annotations
import argparse
import contextlib
import functools
import os
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ada_gnatdoc_enhancer.config import load
from ada_gnatdoc_enhancer.pipeline import enhance


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def run(fixtures:Path,profile:str):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError('Install playwright as an optional browser-test dependency') from exc
    with tempfile.TemporaryDirectory(prefix='ada-gde-browser-') as td:
        dest=Path(td)/'fixture';shutil.copytree(fixtures/profile,dest)
        config=load(dest,'project.toml');enhance(config,dest/'_site')
        handler=functools.partial(Quiet,directory=str(dest/'_site'))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_address[1]}/api/index.html'
        try:
            with sync_playwright() as p:
                opts={'headless':True}
                exe=os.environ.get('CHROMIUM_PATH')
                if exe:opts['executable_path']=exe
                browser=p.chromium.launch(**opts)
                try:
                    for width in (1280,390):
                        for theme in ('light','dark'):
                            page=browser.new_page(viewport={'width':width,'height':760},
                                                  color_scheme=theme)
                            try:
                                page.goto(base,wait_until='load')
                                controls=page.locator('#package-navigation')
                                controls.wait_for(state='visible')
                                package_links=page.locator('.side-navigation a[target="document-content"]')
                                assert package_links.count()>=3
                                search=page.locator('#package-search')
                                search.fill('Sparse')
                                assert 'result' in page.locator('#package-results').inner_text()
                                page.locator('#package-clear').click()
                                assert search.input_value()==''
                                link=page.get_by_role('link',name='OpenCV.Core.Sparse',exact=True)
                                link.click()
                                page.wait_for_url('**?package=OpenCV.Core.Sparse')
                                assert page.locator('a[aria-current="page"]').count()==1
                                page.go_back()
                                page.wait_for_url('**?package=OpenCV.Core')
                                page.goto(base+'?package=OpenCV.Core.Sparse')
                                page.wait_for_timeout(120)
                                assert page.locator('a[aria-current="page"]').inner_text()=='OpenCV.Core.Sparse'
                                frame=page.frame_locator('iframe[name="document-content"]')
                                frame.get_by_role('heading',name='OpenCV.Core.Sparse').wait_for()
                                assert frame.locator('.ada-keyword').count()>0
                                assert frame.locator('a.type-reference').count()>0
                                assert page.locator('body').evaluate('(e) => e.scrollWidth <= innerWidth+2')
                            finally:page.close()
                    # Progressive enhancement is optional: plain GNATdoc nav must work.
                    context=browser.new_context(java_script_enabled=False)
                    page=context.new_page();page.goto(base)
                    assert page.locator('.side-navigation a[target="document-content"]').count()>=3
                    page.get_by_role('link',name='OpenCV.Core.Sparse',exact=True).click()
                    page.frame_locator('iframe[name="document-content"]').get_by_role(
                        'heading',name='OpenCV.Core.Sparse').wait_for()
                    context.close()
                finally:browser.close()
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)
    return {'browser':'passed','profile':profile,'screen_widths':[1280,390],
            'color_schemes':['light','dark'],'javascript_disabled_fallback':'passed'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures',type=Path,default=Path(__file__).resolve().parents[1]/'tests/fixtures')
    parser.add_argument('--profile',choices=('core',),default='core')
    args=parser.parse_args()
    print(run(args.fixtures,args.profile))
