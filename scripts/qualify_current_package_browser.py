#!/usr/bin/env python3
"""Focused Chromium checks of independently authenticated 009B MEL occurrences."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from qualify_current_package_type_links import hashes, require, write


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith('/project/'):
            self.path = path[len('/project'):]
            result = super().translate_path(self.path)
            self.path = path
            return result
        return super().translate_path(path)

    def log_message(self, *args):
        pass


def run(args):
    work = args.workspace.resolve(); output = args.output.resolve()
    require(not output.exists() and not output.is_relative_to(work),'fresh external browser output required')
    output.mkdir(parents=True)
    report = json.loads((work/'qualification.json').read_text())
    site = work/'candidate-publication-first'
    require(hashes(site)==report['candidate_sha256'],'browser publication substitution')
    ledger = json.loads((work/'complete-occurrence-ledger.json').read_text())
    additions = [r for r in ledger if r['baseline']=='plain']
    navigation = [r for r in ledger if r['declaration']=='Navigation_Report']
    require(len(additions)==9 and len(navigation)==6,'browser independent census')
    cases = []
    server = ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(site)))
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            version = browser.version
            for prefix in ('/','/project/'):
                base = 'http://127.0.0.1:'+str(server.server_port)+prefix
                for width in (1440,390):
                    for theme in ('light','dark'):
                        for javascript in (True,False):
                            context = browser.new_context(viewport={'width':width,'height':900},
                                                          color_scheme=theme,java_script_enabled=javascript)
                            page = context.new_page();page.set_default_timeout(8000)
                            errors = [];page.on('pageerror',lambda error:errors.append(str(error)))
                            page.on('console',lambda message:errors.append(message.text) if message.type=='error' else None)
                            record = {'prefix':prefix,'width':width,'theme':theme,'javascript':javascript,'occurrences':[]}
                            selected = additions+[r for r in navigation if r['baseline']=='linked']
                            for index,row in enumerate(selected):
                                source = base+'api/'+row['containing_page']+'#'+row['containing_anchor']
                                destination = base+'api/'+row['destination_page']+'#'+row['destination_anchor']
                                page.goto(source)
                                snippet = page.locator('[id="'+row['containing_anchor']+'"] + pre code')
                                require(snippet.inner_text()==row['pristine'],'browser visible declaration changed')
                                links = snippet.locator('a.type-reference')
                                if row['declaration']=='Navigation_Report':require(links.count()==6,'six Navigation_Report links')
                                # Two NED occurrences have the same identity; select by
                                # exact independently pinned decoded token offset.
                                matches = snippet.locator('a.type-reference[data-type="'+row['destination_identity']+'"]')
                                equal_rows = [r for r in selected[:index] if r['containing_anchor']==row['containing_anchor'] and
                                              r['destination_identity']==row['destination_identity']]
                                link = matches.nth(len(equal_rows))
                                require(link.inner_text()==row['spelling'],'browser type spelling changed')
                                require(link.get_attribute('href')==row['destination_page']+'#'+row['destination_anchor'],'browser destination')
                                # Keyboard access with a real Tab, not focus() alone.
                                link.focus();page.keyboard.press('Shift+Tab');page.keyboard.press('Tab')
                                require(link.evaluate('(e)=>e===document.activeElement'),'keyboard access')
                                focus = link.evaluate('(e)=>{const s=getComputedStyle(e);return {style:s.outlineStyle,width:s.outlineWidth}}')
                                require(focus['style']!='none' and focus['width']!='0px','visible keyboard focus')
                                link.click()
                                page.wait_for_url(destination)
                                require(urlsplit(page.url).fragment==row['destination_anchor'],'actual native fragment')
                                target = page.locator('[id="'+row['destination_anchor']+'"]')
                                require(target.inner_text()==row['destination_source']['name'],'actual native declaration heading')
                                require(target.locator('xpath=following-sibling::pre[1]/code').inner_text()==row['destination_source']['native'],
                                        'actual native declaration content')
                                page.reload();require(page.url==destination,'reload fragment')
                                page.go_back();require(page.url==source,'normal Back')
                                page.go_forward();require(page.url==destination,'normal Forward')
                                page.goto(destination);require(page.locator(':target').get_attribute('id')==row['destination_anchor'],'direct destination')
                                record['occurrences'].append({'declaration':row['declaration'],'component':row['component_or_formal'],
                                                              'spelling':row['spelling'],'source':source,'destination':destination,'focus':focus})
                            nav = navigation[0]
                            page.goto(base+'api/'+nav['containing_page']+'#'+nav['containing_anchor'])
                            pre = page.locator('[id="'+nav['containing_anchor']+'"] + pre')
                            scrolling = pre.evaluate('(e)=>{const old=e.scrollLeft;e.scrollLeft=10000;return {client:e.clientWidth,scroll:e.scrollWidth,moved:e.scrollLeft>old}}')
                            if width==390:require(scrolling['scroll']>scrolling['client'] and scrolling['moved'],'mobile code scrolling')
                            require(page.locator('span.ada-number').count()>0,'unchanged numeric coloring')
                            # Generated native declarations may omit source comments;
                            # require every visible comment token remains colored if present.
                            record['colored_comments'] = page.locator('span.ada-comment').count()
                            record['scrolling'] = scrolling
                            page.screenshot(path=str(output/(str(len(cases))+'-navigation.png')),full_page=False)
                            literal_page = next(p for p in (site/'api').glob('*.html') if 'class="ada-string"' in p.read_text())
                            page.goto(base+'api/'+literal_page.name)
                            literal = page.locator('span.ada-string').first
                            require(literal.count()==1 and literal.inner_text().startswith('"'),'authentic string literal coloring')
                            record['literal_page'] = literal_page.name
                            record['literal_color'] = literal.evaluate('(e)=>getComputedStyle(e).color')
                            # Ordinary declaration links stay within the iframe and
                            # do not introduce outer bookmark/history state.
                            if javascript:
                                page.goto(base+'api/index.html')
                                frame = page.frame(name='document-content')
                                require(frame is not None,'native content frame')
                                frame.goto(base+'api/'+navigation[2]['containing_page']+'#'+navigation[2]['containing_anchor'])
                                outer = page.url
                                frame.locator('[id="'+navigation[2]['containing_anchor']+'"] + pre a.type-reference').first.click()
                                require(page.url==outer,'ordinary declaration link changed outer bookmark')
                            require(not errors,'unexpected console/page errors: '+repr(errors))
                            record['errors'] = errors;cases.append(record);context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join()
    require(hashes(site)==report['candidate_sha256'],'browser modified publication')
    write(output/'browser.json',{'browser':'Chromium','version':version,'cases':cases,
          'scope':'root/project-prefix; desktop/mobile; light/dark; JS on/off; nine new and four retained Navigation_Report occurrences; not cross-browser or accessibility certification'})
    print(json.dumps({'status':'PASS','version':version,'contexts':len(cases),'occurrence_visits':sum(len(c['occurrences']) for c in cases)}))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args())