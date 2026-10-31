import functools,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from ada_gnatdoc_enhancer.examples import code
from ada_gnatdoc_enhancer.qualification import hashes
root=Path('/tmp/gnatdoc028/token-browser');root.mkdir()
text='''procedure Example is
   S : String := "begin < &";
   C : Character := '<';
   N : Float := 16#F.F#E+1 + 1.5E-2;
begin
   -- Mat and begin remain inert.
   Inspect (S'Access, S'Length, S'First);
end Example;
'''
(root/'tokens.html').write_text('<!doctype html><html><head><link rel="stylesheet" href="examples.css"></head><body><pre class="ada-example" tabindex="0"><code>'+code(text)+'</code></pre></body></html>')
(root/'examples.css').write_bytes(Path('/tmp/gnatdoc028/source/src/ada_gnatdoc_enhancer/assets/gnatdoc-examples.css').read_bytes())
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}/'
result=dict(scope='supplemental synthetic all-token browser control; authentic consumer controls are separate',cases=[],errors=[],external_requests=[])
try:
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for width in (1280,390):
   for theme in ('light','dark'):
    for js in (True,False):
     ctx=browser.new_context(viewport=dict(width=width,height=900),color_scheme=theme,java_script_enabled=js,permissions=['clipboard-read','clipboard-write'])
     def route(r):
      if not r.request.url.startswith(base):result['external_requests'].append(r.request.url);r.abort()
      else:r.continue_()
     ctx.route('**/*',route);page=ctx.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)));page.goto(base+'tokens.html')
     pre=page.locator('pre');assert pre.text_content()==text
     colors={}
     for token in ('keyword','string','character','number','attribute','comment','operator'):
      span=page.locator('.ada-'+token).first;assert span.is_visible();colors[token]=span.evaluate('(e)=>getComputedStyle(e).color');assert colors[token]!=pre.evaluate('(e)=>getComputedStyle(e).color')
     pre.evaluate('(e)=>{const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r)}');assert page.evaluate('getSelection().toString()')==text;page.keyboard.press('Control+c');assert page.evaluate('navigator.clipboard.readText()')==text
     assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
     file=f'tokens-{width}-{theme}-js{int(js)}.png';page.screenshot(path=str(root/file));result['cases'].append(dict(width=width,height=900,theme=theme,javascript=js,colors=colors,exact_text=True,clipboard=True,screenshot=file));ctx.close()
  browser.close()
 assert not result['errors'] and not result['external_requests'];result['status']='passed'
finally:
 server.shutdown();thread.join();server.server_close();(root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
