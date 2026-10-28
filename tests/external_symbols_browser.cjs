/* GNATDOC-018 real Chromium campaign. No interception or publisher modification.
 * GNATDOC018_WORKSPACE is qualify_external_symbols.py output; CHROME and
 * PLAYWRIGHT_MODULE identify installed browser tools; GNATDOC018_REPORT is new.
 */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const crypto = require('node:crypto');

(async () => {
  const root = path.resolve(process.env.GNATDOC018_WORKSPACE);
  const oracle = JSON.parse(fs.readFileSync(path.join(root, 'browser-oracle.json')));
  const report = {requestInterception: false, publisherModified: false, migrationApproved: false,
    assertions: [], responses: [], failures: []};
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
  // BFCache synthetic response events do not expose body bytes through CDP.
  // Exercise real history traversal with fresh network responses, not fabricated
  // body evidence; this flag changes no publisher/consumer code or responses.
  const browser = await chromium.launch({executablePath: process.env.CHROME, headless: true,
    args: ['--disable-back-forward-cache']});
  report.backForwardCache = false;
  report.browser = browser.version();
  const hash = data => crypto.createHash('sha256').update(data).digest('hex');
  try {
    for (const width of [1280, 390]) for (const colorScheme of ['light', 'dark'])
      for (const javaScriptEnabled of [true, false]) {
        const campaign = `${width}-${colorScheme}-js${javaScriptEnabled}`;
        if (process.env.GNATDOC018_PROFILE && process.env.GNATDOC018_PROFILE !== campaign) continue;
        const context = await browser.newContext({viewport: {width, height: 900}, colorScheme, javaScriptEnabled});
        const pending = [], errors = [];
        context.on('page', page => page.on('pageerror', e => errors.push(e.stack)));
        context.on('response', response => {
          if (!response.url().startsWith(oracle.publisher_base)) return;
          pending.push((async () => {
            const name = new URL(response.url()).pathname.slice(new URL(oracle.publisher_base).pathname.length);
            assert.ok(oracle.publication_sha256[name], 'uninventoried publisher response');
            assert.ok([200, 304].includes(response.status()), 'unsuccessful publisher response');
            assert.equal(response.request().redirectedFrom(), null);
            let bytes, evidence = 'browser-response-body';
            try {
              if (response.status() === 304) throw new Error('304 conditional response has no entity body');
              bytes = await response.body();
            }
            catch (error) {
              // Chromium history/frame replacement can discard an obsolete
              // response's CDP buffer. Do not invent its bytes or suppress the
              // observation: audit that exact live URL separately and label it.
              if (!error.message.includes('No resource with given identifier') && response.status() !== 304) throw error;
              const audit = await context.request.get(response.url(), {maxRedirects: 0});
              assert.equal(audit.status(), 200); assert.equal(audit.url(), response.url());
              bytes = await audit.body(); evidence = response.status() === 304
                ? 'separate-live-HTTPS-audit-304-no-entity-body' : 'separate-live-HTTPS-audit-CDP-body-unavailable';
            }
            const sha256 = hash(bytes);
            assert.equal(sha256, oracle.publication_sha256[name], response.url());
            report.responses.push({url: response.url(), sha256, evidence});
          })().catch(e => errors.push(response.url() + ': ' + e.stack)));
        });
        const page = await context.newPage();
        const networkSession = await context.newCDPSession(page);
        await networkSession.send('Network.enable');
        await networkSession.send('Network.setCacheDisabled', {cacheDisabled: true});
        async function settled(p) {
          await p.waitForLoadState('networkidle');
          await Promise.all(pending);
          assert.deepEqual(errors, []);
        }
        async function shell(mode, occurrence) {
          await settled(page);
          await page.goto(base + mode + '/api/index.html' + (javaScriptEnabled
            ? `?package=OpenCV.Image_Processing&declaration=${occurrence.native_anchor}` : ''));
          if (!javaScriptEnabled)
            await page.locator('.content-column a').filter({hasText: /^OpenCV.Image_Processing$/}).click();
          const frame = page.frameLocator('iframe[name="document-content"]');
          await frame.locator('h1').filter({hasText: /^OpenCV.Image_Processing$/}).waitFor();
          return frame;
        }
        async function selected(p, type) {
          assert.equal(p.url(), type.stable);
          await settled(p);
          await p.waitForFunction(() => document.getElementById('package-navigation')?.dataset.ready === 'true');
          const frame = p.frame({name: 'document-content'});
          await frame.waitForURL(type.native);
          assert.equal(await frame.locator('h1').textContent(), type.identity.slice(0, type.identity.lastIndexOf('.')));
          const heading = frame.locator(`h4[id="${type.native_anchor}"]`);
          await heading.waitFor({state: 'visible'});
          assert.equal(await heading.textContent(), type.identity.split('.').pop());
          assert.equal(await heading.locator('xpath=following-sibling::pre[1]').textContent(), type.native_snippet);
          await p.waitForTimeout(100);
          const box = await heading.boundingBox();
          assert.ok(box && box.y >= -1 && box.y < 900, 'native declaration not in viewport');
          assert.equal(p.url(), type.stable);
        }
        async function fallback(p, type) {
          assert.equal(p.url(), type.stable);
          const frame = p.frame({name: 'document-content'});
          assert.equal(frame.url(), 'about:blank');
          const owner = type.identity.slice(0, type.identity.lastIndexOf('.'));
          const link = p.locator('a[target="document-content"]').filter({hasText: new RegExp('^'+owner.replaceAll('.', '\\.')+'$')});
          assert.equal(await link.count(), 1);
          await settled(p);
          // Native package fallback remains accessible; no automatic symbol claim.
        }
        for (const [identity, type] of Object.entries(oracle.types)) {
          const occurrence = oracle.occurrences.find(x => x.core_identity === identity);
          for (const mode of ['disabled', 'stable']) for (const activation of ['mouse', 'keyboard']) {
            const frame = await shell(mode, occurrence);
            const link = frame.locator(`h4[id="${occurrence.native_anchor}"] + pre a[data-type="${identity}"]`).first();
            const destination = mode === 'stable' ? type.stable : type.native;
            assert.equal(await link.getAttribute('href'), destination);
            assert.equal(await link.getAttribute('target'), '_top');
            const consumerUrl = page.url();
            if (activation === 'keyboard') { await link.focus(); await link.press('Enter'); }
            else await link.click();
            await page.waitForURL(destination);
            assert.equal(new URL(page.url()).origin, new URL(oracle.publisher_base).origin);
            if (mode === 'stable') {
              if (javaScriptEnabled) await selected(page, type); else await fallback(page, type);
              assert.equal(page.frames().length, 2); // publisher top document owns its native frame
            } else {
              assert.equal(page.frames().length, 1);
              await page.locator('h4:target').waitFor({state: 'visible'});
              assert.equal(await page.locator('h4:target + pre').textContent(), type.native_snippet);
              await settled(page);
            }
            await page.goBack(); await page.waitForURL(consumerUrl);
            await page.frameLocator('iframe[name="document-content"]').locator('h1').waitFor();
            await page.goForward(); await page.waitForURL(destination);
            if (mode === 'stable' && javaScriptEnabled) await selected(page, type);
            if (mode === 'disabled') await page.locator('h4:target').waitFor({state: 'visible'});
            await settled(page);
            report.assertions.push({campaign, identity, mode, activation, hrefExact: true,
              topLevel: true, historyRestored: true, automaticSelection: mode === 'disabled' || javaScriptEnabled});
          }
          const cdp = await context.newCDPSession(page);
          await cdp.send('Page.enable');
          const topFrame = (await cdp.send('Page.getFrameTree')).frameTree.frame.id;
          const canonicalizations = [];
          cdp.on('Page.navigatedWithinDocument', event => {
            if (event.frameId === topFrame) canonicalizations.push(event);
          });
          await settled(page);
          await page.goto(type.stable);
          if (javaScriptEnabled) await selected(page, type); else await fallback(page, type);
          assert.deepEqual(canonicalizations, [], 'canonical URL required same-document history rewrite');
          await cdp.detach();
          await page.reload();
          if (javaScriptEnabled) await selected(page, type); else await fallback(page, type);
          const fresh = await context.newPage(); await fresh.goto(type.stable);
          if (javaScriptEnabled) await selected(fresh, type); else await fallback(fresh, type);
          await fresh.close();
          if (javaScriptEnabled) {
            await page.goto(oracle.publisher_base+'api/index.html?symbol='+type.identity);
            await page.waitForURL(type.stable); await selected(page, type);
          } else {
            await page.locator('a[target="document-content"]').filter({hasText: new RegExp('^'+type.identity.slice(0,type.identity.lastIndexOf('.')).replaceAll('.', '\\.')+'$')}).click();
            await page.frame({name:'document-content'}).waitForURL(type.native.split('#')[0]);
            await settled(page);
          }
          report.assertions.push({campaign, identity, directEntry: true, reload: true, freshTab: true,
            canonicalUrlUnchanged: true, symbolOnlyAliasCanonicalizes: javaScriptEnabled,
            nativeFallbackAccessible: !javaScriptEnabled});
        }
        await Promise.all(pending); assert.deepEqual(errors, []);
        await context.close();
      }
    report.status = 'pass';
  } catch (error) { report.status = 'fail'; report.failures.push(error.stack); process.exitCode = 1; }
  finally {
    await browser.close(); await new Promise(resolve => server.close(resolve));
    fs.writeFileSync(process.env.GNATDOC018_REPORT, JSON.stringify(report, null, 2)+'\n');
  }
})();