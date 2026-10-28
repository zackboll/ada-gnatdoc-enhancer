/* Authentic local artifacts only. Oracle is independently source/native bound.
 * No interception/substitution. The HTTP gate delays original file responses. */
'use strict';
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const assert=require('node:assert/strict');
const workspace=process.env.GNATDOC019_WORKSPACE;
const output=process.env.GNATDOC019_REPORT;
assert(workspace && output);
const report={checks:[],traces:[],errors:[],requests:[],synthetic_pageshow_is_not_bfcache:true};
const norm=s=>s.replace(/\s+/g,' ').trim();
let gate=null;
const server=http.createServer(async(req,res)=>{
  const relative=decodeURIComponent(new URL(req.url,'http://local').pathname).slice(1);
  if(relative==='favicon.ico'){res.writeHead(204);res.end();return;}
  const file=path.resolve(workspace,relative);
  if (!file.startsWith(path.resolve(workspace)+path.sep)) {res.writeHead(403);res.end();return;}
  report.requests.push({url:req.url,delayed:!!gate && relative===gate.path});
  if(gate && relative===gate.path){gate.enter();await gate.promise;}
  try {
    const data=fs.readFileSync(file);
    res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.json')?'application/json':'text/html');
    res.setHeader('Cache-Control','no-store');res.end(data);
  } catch(e){res.writeHead(404);res.end('Not found');}
});
const save=()=>fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const host='http://127.0.0.1:'+server.address().port+'/';
  const browser=await chromium.launch({executablePath:process.env.CHROME||'/usr/bin/google-chrome',headless:true});
  report.browser=browser.version();
  try {
    for(const label of ['historical-imgproc','current-imgproc','core']) {
      const oracle=JSON.parse(fs.readFileSync(path.join(workspace,label,'oracle.json')));
      for(const width of [1280,390]) for(const colorScheme of ['light','dark']) for(const javaScriptEnabled of [true,false]) {
        const dims={label,width,colorScheme,javaScriptEnabled};
        const context=await browser.newContext({viewport:{width,height:900},colorScheme,javaScriptEnabled});
        await context.tracing.start({screenshots:true,snapshots:true,sources:true});
        const page=await context.newPage();const errors=[];
        page.on('pageerror',e=>errors.push({type:'pageerror',message:e.message}));
        page.on('console',m=>{if(m.type()==='error')errors.push({type:'console',message:m.text()});});
        const base=host+label+'/candidate/api/';
        const outer=d=>base+'index.html?'+new URLSearchParams({package:d.package,declaration:d.href.split('#')[1]});
        async function rendering(p=page) {
          await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
        }
        async function native(p,d,event,checkOuter=true) {
          if(javaScriptEnabled && checkOuter)await p.waitForURL(outer(d));
          const f=p.frame({name:'document-content'});assert(f,'missing iframe');
          await f.waitForURL(base+d.href);await f.waitForLoadState('load');
          const heading=f.locator('h4[id="'+d.href.split('#')[1]+'"]');await heading.waitFor({state:'attached'});
          assert.equal(await heading.count(),1);assert.equal(await heading.innerText(),d.name);
          assert.equal(norm(await heading.locator('xpath=following-sibling::pre[1]').innerText()),norm(d.native_profile));
          // Playwright evaluation observes geometry even with site JS disabled;
          // it does not execute the router or create native anchor behavior.
          if(javaScriptEnabled)await rendering(p);
          const s=await heading.evaluate(e=>{
            const r=e.getBoundingClientRect();return {rectangle:r.toJSON(),viewport:{width:innerWidth,height:innerHeight},
              scroll:{x:scrollX,y:scrollY},iframeUrl:location.href,readyState:document.readyState,
              visible:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.left<innerWidth};
          });
          Object.assign(s,dims,{event,outerUrl:p.url(),target:d,historyLength:await p.evaluate(()=>history.length),errors:[...errors]});
          report.traces.push(s);assert(s.visible,'correct approved declaration and fragment but outside iframe viewport');
          return f;
        }
        async function check(name,fn) {
          try{await fn();report.checks.push({...dims,name,status:'pass'});}
          catch(e){report.checks.push({...dims,name,status:'fail',reason:String(e)});}
          save();
        }
        await page.goto(base+'index.html');
        const hrefs=await page.locator('.side-navigation a[target="document-content"]').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
        let selected;
        if(label==='core')selected=['OpenCV.Core','OpenCV.Core.Sparse'].map(pkg=>oracle.find(d=>d.package===pkg&&hrefs.includes(d.href)));
        else selected=oracle.filter(d=>d.name==='Filter_2D');
        assert(selected.length===2 && selected.every(Boolean));const [a,b]=selected;
        const sidebar=d=>page.locator('.side-navigation a[href="'+d.href+'"]').first();
        if(label!=='core')await check('non-overloaded-operation',async()=>{
          const d=oracle.find(d=>d.overloads===1 && /^(function|procedure)\b/.test(d.native_profile));
          assert(d);await sidebar(d).click();await native(page,d,'normal-operation');
        });
        await check('genuine-sidebar-normal-or-overload-1',async()=>{await sidebar(a).click();await native(page,a,'sidebar-a');});
        await check('genuine-sidebar-other-package-or-overload-2',async()=>{await sidebar(b).click();await native(page,b,'sidebar-b');});
        if(!javaScriptEnabled) {
          await check('native-back-forward',async()=>{
            // Same-document iframe history does not fire an outer load. Invoke
            // actual joint-history traversal, then assert the native destination.
            await page.evaluate(()=>history.back());await native(page,a,'native-back',false);
            await page.evaluate(()=>history.forward());await native(page,b,'native-forward',false);
          });
          await check('native-direct-fragment',async()=>{
            await page.goto(base+a.href);const h=page.locator('h4[id="'+a.href.split('#')[1]+'"]');await h.waitFor({state:'attached'});
            assert.equal(norm(await h.locator('xpath=following-sibling::pre[1]').innerText()),norm(a.native_profile));
            const r=await h.boundingBox();assert(r && r.y>=0 && r.y+r.height<=900);
          });
        } else {
          await check('real-repeated-back-forward-no-extra-entries',async()=>{
            const n=await page.evaluate(()=>history.length);
            for(let i=0;i<3;i++){await page.goBack();await native(page,a,'back-'+i);await page.goForward();await native(page,b,'forward-'+i);}
            assert.equal(await page.evaluate(()=>history.length),n);
          });
          await check('reload-visible',async()=>{await page.reload();await native(page,b,'reload');});
          await check('fresh-tab-exact-bookmark-visible',async()=>{const p=await context.newPage();try{await p.goto(outer(b));await native(p,b,'fresh-tab');}finally{await p.close();}});
          await check('same-url-back-stale-scroll',async()=>{
            const f=page.frame({name:'document-content'});await f.evaluate(()=>scrollTo(0,0));
            await page.getByRole('link',{name:'Compilation Units',exact:true}).click();
            await page.goBack();await native(page,b,'same-url-back');
          });
          await check('pageshow-probe-not-bfcache-no-history',async()=>{
            await page.frame({name:'document-content'}).evaluate(()=>scrollTo(0,0));const n=await page.evaluate(()=>history.length);
            await page.evaluate(()=>dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
            await native(page,b,'pageshow-probe');assert.equal(await page.evaluate(()=>history.length),n);
          });
          await check('same-selection-reveal-no-history',async()=>{
            await page.frame({name:'document-content'}).evaluate(()=>scrollTo(0,0));const n=await page.evaluate(()=>history.length);
            await sidebar(b).click();await native(page,b,'same-selection');assert.equal(await page.evaluate(()=>history.length),n);
          });
          await check('cross-origin-frame-cannot-grant-authority',async()=>{
            const foreign=base.replace('127.0.0.1','localhost')+a.href;
            await page.evaluate(url=>document.querySelector('iframe').contentWindow.location.replace(url),foreign);
            await page.frame({name:'document-content'}).waitForURL(foreign);
            const n=await page.evaluate(()=>history.length);
            await sidebar(b).click();await native(page,b,'foreign-frame-approved-recovery');
            assert.equal(await page.evaluate(()=>history.length),n);
          });
          await check('iframe-native-approved-link',async()=>{
            const f=page.frame({name:'document-content'});const links=await f.locator('a[href]').evaluateAll(es=>es.map(e=>e.getAttribute('href')));
            const link=links.find(h=>oracle.some(d=>hrefs.includes(d.href)&&new URL(h,f.url()).href===base+d.href));
            assert(link,'no genuine approved native link');const d=oracle.find(d=>new URL(link,f.url()).href===base+d.href);
            await f.locator('a[href="'+link+'"]').first().click();await native(page,d,'iframe-native');
          });
          await check('wrong-owner-existing-native-fragment-falls-back-package',async()=>{
            const foreign=label==='core'?b:JSON.parse(fs.readFileSync(path.join(workspace,'core/oracle.json'))).find(d=>d.name==='Mat');
            await page.goto(base+'index.html?'+new URLSearchParams({package:a.package,declaration:foreign.href.split('#')[1]}));
            assert.equal(new URL(page.url()).searchParams.get('declaration'),null);
            const f=page.frame({name:'document-content'});await f.waitForURL(base+a.href.split('#')[0]);
            assert.equal(await f.locator('h1').innerText(),a.package);
          });
          await check('delayed-authentic-iframe-superseded-selection',async()=>{
            await page.goto(outer(a));await native(page,a,'stress-start');
            await page.evaluate(()=>document.querySelector('iframe').contentWindow.location.replace('about:blank'));
            await page.frame({name:'document-content'}).waitForURL('about:blank');
            let entered,release;const enteredPromise=new Promise(r=>entered=r);
            const promise=new Promise(r=>release=r);gate={path:label+'/candidate/api/'+a.href.split('#')[0],promise,enter:entered};
            try {
              await sidebar(a).click({noWaitAfter:true});await enteredPromise;
              await sidebar(b).click({noWaitAfter:true});release();gate=null;
              await native(page,b,'stress-final');
            } finally {release();gate=null;}
          });
          await check('repeated-initialization-and-user-scroll',async()=>{
            const n=await page.evaluate(()=>history.length);await page.addScriptTag({url:base+'gnatdoc-navigation.js'});
            await page.frame({name:'document-content'}).evaluate(()=>scrollTo(0,0));await rendering();
            assert.equal(await page.frame({name:'document-content'}).evaluate(()=>scrollY),0);
            assert.equal(await page.evaluate(()=>history.length),n);
          });
        }
        report.errors.push({...dims,errors});
        await check('no-browser-errors',async()=>{assert.deepEqual(errors,[]);});
        await page.screenshot({path:output+`.${label}-${width}-${colorScheme}-js${javaScriptEnabled}.png`});
        await context.tracing.stop({path:output+`.${label}-${width}-${colorScheme}-js${javaScriptEnabled}.zip`});
        await context.close();
      }
    }
  } finally {
    await browser.close();server.close();report.totals={pass:report.checks.filter(c=>c.status==='pass').length,fail:report.checks.filter(c=>c.status==='fail').length};save();console.log(report.totals);
    if(report.totals.fail)process.exitCode=1;
  }
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});