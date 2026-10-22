/* GNATDOC-014 live HTTPS qualification; never intercepts or rewrites responses.
 * PLAYWRIGHT_MODULE=/absolute/playwright GNATDOC014_WORKSPACE=/absolute/imgproc
 * GNATDOC014_REPORT=/absolute/report.json node /absolute/this-file.cjs
 */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const crypto = require('node:crypto');

(async () => {
  const root = path.resolve(process.env.GNATDOC014_WORKSPACE);
  const proposal = JSON.parse(fs.readFileSync(path.join(root, 'proposal.json')));
  const report = {requestInterception: false, migrationApproved: false, assertions: [], failures: []};
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    if (url.pathname === '/favicon.ico') { res.writeHead(204); res.end(); return; }
    const file = path.resolve(root, '.' + decodeURIComponent(url.pathname));
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404); res.end(); return;
    }
    res.writeHead(200, {'Content-Type': {'.html': 'text/html; charset=utf-8', '.css': 'text/css',
      '.js': 'text/javascript', '.json': 'application/json'}[path.extname(file)] || 'application/octet-stream'});
    fs.createReadStream(file).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/`;
  const browser = await chromium.launch({executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: true});
  report.browser = browser.version();
  const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
  try {
    for (const width of [1280, 390]) for (const colorScheme of ['light', 'dark'])
      for (const javaScriptEnabled of [true, false]) {
        const context = await browser.newContext({viewport: {width, height: 900}, colorScheme, javaScriptEnabled});
        const page = await context.newPage();
        const errors = []; const network = [];
        page.on('pageerror', e => errors.push(e.message));
        page.on('console', m => { if (m.type() === 'error' &&
          !(m.location().url === 'https://zackboll.github.io/favicon.ico' && m.text().includes('404'))) {
          errors.push({text: m.text(), url: m.location().url});
        }});
        page.on('response', response => { if (response.status() >= 400) {
          network.push({url: response.url(), status: response.status()});
        }});
        const campaign = `${width}-${colorScheme}-js${javaScriptEnabled}`;
        async function shell(mode, occurrence) {
          await page.goto(base + mode + '/api/index.html' + (javaScriptEnabled
            ? `?package=OpenCV.Image_Processing&declaration=${occurrence.native_anchor}` : ''));
          if (!javaScriptEnabled) {
            await page.locator('.content-column a').filter({hasText: /^OpenCV.Image_Processing$/}).click();
          }
          const frame = page.frameLocator('iframe[name="document-content"]');
          await frame.locator('h1').waitFor();
          return frame;
        }
        // No opt-in: demonstrate the historical iframe behavior is preserved.
        const [firstIdentity, firstType] = Object.entries(proposal.types)[0];
        const firstOccurrence = proposal.occurrences.find(x => x.core_identity === firstIdentity);
        let frame = await shell('default', firstOccurrence);
        let link = frame.locator(`h4[id="${firstOccurrence.native_anchor}"] + pre a[data-type="${firstIdentity}"]`).first();
        assert.equal(await link.getAttribute('target'), null);
        const defaultOuter = page.url();
        await link.click();
        await page.frame({name: 'document-content'}).waitForURL(firstType.url);
        assert.equal(page.url(), defaultOuter);
        report.assertions.push({campaign, defaultIframePreserved: true});

        for (const [identity, type] of Object.entries(proposal.types)) {
          const occurrence = proposal.occurrences.find(x => x.core_identity === identity);
          // Every distinct live destination, direct address-bar entry, exact
          // artifact bytes, owner, native profile and unique visible declaration.
          await page.goto('about:blank');
          const direct = await page.goto(type.url);
          assert.equal(direct.status(), 200);
          assert.equal(direct.request().redirectedFrom(), null);
          assert.equal(hash(await direct.body()), type.hosted_page_sha256);
          assert.equal(page.url(), type.url);
          await page.locator('h4:target').waitFor({state: 'visible'});
          assert.equal(await page.locator('h4:target').textContent(), type.identity.split('.').pop());
          assert.equal((await page.locator('h1').textContent()).toLowerCase(), type.owner);
          assert.equal(await page.locator('h4:target + pre').textContent(), type.native_snippet);
          assert.equal(await page.locator(`[id="${type.native_anchor}"]`).count(), 1);
          for (const activation of ['click', 'keyboard']) {
            frame = await shell('top', occurrence);
            link = frame.locator(`h4[id="${occurrence.native_anchor}"] + pre a[data-type="${identity}"]`).first();
            assert.equal(await link.getAttribute('href'), type.url);
            assert.equal(await link.getAttribute('target'), '_top');
            const outerBefore = page.url();
            const response = page.waitForResponse(r => r.url() === type.url.split('#')[0] && r.request().isNavigationRequest());
            if (activation === 'keyboard') { await link.focus(); await link.press('Enter'); }
            else await link.click();
            await page.waitForURL(type.url);
            assert.equal(hash(await (await response).body()), type.hosted_page_sha256);
            assert.equal(page.frames().length, 1); // Core is the top document, not an Imgproc child.
            await page.locator('h4:target').waitFor({state: 'visible'});
            assert.equal(await page.locator('h4:target + pre').textContent(), type.native_snippet);
            await page.goBack();
            await page.waitForURL(outerBefore);
            frame = page.frameLocator('iframe[name="document-content"]');
            await frame.locator('h1').filter({hasText: /^OpenCV.Image_Processing$/}).waitFor();
            assert.equal(await frame.locator(`h4[id="${occurrence.native_anchor}"] + pre a[data-type="${identity}"]`).first().getAttribute('target'), '_top');
            await page.goForward();
            await page.waitForURL(type.url);
            assert.equal(page.frames().length, 1);
            await page.locator('h4:target').waitFor({state: 'visible'});
            assert.equal(await page.locator('h4:target + pre').textContent(), type.native_snippet);
            report.assertions.push({campaign, identity, activation, topLevel: true, exactFragment: true,
              artifactBytesEqual: true, backForward: true, declarationVisible: true});
          }
        }
        assert.deepEqual(network.filter(x => x.url !== 'https://zackboll.github.io/favicon.ico'), []);
        assert.deepEqual(errors, []);
        report.assertions.push({campaign, networkErrorsObserved: network, unexpectedConsoleErrors: errors});
        await context.close();
      }
    report.status = 'pass';
  } catch (error) {
    report.status = 'fail'; report.failures.push(error.stack); process.exitCode = 1;
  } finally {
    await browser.close(); await new Promise(resolve => server.close(resolve));
    fs.writeFileSync(process.env.GNATDOC014_REPORT, JSON.stringify(report, null, 2) + '\n');
  }
})();