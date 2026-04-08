/**
 * scrappy/scraper.js
 * Playwright scraper for zm.yiyuan.ai Bitmoji device portal.
 * Captures: config pages, detection schema, copywriting, product efficacy, record list.
 *
 * Usage:  node scraper.js
 * Requires: npm install playwright && npx playwright install chromium
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  url: 'https://zm.yiyuan.ai/',
  username: 'Cyrus',
  password: 'Zhuri',
  rawDir: path.join(__dirname, 'raw'),
};

if (!fs.existsSync(CONFIG.rawDir)) fs.mkdirSync(CONFIG.rawDir, { recursive: true });

const captured = [];  // all API responses

function log(msg) { console.log('[' + new Date().toISOString().substring(11, 19) + '] ' + msg); }
function saveFile(name, content, ext) {
  ext = ext || 'json';
  const body = ext === 'json' ? JSON.stringify(content, null, 2) : content;
  fs.writeFileSync(path.join(CONFIG.rawDir, name + '.' + ext), body, 'utf8');
}
async function waitForIdle(page, timeout) {
  try { await page.waitForLoadState('networkidle', { timeout: timeout || 8000 }); } catch (_) {}
  await page.waitForTimeout(1200);
}
async function shot(page, name) {
  await page.screenshot({ path: path.join(CONFIG.rawDir, name + '.png'), fullPage: true });
}

async function selectEnglish(page) {
  await page.locator('.el-select').first().click({ force: true });
  await page.waitForTimeout(500);
  const opts = await page.locator('.el-select-dropdown__item').all();
  for (const o of opts) {
    if ((await o.textContent().catch(() => '')).trim().toLowerCase() === 'english') {
      await o.click({ force: true });
      await page.waitForTimeout(800);
      return;
    }
  }
}

async function humanType(el, text) {
  await el.click(); await el.fill('');
  for (const ch of text) await el.type(ch, { delay: 70 + Math.random() * 50 });
}

async function clickMenuItem(page, labels) {
  for (const label of labels) {
    const el = page.locator('text="' + label + '"').first();
    if ((await el.count()) > 0) {
      await el.click({ timeout: 4000 });
      await page.waitForTimeout(600);
      return label;
    }
  }
  return null;
}

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100, args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  // Intercept all yiyuan.ai JSON responses
  const skipExt = ['.png','.jpg','.jpeg','.gif','.css','.woff','.woff2','.ttf','.ico','.svg','.js'];
  page.on('response', async (res) => {
    const url = res.url();
    if (!url.includes('yiyuan.ai') || skipExt.some(e => url.includes(e))) return;
    let body = null;
    try {
      if ((res.headers()['content-type'] || '').includes('json')) body = await res.json().catch(() => null);
    } catch (_) {}
    if (body) captured.push({ url, status: res.status(), body, ts: new Date().toISOString() });
  });

  log('=== STAGE 0: Load and select English ===');
  await page.goto(CONFIG.url, { waitUntil: 'networkidle', timeout: 30000 });
  await selectEnglish(page);
  log('Language: English | Title: ' + await page.title());

  log('=== STAGE 1: Login ===');
  await humanType(page.locator('input[type="text"]:not([readonly])').first(), CONFIG.username);
  await page.waitForTimeout(300);
  await humanType(page.locator('input[type="password"]').first(), CONFIG.password);
  await page.waitForTimeout(400);
  await page.locator('button[type="submit"], button:has-text("Login")').first().click();
  await waitForIdle(page, 12000);
  log('Logged in → ' + page.url());
  await shot(page, 'scraper-00-dashboard');

  log('=== STAGE 2: Config → Global Numerical ===');
  await page.locator('text="Config"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await page.locator('text="global numerical"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await shot(page, 'scraper-01-global-numerical');
  saveFile('global-numerical', await page.locator('body').innerText().catch(() => ''), 'txt');

  log('=== STAGE 3: Config → Surface Detection Copywriting ===');
  for (const label of ['.el-submenu__title:has-text("Text")', 'text="Text"']) {
    try { const el = page.locator(label).first(); if (await el.count()) { await el.click({ timeout: 2000 }).catch(() => {}); break; } } catch (_) {}
  }
  await page.waitForTimeout(500);
  await page.locator('text="surface detection"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await shot(page, 'scraper-02-surface-detection');
  saveFile('surface-detection', await page.locator('body').innerText().catch(() => ''), 'txt');
  saveFile('surface-detection', await page.content(), 'html');

  log('=== STAGE 4: Config → Deep Detection Copywriting ===');
  await page.locator('text="deep detection"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await shot(page, 'scraper-03-deep-detection');
  saveFile('deep-detection', await page.locator('body').innerText().catch(() => ''), 'txt');
  saveFile('deep-detection', await page.content(), 'html');

  log('=== STAGE 5: Config → Content Settings ===');
  for (const label of ['.el-submenu__title:has-text("Other")', 'text="Other"']) {
    try { const el = page.locator(label).first(); if (await el.count()) { await el.click({ timeout: 2000 }).catch(() => {}); break; } } catch (_) {}
  }
  await page.waitForTimeout(400);
  await page.locator('text="content settings"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await shot(page, 'scraper-04-content-settings');
  saveFile('content-settings', await page.locator('body').innerText().catch(() => ''), 'txt');
  saveFile('content-settings', await page.content(), 'html');

  log('=== STAGE 6: Config → Product Efficacy ===');
  await page.locator('text="product efficacy"').first().click({ timeout: 5000 });
  await waitForIdle(page);
  await shot(page, 'scraper-05-product-efficacy');
  saveFile('product-efficacy', await page.locator('body').innerText().catch(() => ''), 'txt');
  saveFile('product-efficacy', await page.content(), 'html');

  log('=== STAGE 7: Reports → Record List ===');
  await page.locator('text="Reports"').first().click({ timeout: 5000 });
  await waitForIdle(page, 10000);
  await shot(page, 'scraper-06-records-list');
  saveFile('records-list', await page.locator('body').innerText().catch(() => ''), 'txt');

  log('=== STAGE 8: Save all API responses ===');
  saveFile('all-api-responses', captured);

  // Group by endpoint
  const epMap = {};
  for (const c of captured) {
    const base = c.url.replace(/\?.*$/, '');
    if (!epMap[base]) epMap[base] = [];
    epMap[base].push(c.body);
  }
  saveFile('endpoints', epMap);

  await shot(page, 'scraper-99-final');
  await browser.close();

  log('=== DONE === Captured ' + captured.length + ' API responses');
  log('Files saved to: ' + CONFIG.rawDir);
})();
