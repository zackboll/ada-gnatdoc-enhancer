/* GNATDOC-011R2: real source/native-qualified sites, not URL-string mocks.
 * INSTANCE_LEDGER is independently reconstructed by the unchanged Core oracle.
 * This is additive to instance_references.cjs; no older assertion is replaced. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const assert=require('node:assert/strict'),fs=require('node:fs');
const ledger=JSON.parse(fs.readFileSync(process.env.INSTANCE_LEDGER));
const base=process.env.DOC_URL, traces=[];
const exact=name=>new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$','i');
function clean(page,packageName,symbol=null,fragment='') {
  const url=new URL(page.url());
  assert.deepEqual([...url.searchParams.entries()],symbol?
    [['package',packageName],['symbol',symbol]]:[['package',packageName]]);
  assert.equal(url.hash,fragment);
  assert.equal(url.origin,new URL(base).origin);assert.equal(url.pathname,new URL(base).pathname);
}
async function packageSelected(page,name) {
  await page.locator('#package-navigation[data-ready="true"]').waitFor();
  await page.frameLocator('iframe').locator('h1',{hasText:exact(name)}).waitFor();
  clean(page,name);
  assert.equal(await page.frameLocator('iframe').locator('h4:target').count(),0);
  traces.push({kind:'package',outer:page.url(),frame:page.frame({name:'document-content'}).url()});
}
async function symbolSelected(page) {
  const frame=page.frame({name:'document-content'});
  await frame.locator('h4:target',{hasText:/^Mat$/}).waitFor();
  clean(page,'OpenCV.Core','OpenCV.Core.Mat');
  const allowed=await page.locator('#type-navigation a[data-symbol="OpenCV.Core.Mat"]').getAttribute('href');
  assert.equal(frame.url(),new URL(allowed,base).href);
  assert.match(await frame.locator('h4:target + pre').textContent(),/^type Mat is tagged private;/);
  await frame.waitForFunction(()=>{const r=document.querySelector('h4:target')?.getBoundingClientRect();return r&&r.top>=0&&r.top<innerHeight});
  traces.push({kind:'symbol',outer:page.url(),frame:frame.url()});
}
async function selectSymbol(page) {
  await page.getByRole('link',{name:'Tagged Types',exact:true}).click();
  await page.getByRole('link',{name:'OpenCV.Core.Mat',exact:true}).click();
  await symbolSelected(page);
}
async function summarySelected(page,row) {
  const frame=page.frame({name:'document-content'});
  await frame.waitForFunction(url=>location.href===url,new URL(row.destination_page+'#instance-members-summary',base).href);
  const section=frame.locator('#instance-members-summary');await section.waitFor();
  const owner=row.identity.slice(0,row.identity.lastIndexOf('.'));
  const canonical=await page.locator('#compilation-units + ul a').filter({hasText:exact(owner)}).textContent();
  clean(page,canonical,null,'#instance-members-summary');
  assert.equal((await frame.locator('h1').textContent()).toLowerCase(),owner);
  assert.equal(await frame.locator('h4').count(),0);
  const args=await section.locator('table').first().locator('tbody tr').evaluateAll(rows=>
    Object.fromEntries(rows.map(r=>[r.querySelector('th').textContent,r.querySelector('td').textContent])));
  assert.equal(args.Element_Type.split('.').pop(),row.actual_type);
  const names=row.dimensions.length===1?['Length']:['Row_Count','Column_Count'];
  for(let i=0;i<names.length;i++)assert.equal(args[names[i]],String(row.dimensions[i]));
  assert.ok((await section.textContent()).toLowerCase().includes(row.template));
  await frame.waitForFunction(()=>{const r=document.getElementById('instance-members-summary')?.getBoundingClientRect();return r&&r.top>=-1&&r.top<innerHeight});
  traces.push({kind:'summary',identity:row.identity,outer:page.url(),frame:frame.url(),arguments:args});
}
async function clickIncoming(page,row) {
  await page.getByRole('link',{name:'Compilation Units',exact:true}).click();
  await page.getByRole('link',{name:exact(row.source_package)}).click();
  const frame=page.frame({name:'document-content'}),selector='[id="'+row.source_anchor+'"] + pre';
  await frame.locator(selector).waitFor();
  assert.equal(await frame.locator(selector).textContent(),row.native_profile);
  const links=frame.locator(selector+' a[data-type="'+row.identity+'"]');
  const starts=await links.evaluateAll(nodes=>nodes.map(a=>{
    const r=document.createRange();r.setStart(a.closest('code'),0);r.setEndBefore(a);return r.toString().length;
  }));
  const index=starts.indexOf(row.native_type_span[0]);assert.ok(index>=0);
  assert.equal(await links.nth(index).getAttribute('href'),row.shared.url);
  await links.nth(index).click();await summarySelected(page,row);
}
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME,headless:true});
 let failure=null;
 try {
  const vector=ledger.occurrences.find(r=>r.identity.endsWith('.vector'));
  const matrix=ledger.occurrences.find(r=>r.identity.endsWith('.matrix'));
  assert.ok(vector&&matrix);assert.equal(ledger.public_symbols,215);
  for(const width of [1280,390])for(const colorScheme of ['light','dark']) {
   const context=await browser.newContext({viewport:{width,height:900},colorScheme});
   await context.route('**/favicon.ico',r=>r.fulfill({status:204}));
   const page=await context.newPage();page.setDefaultTimeout(15000);const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
   // A: incoming fallback must be clean before any subsequent valid click.
   await page.goto(base+'?package=OpenCV.Core&unknown=1');await packageSelected(page,'OpenCV.Core');
   await selectSymbol(page);await page.reload();await symbolSelected(page);
   await page.goBack();await packageSelected(page,'OpenCV.Core');
   await page.goForward();await symbolSelected(page);
   // Also verify canonical writers discard dirty current state, independently
   // of the initial fallback path. This does not manufacture any destination.
   await page.evaluate(()=>history.replaceState(null,'',location.href+'&unknown=2'));
   await page.getByRole('link',{name:'Compilation Units',exact:true}).click();
   await page.getByRole('link',{name:'OpenCV.Core.Sparse',exact:true}).click();await packageSelected(page,'OpenCV.Core.Sparse');
   await selectSymbol(page);await symbolSelected(page);
   // B: actual source-qualified vector AND matrix hyperlinks, never metadata clicks.
   for(const row of [vector,matrix]) {
    await page.goto(base+'?package=OpenCV.Core&unsupported=1');await packageSelected(page,'OpenCV.Core');
    await clickIncoming(page,row);await page.reload();await summarySelected(page,row);
    await page.goBack();
    await page.frameLocator('iframe').locator('[id="'+row.source_anchor+'"] + pre').waitFor();
    assert.equal(new URL(page.url()).searchParams.get('package').toLowerCase(),row.source_package);
    assert.deepEqual([...new URL(page.url()).searchParams.keys()],['package']);
    await page.goForward();await summarySelected(page,row);
    await page.getByRole('link',{name:'OpenCV.Core',exact:true}).click();await packageSelected(page,'OpenCV.Core');
    await page.goBack();await summarySelected(page,row);
   }
   // C: rejection policy unchanged; unsupported fragments confer no authority.
   const mat=await page.locator('#type-navigation a[data-symbol="OpenCV.Core.Mat"]').getAttribute('href');
   const anchor=mat.split('#')[1];
   const malformed=['?package=OpenCV.Core&package=OpenCV.Core.Sparse',
     '?symbol=OpenCV.Core.Mat&symbol=OpenCV.Rect','?package=OpenCV.Core.Sparse&unknown=1',
     '?symbol=OpenCV.Core.Mat&declaration='+anchor,'?%70ackage=OpenCV.Core.Sparse',
     '?symbol=%4fpenCV.Core.Mat','?package=OpenCV.Core#unapproved',
     '?package=OpenCV.Core#instance-members-summary','?package=OpenCV.Core#https://example.com/',
     '?package=OpenCV.Core#%69nstance-members-summary'];
   for(const suffix of malformed) {
    await page.goto(base+suffix);await packageSelected(page,'OpenCV.Core');
    await selectSymbol(page);await page.reload();await symbolSelected(page);
   }
   // D: preserve approved declaration-query interpretation (Mat canonicalizes
   // to its native symbol); unknown declaration anchors remain package-only.
   await page.goto(base+'?package=OpenCV.Core&declaration='+anchor);await symbolSelected(page);
   await page.reload();await symbolSelected(page);
   await page.goto(base+'?package=OpenCV.Core&declaration='+'0'.repeat(64));await packageSelected(page,'OpenCV.Core');
   await page.getByRole('link',{name:'Compilation Units',exact:true}).click();
   await page.evaluate(()=>{
    const links=[...document.querySelectorAll('#compilation-units + ul a')];
    links.find(a=>a.textContent==='OpenCV.Core.Sparse').click();links.find(a=>a.textContent==='OpenCV.Core').click();
   });
   await packageSelected(page,'OpenCV.Core');
   assert.deepEqual(errors,[]);await context.close();console.log(`PASS ${width}px ${colorScheme}: A symbol B vector/matrix C malformed D existing declarations/packages/rapid selection`);
  }
  for(const width of [1280,390]) {
   const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:900}});
   const page=await context.newPage();await page.goto(base);
   assert.equal(await page.locator('#package-navigation').isVisible(),false);
   await page.getByRole('link',{name:exact(vector.source_package)}).click();
   const frame=page.frame({name:'document-content'}),selector='[id="'+vector.source_anchor+'"] + pre';
   await frame.locator(selector).waitFor();
   await frame.locator(selector+' a[data-type="'+vector.identity+'"]').first().click();
   await frame.locator('#instance-members-summary').waitFor();
   assert.equal(frame.url(),new URL(vector.destination_page+'#instance-members-summary',base).href);
   assert.equal(await frame.locator('h4').count(),0);await context.close();
   console.log(`PASS ${width}px JavaScript disabled native incoming reference`);
  }
 } catch(e) {failure=String(e.stack||e);throw e;}
 finally {
  fs.writeFileSync(process.env.BROWSER_REPORT,JSON.stringify({revision:ledger.revision,browser:browser.version(),failure,traces},null,2)+'\n');
  await browser.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1});