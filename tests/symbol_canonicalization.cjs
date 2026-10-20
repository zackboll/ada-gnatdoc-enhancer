/* GNATDOC-011R3 real-site regression. SYMBOL_ORACLE is reconstructed from
 * trusted Ada source/native input, never from the candidate's metadata. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const assert=require('node:assert/strict'),fs=require('node:fs');
const oracle=JSON.parse(fs.readFileSync(process.env.SYMBOL_ORACLE));
const base=process.env.DOC_URL,traces=[],requests=[],errors=[];
const primary=oracle.symbols[oracle.primary],secondary=oracle.symbols[oracle.secondary];
const exact=name=>new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$');
const href=row=>row.page+'#'+row.anchor;
function clean(page,owner,symbol=null,declaration=null) {
 const url=new URL(page.url());
 assert.deepEqual([...url.searchParams.entries()],symbol?
  [['package',owner],['symbol',symbol]]:declaration?
  [['package',owner],['declaration',declaration]]:[['package',owner]]);
 assert.equal(url.hash,'');assert.equal(url.origin,new URL(base).origin);
 assert.equal(url.pathname,new URL(base).pathname);
}
function trace(page,kind) {
 traces.push({kind,outer:page.url(),frame:page.frame({name:'document-content'}).url()});
}
async function packageSelected(page,name=oracle.default_package) {
 await page.locator('#package-navigation[data-ready="true"]').waitFor();
 const frame=page.frame({name:'document-content'});
 await frame.waitForURL(new URL(oracle.packages[name],base).href);
 await frame.locator('h1',{hasText:exact(name)}).waitFor();clean(page,name);
 trace(page,'package');
}
async function selected(page,name) {
 const row=oracle.symbols[name],frame=page.frame({name:'document-content'});
 await page.locator('#package-navigation[data-ready="true"]').waitFor();
 await frame.waitForURL(new URL(href(row),base).href);
 await frame.locator('[id="'+row.anchor+'"]').waitFor();
 assert.equal(await frame.locator('[id="'+row.anchor+'"]').textContent(),name.split('.').pop());
 assert.equal(await frame.locator('[id="'+row.anchor+'"] + pre').textContent(),row.native_profile);
 clean(page,row.owner,name);
 await frame.waitForFunction(anchor=>{
  const r=document.getElementById(anchor)?.getBoundingClientRect();return r&&r.top>=0&&r.top<innerHeight;
 },row.anchor);
 trace(page,'symbol');
}
async function clickType(page,name) {
 await page.frame({name:'document-content'}).locator('a.type-reference[data-type="'+name.toLowerCase()+'"]').first().click();
 await selected(page,name);
}
async function clickPackage(page,name) {
 await page.getByRole('link',{name:exact(name)}).first().click();await packageSelected(page,name);
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME,args:['--no-sandbox']});
 let failure=null;
 try {
  for(const width of [1440,390]) for(const colorScheme of ['light','dark']) {
   const context=await browser.newContext({viewport:{width,height:1000},colorScheme});
   await context.route('**/*',route=>{
    const url=new URL(route.request().url());requests.push(url.href);
    if(url.origin!==new URL(base).origin) {errors.push('foreign request '+url.href);return route.abort();}
    const relative=url.pathname.slice(new URL(base).pathname.lastIndexOf('/')+1);
    if(!oracle.api_files.includes(relative)) {errors.push('unexpected resource '+relative);return route.abort();}
    return route.continue();
   });
   const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
   // Required negative-first transition. The uncorrected merge fails here.
   await page.goto(base+'?package='+oracle.default_package+'&unknown=1');
   await page.locator('#package-navigation[data-ready="true"]').waitFor();
   trace(page,'dirty-fallback-before-clean-assertion');
   if(process.env.SCREENSHOT_DIR) await page.screenshot({path:process.env.SCREENSHOT_DIR+'/'+width+'-'+colorScheme+'.png'});
   await packageSelected(page);await clickType(page,oracle.primary);
   await page.reload();await selected(page,oracle.primary);
   const fresh=await context.newPage();await fresh.goto(page.url());await selected(fresh,oracle.primary);await fresh.close();
   // Real source-linked selection, actual declaration scrolling and history.
   await clickType(page,oracle.secondary);await page.goBack();await selected(page,oracle.primary);
   await page.goForward();await selected(page,oracle.secondary);
   await clickPackage(page,oracle.alternate_package);
   await page.goBack();await selected(page,oracle.secondary);
   await page.goForward();await packageSelected(page,oracle.alternate_package);
   const malformed=['?package='+oracle.default_package+'&unknown=1',
    '?package='+oracle.default_package+'&package='+oracle.alternate_package,
    '?symbol='+oracle.primary+'&symbol='+oracle.secondary,
    '?declaration='+primary.anchor+'&declaration='+secondary.anchor,
    '?symbol='+oracle.primary+'&declaration='+primary.anchor,
    '?package='+oracle.alternate_package+'&symbol='+oracle.primary,
    '?%70ackage='+oracle.default_package,'?symbol=%'+oracle.primary.charCodeAt(0).toString(16)+oracle.primary.slice(1),
    '?symbol='+oracle.primary+'+','?symbol='+oracle.primary+'\\',
    '?symbol=Unknown.Owner.Type','?symbol='+oracle.default_package+'.Internal.Owner',
    '?symbol='+oracle.default_package+'.Session.Raw_Handle','?symbol=../Type',
    '?symbol='+oracle.primary+'&unknown=%26symbol%3D'+oracle.secondary,
    '?package=https://example.invalid/','?package='+oracle.default_package+'#unapproved',
    '?package='+oracle.default_package+'#instance-members-summary',
    '?package='+oracle.default_package+'#%69njected',
    '?package='+oracle.default_package+'#https://example.invalid/'];
   for(const suffix of malformed) {
    await page.goto(base+suffix);await packageSelected(page);
    trace(page,'malformed-input '+suffix);
    await clickType(page,oracle.primary);await page.reload();await selected(page,oracle.primary);
   }
   await page.goto(base+'?symbol='+oracle.secondary+'#unapproved');await selected(page,oracle.secondary);
   // Source spelling is canonical; input matching remains Ada case-insensitive.
   await page.goto(base+'?symbol='+oracle.primary.toLowerCase());await selected(page,oracle.primary);
   await page.goto(base+'?package='+primary.owner+'&declaration='+primary.anchor);await selected(page,oracle.primary);
   const declaration=oracle.declaration;
   await page.goto(base+'?package='+declaration.owner+'&declaration='+declaration.anchor);
   const frame=page.frame({name:'document-content'});
   await frame.waitForURL(new URL(href(declaration),base).href);
   clean(page,declaration.owner,declaration.symbol||null,declaration.symbol?null:declaration.anchor);trace(page,'native-declaration');
   await page.reload();await frame.waitForURL(new URL(href(declaration),base).href);
   clean(page,declaration.owner,declaration.symbol||null,declaration.symbol?null:declaration.anchor);
   await clickPackage(page,oracle.default_package);
   await page.goto(base+'?package='+primary.owner+'&declaration='+'0'.repeat(64));await packageSelected(page,primary.owner);
   // Hold an older child load, select a newer package, then release it.
   let release,started;
   const held=new Promise(resolve=>release=resolve),requested=new Promise(resolve=>started=resolve);
   const delayed=new URL(oracle.packages[oracle.alternate_package],base).href;
   await page.route(delayed,async route=>{started();await held;try {await route.continue();} catch(_) {/* superseded child navigation */}});
   await page.getByRole('link',{name:exact(oracle.alternate_package)}).first().click();
   await requested;
   await page.getByRole('link',{name:exact(oracle.default_package)}).first().click();
   release();await packageSelected(page);await page.unroute(delayed);
   await clickType(page,oracle.primary);await page.reload();await selected(page,oracle.primary);
   // Keyboard activation uses the genuine native reference, not metadata links.
   await clickPackage(page,oracle.default_package);
   const keyLink=page.frame({name:'document-content'}).locator('a.type-reference[data-type="'+oracle.primary.toLowerCase()+'"]').first();
   await keyLink.focus();await keyLink.press('Enter');await selected(page,oracle.primary);
   const repeatedHistory=await page.evaluate(()=>history.length);
   await clickType(page,oracle.primary);
   assert.equal(await page.evaluate(()=>history.length),repeatedHistory);
   assert.deepEqual(errors,[]);await context.close();
   console.log(`PASS ${width}px ${colorScheme}: canonical queries, source clicks, reload/fresh tab/history, malformed input, delayed loads, keyboard`);
  }
  for(const width of [1440,390]) for(const colorScheme of ['light','dark']) {
   const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:1000},colorScheme});
   const page=await context.newPage();await page.goto(base);
   assert.equal(await page.locator('#package-navigation').isVisible(),false);
   await page.getByRole('link',{name:exact(oracle.default_package)}).first().click();
   const frame=page.frame({name:'document-content'});
   await frame.waitForURL(new URL(oracle.packages[oracle.default_package],base).href);
   await frame.locator('a.type-reference[data-type="'+oracle.primary.toLowerCase()+'"]').first().click();
   await frame.waitForURL(new URL(href(primary),base).href);
   await frame.locator('[id="'+primary.anchor+'"]').waitFor();trace(page,'javascript-disabled-native-type-reference');
   await context.close();console.log(`PASS ${width}px ${colorScheme}: JavaScript-disabled native navigation`);
  }
 } catch(e) {failure=String(e.stack||e);throw e;}
 finally {
  fs.writeFileSync(process.env.BROWSER_REPORT,JSON.stringify({revision:oracle.revision,browser:browser.version(),failure,traces,requests,errors},null,2)+'\n');
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1});