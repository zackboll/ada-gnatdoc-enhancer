/* Core's unchanged navigation assertions with ONLY the three documented shared
 * search-label/status substitutions. Original suite remains run on legacy. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.DOC_URL || 'http://127.0.0.1:8071/api/index.html';
const evidence = process.env.DOC_EVIDENCE || '/tmp/core-doc-071-screenshots';
fs.mkdirSync(evidence, {recursive: true});
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: true});
  try {
    for (const width of [1280, 390]) for (const colorScheme of ['light', 'dark']) {
      const context = await browser.newContext({viewport: {width, height: 900}, colorScheme});
      await context.route('**/favicon.ico', route => route.fulfill({status: 204}));
      const page = await context.newPage();
      const errors = [];
      const documents = [];
      page.on('request', r => { if (r.isNavigationRequest()) documents.push(r.url()); });
      page.on('pageerror', e => errors.push(e.message));
      page.on('console', m => { if (m.type() === 'error' && !m.text().includes('favicon')) errors.push(m.text()); });
      const frame = page.frameLocator('iframe');
      const expectPackage = async name => {
        await frame.locator('h1').filter({hasText: new RegExp('^' + name.replaceAll('.', '\\.') + '$')}).waitFor();
        assert.equal(await page.locator('a[aria-current="page"]').textContent(), name);
        assert.equal(new URL(page.url()).searchParams.get('package'), name);
      };
      await page.goto(base);
      await expectPackage('OpenCV.Core');
      assert.equal(documents.filter(u => /[a-f0-9]{64}\.html$/.test(u)).length, 1);
      await page.addScriptTag({url: new URL('gnatdoc-navigation.js', base).href});
      assert.equal(documents.filter(u => /[a-f0-9]{64}\.html$/.test(u)).length, 1);
      assert.notEqual(await page.evaluate(() => document.activeElement.id), 'package-search');
      const links = page.locator('#compilation-units + ul a');
      const names = await links.allTextContents();
      assert.equal(names.length, 195);
      assert.equal(await page.locator('#tagged-types + ul a').count(), 4);
      const search = page.getByLabel('Search documentation');
      await search.fill('fLoAt16_VeC2');
      assert.deepEqual(await page.locator('#compilation-units + ul li:not([hidden]) a').allTextContents(), names.filter(n => n.toLowerCase().includes('float16_vec2')));
      await expectPackage('OpenCV.Core');
      await page.getByRole('button', {name: 'Clear', exact: true}).click();
      assert.equal(await page.locator('#compilation-units + ul li:not([hidden])').count(), 195);
      await search.fill('NOT_A_PACKAGE');
      assert.equal(await page.locator('#package-results').textContent(), 'No matching documentation.');
      await search.fill('Sparse');
      await page.getByRole('link', {name: 'OpenCV.Core.Sparse', exact: true}).click();
      await expectPackage('OpenCV.Core.Sparse');
      const bookmark = page.url();
      await page.reload();
      await expectPackage('OpenCV.Core.Sparse');
      const fresh = await browser.newContext();
      const copy = await fresh.newPage();
      await copy.goto(bookmark);
      await copy.frameLocator('iframe').locator('h1').filter({hasText: /^OpenCV.Core.Sparse$/}).waitFor();
      await fresh.close();
      await page.getByRole('button', {name: 'Clear', exact: true}).click();
      await page.getByRole('link', {name: 'OpenCV.Core.Float16_Vec2_Access', exact: true}).click();
      await expectPackage('OpenCV.Core.Float16_Vec2_Access');
      await page.goBack();
      await expectPackage('OpenCV.Core.Sparse');
      await page.goForward();
      await expectPackage('OpenCV.Core.Float16_Vec2_Access');
      await frame.locator('a[data-type="opencv.core.float16_vec2.vector"]').first().click();
      await expectPackage('OpenCV.Core.Float16_Vec2');
      await frame.locator('#instance-members-summary').waitFor();
      await page.goBack();
      await expectPackage('OpenCV.Core.Float16_Vec2_Access');
      await page.goForward();
      await expectPackage('OpenCV.Core.Float16_Vec2');
      // Package restoration deliberately does not promise declaration fragments.
      await frame.locator('#instance-members-summary').waitFor();
      await frame.locator('#instance-members-summary a').filter({hasText: /^Vector$/}).click();
      await expectPackage('OpenCV.Core.Vectors');
      await page.getByRole('link', {name: 'OpenCV.Core.Float32_Matx3x3_Conversions', exact: true}).click();
      await expectPackage('OpenCV.Core.Float32_Matx3x3_Conversions');
      await frame.locator('a[data-type="opencv.core.float32_matx3x3.matrix"]').first().click();
      await expectPackage('OpenCV.Core.Float32_Matx3x3');
      await frame.locator('#instance-members-summary a').filter({hasText: /^Matrix$/}).click();
      await expectPackage('OpenCV.Core.Fixed_Matrices');
      await page.getByRole('link', {name: 'Tagged Types', exact: true}).click();
      await page.getByRole('link', {name: 'OpenCV.Core.Mat', exact: true}).click();
      await expectPackage('OpenCV.Core');
      assert.ok(new URL(page.frames()[1].url()).hash);
      await page.getByRole('link', {name: 'Compilation Units', exact: true}).click();
      await search.focus();
      assert.equal(await search.evaluate(e => getComputedStyle(e).outlineStyle), 'solid');
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await search.fill('Float16_Vec2');
      await page.screenshot({path: `${evidence}/${width}-${colorScheme}.png`});
      assert.deepEqual(errors, []);
      await context.close();
      console.log(`PASS ${width}px ${colorScheme}: search/bookmark/history/iframe/generic/tagged/focus/overflow`);
    }
    for (const request of ['unknown', '../index.html', 'https://example.com/', 'oPeNcV.cOrE']) {
      const page = await browser.newPage();
      await page.goto(base + '?package=' + encodeURIComponent(request));
      await page.frameLocator('iframe').locator('h1').filter({hasText: /^OpenCV.Core$/}).waitFor();
      assert.equal(new URL(page.url()).searchParams.get('package'), 'OpenCV.Core');
      await page.addScriptTag({url: new URL('gnatdoc-navigation.js', base).href});
      assert.equal(await page.locator('#package-navigation').count(), 1);
      await page.close();
    }
    const duplicate = await browser.newPage();
    await duplicate.goto(base + '?package=OpenCV.Core&package=OpenCV.Core.Sparse');
    await duplicate.frameLocator('iframe').locator('h1').filter({hasText: /^OpenCV.Core$/}).waitFor();
    assert.deepEqual(new URL(duplicate.url()).searchParams.getAll('package'), ['OpenCV.Core']);
    await duplicate.close();
    for (const width of [1280, 390]) {
      const context = await browser.newContext({javaScriptEnabled: false, viewport: {width, height: 900}});
      const page = await context.newPage();
      await page.goto(base);
      assert.equal(await page.locator('#package-navigation').isVisible(), false);
      await page.getByRole('link', {name: 'OpenCV.Core', exact: true}).click();
      await page.frameLocator('iframe').locator('h1').filter({hasText: /^OpenCV.Core$/}).waitFor();
      await page.getByRole('link', {name: 'Tagged Types', exact: true}).click();
      await page.getByRole('link', {name: 'OpenCV.Core.Sparse.Sparse_Mat', exact: true}).click();
      await page.frameLocator('iframe').locator('h1').filter({hasText: /^OpenCV.Core.Sparse$/}).waitFor();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await context.close();
      console.log(`PASS ${width}px JavaScript disabled: native packages/tabs/tagged links`);
    }
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });