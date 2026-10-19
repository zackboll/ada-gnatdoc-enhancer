/* Independent real-Core browser qualification. Input ledger comes from the
 * unchanged Core source/native oracle, never from candidate HTML metadata. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.DOC_URL;
const ledger=JSON.parse(fs.readFileSync(process.env.SYMBOL_LEDGER)).legacy;
const traces=[];
async function selected(page,name) {
  const [file,anchor]=ledger[name.toLowerCase()];
  const frame=page.frame({name:'document-content'});
  // History traversal can abort Chromium's provisional child request when the
  // authoritative outer router replaces it. Assert the final exact URL and
  // declaration, not the success of that discarded network navigation.
  await frame.waitForFunction(url=>location.href===url,new URL(file+'#'+anchor,base).href);
  await frame.locator('h4:target').waitFor();
  assert.equal(await frame.locator('h4:target').textContent(),name.split('.').pop());
  assert.equal(new URL(page.url()).searchParams.get('symbol'),name);
  assert.equal(new URL(page.url()).searchParams.get('package'),name.slice(0,name.lastIndexOf('.')));
  await frame.waitForFunction(() => {
    const rect=document.querySelector('h4:target')?.getBoundingClientRect();
    return rect && rect.top>=0 && rect.top<innerHeight;
  });
  const profile=await frame.locator('h4:target + pre').textContent();
  assert.match(profile,new RegExp('^(?:type|subtype) '+name.split('.').pop()+'\\b'));
  traces.push({url:page.url(),frame:frame.url(),profile,history:await page.evaluate(()=>history.length)});
}
async function packageSelected(page,name) {
  await page.frameLocator('iframe').locator('h1',{hasText:new RegExp('^'+name.replaceAll('.','\\.')+'$')}).waitFor();
  assert.equal(new URL(page.url()).searchParams.get('package'),name);
  assert.equal(new URL(page.url()).searchParams.has('symbol'),false);
}
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.CHROME,headless:true});
  try {
    for (const width of [1280,390]) for (const colorScheme of ['light','dark']) {
      const context=await browser.newContext({viewport:{width,height:900},colorScheme});
      await context.route('**/favicon.ico',r=>r.fulfill({status:204}));
      const page=await context.newPage();const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
      for (const symbol of ['OpenCV.Rect','OpenCV.Size','OpenCV.Angle_Unit','OpenCV.Point_Array','OpenCV.Core.Mat','OpenCV.Float64_Value']) {
        await page.goto(base+'?symbol='+symbol.toLowerCase());await selected(page,symbol);
        await page.getByLabel('Search documentation').fill('Sparse');await selected(page,symbol);
        await page.getByRole('button',{name:'Clear',exact:true}).click();
        assert.equal(await page.evaluate(()=>document.activeElement.id),'package-search');
        const bookmark=page.url();await page.reload();await selected(page,symbol);
        const fresh=await context.newPage();await fresh.goto(bookmark);await selected(fresh,symbol);await fresh.close();
        await page.getByRole('link',{name:'OpenCV.Core.Sparse',exact:true}).click();await packageSelected(page,'OpenCV.Core.Sparse');
        await page.goBack();await selected(page,symbol);
        await page.goForward();await packageSelected(page,'OpenCV.Core.Sparse');
      }
      await page.goto(base+'?symbol=OpenCV.Rect&package=opencv');await selected(page,'OpenCV.Rect');
      const initialHistory=await page.evaluate(()=>history.length);
      await page.frameLocator('iframe').locator('a[data-type="opencv.float32_point"]').first().click();await selected(page,'OpenCV.Float32_Point');
      assert.equal(await page.evaluate(()=>history.length),initialHistory+1);
      await page.goBack();await selected(page,'OpenCV.Rect');await page.goForward();await selected(page,'OpenCV.Float32_Point');
      await page.reload();await selected(page,'OpenCV.Float32_Point');
      await page.frame({name:'document-content'}).evaluate(()=>scrollTo(0,0));
      await page.evaluate(()=>dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));
      await selected(page,'OpenCV.Float32_Point');
      // Older response must not win over a rapid newer package selection.
      const slow=ledger['opencv.core.mat'][0];
      await context.route('**/'+slow,async route=>{await new Promise(r=>setTimeout(r,180));await route.continue().catch(()=>{});});
      await page.evaluate(()=>{
        document.querySelector('#compilation-units + ul a[href="'+document.querySelector('#type-navigation a[data-symbol="OpenCV.Core.Mat"]').getAttribute('href').split('#')[0]+'"]').click();
        [...document.querySelectorAll('#compilation-units + ul a')].find(a=>a.textContent==='OpenCV.Core.Sparse').click();
      });
      await packageSelected(page,'OpenCV.Core.Sparse');await page.waitForTimeout(350);await packageSelected(page,'OpenCV.Core.Sparse');
      await context.unroute('**/'+slow);
      // Cross-origin iframe redirects never confer outer bookmark authority.
      const outer=page.url();
      await page.evaluate(url=>{document.querySelector('iframe').contentWindow.location.replace(url)},base.replace('127.0.0.1','localhost'));
      await page.waitForTimeout(250);assert.equal(page.url(),outer);
      await page.getByRole('link',{name:'OpenCV.Core',exact:true}).click();await packageSelected(page,'OpenCV.Core');
      const queries=['symbol=Rect','symbol=OpenCV.Absent','symbol=OpenCV.Core.Create','symbol=OpenCV.Core.Handle',
        'symbol=OpenCV.Core.Vectors.Element_Type','symbol=OpenCV.Core.Float32_Vec2.Vector',
        'symbol=OpenCV.Rect&symbol=OpenCV.Size','symbol=OpenCV.Rect&package=OpenCV.Core',
        'symbol=OpenCV.Rect&package=OpenCV&package=OpenCV','symbol=OpenCV.Rect&declaration='+ledger['opencv.rect'][1],
        'symbol=%4fpenCV.Rect','symbol=OpenCV%252eRect','symbol=/index.html','symbol=https://example.com/',
        'symbol=OpenCV.Rect&unknown=1','%73ymbol=OpenCV.Rect'];
      for (const query of queries) {
        await page.goto(base+'?'+query);await packageSelected(page,'OpenCV.Core');
        assert.equal(await page.frameLocator('iframe').locator('h4:target').count(),0);
      }
      await page.getByLabel('Search documentation').fill('NOT_A_PACKAGE');
      assert.equal(await page.locator('#package-results').textContent(),'No matching documentation.');
      await page.getByRole('button',{name:'Clear',exact:true}).click();
      assert.equal(await page.getByLabel('Search documentation').evaluate(e=>getComputedStyle(e).outlineStyle),'solid');
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.deepEqual(errors,[]);await context.close();
      console.log(`PASS ${width}px ${colorScheme}: exact symbols/fragments/scroll/history/reload/fresh/search/invalid/race/foreign frame`);
    }
    for(const width of [1280,390]) {
      const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:900}});
      const page=await context.newPage();await page.goto(base);
      assert.equal(await page.locator('#package-navigation').isVisible(),false);
      assert.equal(await page.locator('#compilation-units + ul a').count(),195);
      await page.getByRole('link',{name:'OpenCV.Core',exact:true}).click();
      await page.frameLocator('iframe').locator('h1',{hasText:/^OpenCV.Core$/}).waitFor();
      await page.getByRole('link',{name:'Tagged Types',exact:true}).click();
      await page.getByRole('link',{name:'OpenCV.Core.Mat',exact:true}).click();
      await page.frameLocator('iframe').locator('h4:target',{hasText:/^Mat$/}).waitFor();
      await context.close();console.log(`PASS ${width}px JavaScript disabled: native packages/tagged declaration`);
    }
    fs.writeFileSync(process.env.BROWSER_REPORT,JSON.stringify({browser:browser.version(),traces},null,2)+'\n');
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});