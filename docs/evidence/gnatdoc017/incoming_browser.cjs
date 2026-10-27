/* Exhaustive real-Core click qualification. Expected occurrences and summary
 * links come from the independent unchanged-consumer source/native ledger. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const assert=require('node:assert/strict'),fs=require('node:fs');
const ledger=JSON.parse(fs.readFileSync(process.env.INSTANCE_LEDGER));
const base=process.env.DOC_URL, traces=[];
const exact=name=>new RegExp('^'+name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$','i');
async function summary(page,row,enabled) {
  const frame=page.frame({name:'document-content'});
  await frame.waitForFunction(url=>location.href===url,new URL(row.destination_page+'#'+row.summary_anchor,base).href);
  const section=frame.locator('#instance-members-summary');await section.waitFor();
  const text=await section.textContent();
  assert.ok(text.toLowerCase().includes(row.template));assert.ok(text.includes(row.actual_type));
  const argumentsTable=await section.locator('table').first().locator('tbody tr').evaluateAll(rows=>
    Object.fromEntries(rows.map(row=>[row.querySelector('th').textContent,row.querySelector('td').textContent])));
  const dimensions=row.dimensions.length===1?['Length']:['Row_Count','Column_Count'];
  for(let i=0;i<dimensions.length;i++)
    assert.equal(argumentsTable[dimensions[i]],String(row.dimensions[i]));
  assert.equal(await frame.locator('h4').count(),0);
  await frame.waitForFunction(()=>{const r=document.getElementById('instance-members-summary')?.getBoundingClientRect();return r&&r.top>=-1&&r.top<innerHeight});
  if(enabled) {
    assert.equal(new URL(page.url()).searchParams.get('package').toLowerCase(),row.identity.slice(0,row.identity.lastIndexOf('.')));
    assert.equal(new URL(page.url()).searchParams.has('symbol'),false);
    assert.equal(new URL(page.url()).searchParams.has('declaration'),false);
    assert.equal(new URL(page.url()).hash,'#instance-members-summary');
  }
}
async function incoming(page,row,enabled) {
  await page.goto(base+'?package='+row.source_package);
  if(!enabled) await page.getByRole('link',{name:exact(row.source_package)}).click();
  const frame=page.frame({name:'document-content'});
  await frame.locator('[id="'+row.source_anchor+'"] + pre').waitFor();
  assert.equal(await frame.locator('[id="'+row.source_anchor+'"] + pre').textContent(),row.native_profile);
  const links=frame.locator('[id="'+row.source_anchor+'"] + pre a[data-type="'+row.identity+'"]');
  const data=await links.evaluateAll(nodes=>nodes.map(a=>{
    const code=a.closest('code'),r=document.createRange();r.setStart(code,0);r.setEndBefore(a);
    return {start:r.toString().length,end:r.toString().length+a.textContent.length,href:a.getAttribute('href'),text:a.textContent};
  }));
  const index=data.findIndex(x=>x.start===row.native_type_span[0]&&x.end===row.native_type_span[1]);
  assert.ok(index>=0,JSON.stringify({row:row.occurrence,data}));
  assert.equal(data[index].href,row.shared.url);assert.equal(data[index].text,row.type_mark);
  await links.nth(index).click();await summary(page,row,enabled);
  traces.push({occurrence:row.occurrence,identity:row.identity,source_anchor:row.source_anchor,
    span:row.native_type_span,outer:page.url(),frame:page.frame({name:'document-content'}).url(),enabled});
}
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME,headless:true});
 try {
  const rows=ledger.occurrences;assert.equal(rows.length,242);assert.equal(ledger.missing.length,0);
  const representatives=[...new Map(rows.map(r=>[r.identity,r])).values()];assert.equal(representatives.length,25);
  for(const width of [1280,390])for(const colorScheme of ['light','dark'])for(const enabled of [true,false]) {
   const context=await browser.newContext({viewport:{width,height:900},colorScheme,javaScriptEnabled:enabled});
   const page=await context.newPage();page.setDefaultTimeout(20000);const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!m.location().url.endsWith('/favicon.ico'))errors.push(m.text())});
   // Every occurrence is actually clicked in the desktop/light JS campaign;
   // every target and profile family is repeated in all other environments.
   const campaign=width===1280&&colorScheme==='light'&&enabled?rows:representatives;
   for(const row of campaign) {
    await incoming(page,row,enabled);
    if(enabled&&campaign===representatives) {
      const bookmark=page.url();await page.reload();await summary(page,row,true);
      await page.getByRole('link',{name:'OpenCV.Core',exact:true}).click();
      await page.frameLocator('iframe').locator('h1',{hasText:/^OpenCV.Core$/}).waitFor();
      await page.goBack();await summary(page,row,true);await page.goForward();
      await page.frameLocator('iframe').locator('h1',{hasText:/^OpenCV.Core$/}).waitFor();
      await page.goto(bookmark);await summary(page,row,true);
    }
    // Check every approved summary-internal destination by clicking it, not
    // merely checking that its fragment occurs somewhere in the output.
    if(enabled&&campaign===rows&&representatives.includes(row)) {
      const bookmark=page.url();
      for(const link of row.summary_links) {
        const target=page.frameLocator('iframe').locator('#instance-members-summary a').filter({hasText:exact(link.label)});
        assert.equal(await target.getAttribute('href'),link.url);await target.click();
        const f=page.frame({name:'document-content'});
        await f.waitForFunction(url=>location.href===url,new URL(link.url,base).href);
        const fragment=new URL(link.url,base).hash;
        if(fragment) await f.locator('h4:target').waitFor();else await f.locator('h1').waitFor();
        await page.goto(bookmark);await summary(page,row,true);
      }
    }
   }
   if(enabled) {
    const row=representatives[0];await incoming(page,row,true);
    const outer=page.url();await page.evaluate(url=>document.querySelector('iframe').contentWindow.location.replace(url),base.replace('127.0.0.1','localhost'));
    await page.waitForTimeout(150);assert.equal(page.url(),outer);
    await page.goto(outer);await summary(page,row,true);
    for(const identity of representatives.map(r=>r.identity)) {
      await page.goto(base+'?symbol='+identity);await page.frameLocator('iframe').locator('h1',{hasText:/^OpenCV.Core$/}).waitFor();
      assert.equal(new URL(page.url()).searchParams.has('symbol'),false);
    }
   }
   assert.deepEqual(errors,[]);await context.close();console.log(`PASS ${width}px ${colorScheme} JS=${enabled}: ${campaign.length} incoming clicks; 25 separate summaries/native-symbol exclusions`);
  }
  fs.writeFileSync(process.env.BROWSER_REPORT,JSON.stringify({revision:ledger.revision,browser:browser.version(),exhaustive_occurrences:242,targets:25,traces},null,2)+'\n');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
