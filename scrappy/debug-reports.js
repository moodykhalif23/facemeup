let chromium;
try { ({ chromium } = require('playwright')); }
catch (_) { ({ chromium } = require('C:\\Users\\Sozuri\\.claude\\skills\\playwright\\node_modules\\playwright')); }
const fs = require('fs');
const CONFIG = { base: 'zm.yiyuan.ai', username: 'Cyrus', password: 'Zhuri' };

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 80, args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, ignoreHTTPSErrors: true });
  const page = await ctx.newPage();

  await page.goto('https://zm.yiyuan.ai/', { waitUntil: 'networkidle', timeout: 30000 });

  // English
  const lang = page.locator('.el-select').first();
  if (await lang.count()) {
    await lang.click({ force: true }); await page.waitForTimeout(400);
    for (const o of await page.locator('.el-select-dropdown__item').all()) {
      if ((await o.textContent().catch(() => '')).trim().toLowerCase() === 'english') { await o.click({ force: true }); break; }
    }
    await page.waitForTimeout(500);
  }

  // Login
  await page.locator('input[type="text"]:not([readonly])').first().fill(CONFIG.username);
  await page.locator('input[type="password"]').first().fill(CONFIG.password);
  await page.locator('button[type="submit"], button:has-text("Login")').first().click();
  try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch (_) {}
  await page.waitForTimeout(2000);

  // Go to Reports
  await page.locator('text="Reports"').first().click({ timeout: 6000 });
  try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch (_) {}
  await page.waitForTimeout(2500);

  await page.screenshot({ path: 'raw/reports-debug.png', fullPage: true });

  // All unique button/span texts
  const btns = await page.locator('button, .el-button').allTextContents();
  console.log('\nBUTTONS ON PAGE:', [...new Set(btns.map(t => t.trim()).filter(Boolean))].join(' | '));

  // Table row count
  const rows = await page.locator('.el-table__row').count();
  console.log('TABLE ROWS in DOM:', rows);

  // First visible row buttons
  const firstRow = await page.locator('.el-table__row').first().innerHTML().catch(() => 'none');
  console.log('\nFIRST ROW HTML (500 chars):\n', firstRow.substring(0, 500));

  // Try clicking the first visible "View Details" using force
  const viewBtns = page.locator('.el-table__row button, .el-table__row .el-button');
  const btnCount = await viewBtns.count();
  console.log('\nButtons inside table rows:', btnCount);
  if (btnCount > 0) {
    const texts = await viewBtns.allTextContents();
    console.log('Row button texts:', texts.slice(0, 10));
  }

  // Check for Export/Download buttons at top of page
  const topBtns = await page.locator('.el-card button, .search-bar button, [class*="header"] button, [class*="toolbar"] button').allTextContents();
  console.log('\nTop area buttons:', topBtns.map(t => t.trim()).filter(Boolean));

  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
