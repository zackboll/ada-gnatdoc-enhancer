/* Real HTTP/browser qualification, never intercepted requests or synthetic CSS.
 * THEME_SITE_ROOT serves legacy/ and candidate/; THEME_EVIDENCE retains PNG/JSON.
 * Both directories must come from independently qualified current Core builds. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const base = process.env.THEME_SITE_ROOT;
const output = process.env.THEME_EVIDENCE;
const candidateDirectory = process.env.THEME_CANDIDATE || 'candidate';
const sha = 'fa265d63e73436a6a449fd16011c3db68a5430e7fa6a98ea8eb0fd6821dca9b2';
const properties = ['fontFamily','fontSize','fontWeight','lineHeight','color','backgroundColor',
  'padding','margin','display','gap','maxWidth','letterSpacing','textTransform','borderRadius',
  'borderTopWidth','borderTopColor','overflowX','tableLayout','outlineStyle','outlineWidth'];
async function inspect(page, selectors) {
  return page.evaluate(({selectors, properties}) => Object.fromEntries(selectors.map(selector => {
    const element = document.querySelector(selector);
    if (!element) throw new Error(`Missing ${selector}`);
    const style = getComputedStyle(element);
    return [selector,Object.fromEntries(properties.map(key => [key,style[key]]))];
  })), {selectors, properties});
}
async function noOverflow(page) {
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    `Horizontal overflow: ${page.url()}`);
}
(async () => {
  assert.ok(base && output, 'Explicit actual-site URL and evidence directory required');
  fs.mkdirSync(output, {recursive:true});
  const browser = await chromium.launch({executablePath:process.env.CHROME,headless:true});
  const records = [], problems = [];
  try {
    for (const width of [1280,390]) for (const colorScheme of ['light','dark'])
      for (const javaScriptEnabled of [true,false]) {
        const context = await browser.newContext({viewport:{width,height:900},colorScheme,javaScriptEnabled});
        const pair = {};
        for (const site of ['legacy','candidate']) {
          const page = await context.newPage(), requests = [], errors = [];
          page.on('request', request => {
            requests.push(request.url());
            if (!request.url().startsWith(base+'/')) errors.push('unexpected request '+request.url());
          });
          page.on('requestfailed', request => errors.push('failed '+request.url()));
          page.on('pageerror', error => errors.push(error.message));
          page.on('response', response => { if (response.status() >= 400) errors.push('HTTP '+response.status()+' '+response.url()); });
          const url = `${base}/${site==='candidate' ? candidateDirectory : site}/`;
          await page.goto(url+'index.html'); await noOverflow(page);
          const theme = await context.request.get(url+'api/gnatdoc-theme.css');
          assert.equal(crypto.createHash('sha256').update(await theme.body()).digest('hex'),sha);
          const landing = await inspect(page,['.landing','h1','.eyebrow','.lead','.api-button','.landing nav']);
          assert.equal(landing['.eyebrow'].textTransform,'uppercase');
          assert.equal(landing['.lead'].fontSize,'19.2px');
          assert.equal(landing['.api-button'].display,'inline-block');
          assert.equal(landing['.landing nav'].display,'flex');
          const contrast = await page.evaluate(() => {
            function rgb(value) { return value.match(/[\d.]+/g).slice(0,3).map(Number); }
            function luminance(color) {
              const c = rgb(color).map(n => n/255).map(n => n<=.04045 ? n/12.92 : ((n+.055)/1.055)**2.4);
              return .2126*c[0]+.7152*c[1]+.0722*c[2];
            }
            const bg = getComputedStyle(document.documentElement).backgroundColor;
            return Object.fromEntries(['.eyebrow','.lead','.api-button'].map(selector => {
              const c = getComputedStyle(document.querySelector(selector));
              const a = luminance(c.color), b = luminance(selector==='.api-button' ? c.backgroundColor : bg);
              return [selector,(Math.max(a,b)+.05)/(Math.min(a,b)+.05)];
            }));
          });
          for (const value of Object.values(contrast)) assert.ok(value>=4.5,'Readable normal-text contrast');
          await page.keyboard.press('Tab');
          const focus = await page.evaluate(() => ({text:document.activeElement.textContent,
            outline:getComputedStyle(document.activeElement).outlineWidth}));
          assert.match(focus.text,/Explore the API/); assert.equal(focus.outline,'3px');
          await page.screenshot({path:path.join(output,`${site}-${width}-${colorScheme}-${javaScriptEnabled}-landing.png`),fullPage:true});
          const guides = await page.locator('a[href^="guides/"]').evaluateAll(links => links.map(a => a.getAttribute('href')));
          assert.equal(guides.length,5);
          const guideStyles = {};
          for (const guide of guides) {
            await page.goto(url+guide); await noOverflow(page);
            const heading = await page.locator('main h1').textContent();
            guideStyles[guide] = {heading,styles:await inspect(page,['main h1','.guide-layout','.guide-nav'])};
            const fragment = await page.locator('main h2[id]').first().getAttribute('id');
            for (const table of await page.locator('.table-scroll').all())
              assert.equal(await table.evaluate(e => getComputedStyle(e).overflowX),'auto');
            await page.goto(url+guide+'#'+fragment);
            assert.equal(await page.locator(':target').count(),1);
            await page.keyboard.press('Tab');
            assert.ok(await page.evaluate(() => document.activeElement.tagName==='A'));
            if (width===390) await page.screenshot({path:path.join(output,`${site}-${colorScheme}-${javaScriptEnabled}-${guide.split('/')[1]}.png`),fullPage:true});
          }
          await page.goto(url+'api/index.html'); await noOverflow(page);
          const packageLink = page.locator('.side-navigation a').filter({hasText:/^OpenCV.Core$/}).first();
          const corePath = await packageLink.getAttribute('href');
          const vector = await page.locator('.side-navigation a').filter({hasText:/^OpenCV.Core.Float32_Vec3$/}).first().getAttribute('href');
          const summaries = await page.locator('.side-navigation a').evaluateAll(links =>
            links.filter(a => /^OpenCV.Core.(?:UInt8|Int8|UInt16|Int16|Int32|Float16|Float32|Float64)_Vec[234]$|^OpenCV.Core.Float32_Matx3x3$/.test(a.textContent))
              .map(a => a.getAttribute('href')));
          assert.equal(summaries.length,25);
          const sidebar = await inspect(page,['.side-navigation','.document-content']);
          await packageLink.focus(); await page.keyboard.press('Enter');
          await page.frameLocator('iframe').locator('h1').filter({hasText:/^OpenCV.Core$/}).waitFor();
          await page.screenshot({path:path.join(output,`${site}-${width}-${colorScheme}-${javaScriptEnabled}-api.png`),fullPage:true});
          await page.goto(url+'api/'+vector); await noOverflow(page);
          const card = await inspect(page,['.generic-instance-summary','.generic-instance-summary h2',
            '.generic-instance-summary table','.generic-instance-summary th','.generic-instance-summary td']);
          assert.equal(await page.locator('.generic-instance-summary a').count(),4);
          assert.equal(card['.generic-instance-summary'].borderTopWidth,'1px');
          await page.screenshot({path:path.join(output,`${site}-${width}-${colorScheme}-${javaScriptEnabled}-card.png`),fullPage:true});
          let summaryLinks = 0;
          for (const summaryPath of summaries) {
            await page.goto(url+'api/'+summaryPath); await noOverflow(page);
            const destinations = await page.locator('.generic-instance-summary a').evaluateAll(links => links.map(a => a.getAttribute('href')));
            summaryLinks += destinations.length;
            for (const destination of destinations) {
              await page.goto(url+'api/'+destination);
              if (destination.includes('#')) assert.equal(await page.locator('h4:target').count(),1);
              else assert.equal(await page.locator('h1').count(),1);
            }
          }
          assert.equal(summaryLinks,102);
          await page.goto(url+'api/'+corePath);
          const anchor = await page.locator('h4').filter({hasText:/^Mat$/}).first().getAttribute('id');
          await page.goto(url+'api/'+corePath+'#'+anchor); await noOverflow(page);
          const declaration = await inspect(page,['h4:target','h4:target + pre']);
          assert.equal(declaration['h4:target + pre'].overflowX,'auto');
          assert.equal(declaration['h4:target'].backgroundColor,
            colorScheme==='dark' ? 'rgb(40, 62, 91)' : 'rgb(224, 235, 250)');
          const scrollable = await page.locator('pre').evaluateAll(items => items.filter(p => p.scrollWidth>p.clientWidth).length);
          if (width===390) assert.ok(scrollable>0, 'Long signatures must scroll inside declaration blocks');
          await page.reload(); assert.equal(await page.locator('h4:target').textContent(),'Mat');
          await page.goto(url+'index.html'); await page.goBack();
          assert.equal(await page.locator('h4:target').textContent(),'Mat');
          await page.goForward(); assert.equal(await page.locator('.landing').count(),1);
          pair[site] = {landing,guideStyles,card,declaration,sidebar};
          records.push({site,width,colorScheme,javaScriptEnabled,requests,errors,focus,scrollable,contrast,summaryLinks,...pair[site]});
          assert.deepEqual(errors,[]);
          await page.close();
        }
        for (const feature of ['landing','guideStyles','card','declaration','sidebar'])
          assert.deepEqual(pair.candidate[feature],pair.legacy[feature], `${feature} computed-style parity`);
        await context.close();
      }
  } catch (error) {
    problems.push(error.stack); throw error;
  } finally {
    fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify({browser:browser.version(),records,problems},null,2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode=1; });