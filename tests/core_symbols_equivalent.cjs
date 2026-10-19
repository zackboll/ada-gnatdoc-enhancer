/* Core's unchanged symbol assertions; only Search packages -> Search
 * documentation reflects the previously approved shared presentation label. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const base = process.env.DOC_URL || 'http://127.0.0.1:8071/api/index.html';
async function declaration(page, symbol) {
  const simple = symbol.slice(symbol.lastIndexOf('.') + 1);
  const frame = page.frameLocator('iframe[name="document-content"]');
  await frame.locator('h4:target').filter({hasText: new RegExp(`^${simple}$`)}).waitFor();
  assert.equal(new URL(page.url()).searchParams.get('symbol'), symbol);
  assert.match(await frame.locator('h4:target + pre').textContent(),
    new RegExp(`^(type|subtype) ${simple}\\b`));
  await page.frame({name: 'document-content'}).waitForFunction(() => {
    const r = document.querySelector('h4:target')?.getBoundingClientRect();
    if (!r) return false;
    return r.top >= 0 && r.top < innerHeight;
  });
}
(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: true});
  try {
    for (const width of [1280, 390]) {
      const page = await browser.newPage({viewport: {width, height: 900}});
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      for (const symbol of ['OpenCV.Rect', 'OpenCV.Size', 'OpenCV.Angle_Unit',
                            'OpenCV.Core.Mat', 'OpenCV.Float64_Value']) {
        await page.goto(base + '?symbol=' + symbol.toLowerCase());
        await declaration(page, symbol);
        await page.getByLabel('Search documentation').fill('Sparse');
        await declaration(page, symbol);
        await page.getByRole('button', {name: 'Clear', exact: true}).click();
        const bookmark = page.url();
        await page.reload();
        await declaration(page, symbol);
        const fresh = await browser.newPage();
        await fresh.goto(bookmark);
        await declaration(fresh, symbol);
        await fresh.close();
        await page.getByRole('link', {name: 'OpenCV.Core.Sparse', exact: true}).click();
        await page.frameLocator('iframe').locator('h1', {hasText: /^OpenCV.Core.Sparse$/}).waitFor();
        assert.equal(new URL(page.url()).searchParams.has('symbol'), false);
        await page.goBack();
        await declaration(page, symbol);
        await page.goForward();
        await page.frameLocator('iframe').locator('h1', {hasText: /^OpenCV.Core.Sparse$/}).waitFor();
      }
      await page.goto(base + '?symbol=OpenCV.Rect');
      await declaration(page, 'OpenCV.Rect');
      // Native same-page declaration clicks update the stable outer bookmark.
      await page.frameLocator('iframe').locator('a[data-type="opencv.float32_point"]').first().click();
      await declaration(page, 'OpenCV.Float32_Point');
      await page.goBack();
      await declaration(page, 'OpenCV.Rect');
      await page.goForward();
      await declaration(page, 'OpenCV.Float32_Point');
      await page.reload();
      await declaration(page, 'OpenCV.Float32_Point');
      assert.deepEqual(errors, []);
      await page.close();
      console.log(`PASS ${width}px: direct symbols/subtype/reload/fresh/history/native click`);
    }
    for (const query of ['symbol=Rect', 'symbol=OpenCV.Absent', 'symbol=OpenCV.Core.Create',
                         'symbol=OpenCV.Core.Handle', 'symbol=../index.html',
                         'symbol=https://example.com/', 'symbol=OpenCV.Rect&symbol=OpenCV.Size',
                         'symbol=OpenCV.Rect&package=OpenCV.Core',
                         'symbol=OpenCV.Rect&package=OpenCV&package=OpenCV']) {
      const page = await browser.newPage();
      await page.goto(base + '?' + query);
      await page.frameLocator('iframe').locator('h1', {hasText: /^OpenCV.Core$/}).waitFor();
      assert.equal(new URL(page.url()).searchParams.has('symbol'), false);
      assert.deepEqual(new URL(page.url()).searchParams.getAll('package'), ['OpenCV.Core']);
      assert.equal(await page.frameLocator('iframe').locator('h4:target').count(), 0);
      await page.close();
    }
    console.log('PASS invalid/ambiguous/conflicting symbol requests rejected');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });