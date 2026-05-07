/**
 * scrappy/collector.js
 * Direct API client for zm.yiyuan.ai.
 * Authenticates with the portal and fetches full record details,
 * saving each record's complete analysis payload.
 *
 * Usage:  node collector.js [--limit 50] [--page 1]
 * Output: raw/records-full.json  (array of full analysis records)
 *         raw/records-scores.json (simplified: id + all 15 metric scores)
 */
const https = require('https');
const fs = require('fs');
const path = require('path');
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (_) {
  ({ chromium } = require('C:\\Users\\Sozuri\\.claude\\skills\\playwright\\node_modules\\playwright'));
}

const CONFIG = {
  base: 'zm.yiyuan.ai',
  username: 'Cyrus',
  password: 'Zhuri',
  rawDir: path.join(__dirname, 'raw'),
  imagesDir: path.join(__dirname, 'raw', 'images'),
  pageSize: 20,
};

const args = process.argv.slice(2);
function getArg(name, fallback) {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
}
const LIMIT = parseInt(getArg('--limit', '100'));
const START_PAGE = parseInt(getArg('--page', '1'));
const SKIP_EXPORT = args.includes('--skip-export');
const CHROME_PATH = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
  || '/usr/bin/google-chrome';

if (!fs.existsSync(CONFIG.rawDir)) fs.mkdirSync(CONFIG.rawDir, { recursive: true });
if (!fs.existsSync(CONFIG.imagesDir)) fs.mkdirSync(CONFIG.imagesDir, { recursive: true });

function log(msg) { console.log('[' + new Date().toISOString().substring(11, 19) + '] ' + msg); }

function apiRequest(method, urlPath, token, formData) {
  const body = formData
    ? Object.entries(formData).map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&')
    : null;

  return new Promise((resolve, reject) => {
    const opts = {
      hostname: CONFIG.base,
      path: urlPath,
      method: method,
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': formData ? 'application/x-www-form-urlencoded;charset=UTF-8' : 'application/json',
        'locale': 'en',
        'language': 'en',
        ...(token ? { 'access_token': token } : {}),
        ...(body ? { 'Content-Length': Buffer.byteLength(body) } : {}),
      },
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch (e) { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

const apiPost = (p, tok, form) => apiRequest('POST', p, tok, form);


function extractScores(analysis) {
  if (!analysis) return null;

  function metricScore(key) {
    const m = analysis[key];
    if (!m) return { score: null, level: null, count: null };
    return {
      score: m.score !== undefined ? Number(m.score) : null,
      level: m.level !== undefined ? Number(m.level) : null,
      count: m.count !== undefined ? Number(m.count) : null,
    };
  }

  return {
    // The 15 Bitmoji detection metrics
    uv_acne:      metricScore('acne'),       
    blackhead:    metricScore('blackhead'),   
    collagen:     metricScore('collagen'),    
    skin_tone:    {                          
      score: analysis.color?.score ?? null,
      level: analysis.color?.level ?? null,
      ita:   analysis.color?.ita ?? null,
      result: analysis.color?.result ?? null,  
    },
    dark_circles: metricScore('dark_circle'),
    moisture:     metricScore('ext_water'),
    pigmentation: metricScore('pigment'),
    pimples:      metricScore('pockmark'),    
    pores:        metricScore('pore'),
    sebum:        metricScore('skin_type'),   
    sensitivity:  metricScore('sensitive'),  
    spots:        metricScore('spot'),        
    uv_spots:     metricScore('uv_spot'),     
    wrinkles:     metricScore('wrinkle'),

    // Additional derived metrics
    face_score:   analysis.appearance?.score ?? null, 
    age_estimate: analysis.age?.result ?? null,
  };
}

/**
 * Summarize which skin conditions are "concerning" (level >= 3 or score < 50)
 */
function extractConditions(scores) {
  const conditions = [];
  const thresholds = {
    uv_acne:      { levelThreshold: 2, scoreThreshold: 70 },
    blackhead:    { levelThreshold: 2, scoreThreshold: 70 },
    pimples:      { levelThreshold: 2, scoreThreshold: 70 },
    pores:        { levelThreshold: 2, scoreThreshold: 70 },
    spots:        { levelThreshold: 2, scoreThreshold: 70 },
    uv_spots:     { levelThreshold: 2, scoreThreshold: 70 },
    pigmentation: { levelThreshold: 2, scoreThreshold: 70 },
    wrinkles:     { levelThreshold: 2, scoreThreshold: 70 },
    dark_circles: { levelThreshold: 2, scoreThreshold: 70 },
    sensitivity:  { levelThreshold: 2, scoreThreshold: 70 },
    moisture:     { levelThreshold: 2, scoreThreshold: 60 },  // moisture needs higher threshold
    sebum:        { levelThreshold: 2, scoreThreshold: 70 },
  };

  for (const [key, thr] of Object.entries(thresholds)) {
    const m = scores[key];
    if (!m) continue;
    if ((m.level !== null && m.level > thr.levelThreshold) ||
        (m.score !== null && m.score < thr.scoreThreshold)) {
      conditions.push(key);
    }
  }
  return conditions;
}

/**
 * Derive skin type from Bitmoji scores (sebum, moisture, sensitivity)
 */
function deriveSkinType(scores) {
  const sebum = scores.sebum?.score;
  const moisture = scores.moisture?.score;
  const sensitivity = scores.sensitivity?.level;

  if (sensitivity !== null && sensitivity >= 3) return 'Sensitive';
  if (sebum !== null && sebum < 50) return 'Oily';     // low score = more oily
  if (moisture !== null && moisture < 50) return 'Dry';
  if (sebum !== null && sebum < 65 && moisture !== null && moisture < 65) return 'Combination';
  return 'Normal';
}

/**
 * Download a file from a URL (https) to a local path.

 */
function downloadFile(url, destPath, extraHeaders = {}) {
  return new Promise((resolve) => {
    const proto = url.startsWith('https') ? require('https') : require('http');
    const file = fs.createWriteStream(destPath);
    const options = { headers: { ...extraHeaders } };
    proto.get(url, options, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        fs.unlink(destPath, () => {});
        return downloadFile(res.headers.location, destPath, extraHeaders).then(resolve);
      }
      if (res.statusCode !== 200) {
        file.close();
        fs.unlink(destPath, () => {});
        return resolve(false);
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(true); });
      file.on('error', () => { fs.unlink(destPath, () => {}); resolve(false); });
    }).on('error', () => { fs.unlink(destPath, () => {}); resolve(false); });
  });
}


function buildImageUrls(filename) {
  if (!filename || typeof filename !== 'string') return [];
  // Already a full URL
  if (filename.startsWith('http')) return [filename];
  const clean = filename.replace(/^\/+/, '');
  return [
    `https://${CONFIG.base}/${clean}`,
    `https://${CONFIG.base}/data/${clean}`,
  ];
}


async function downloadRecordImage(record, token) {
  const { result_id, derived_skin_type, derived_conditions, scores,
          image_url, image_url_positive, original_images } = record;
  const destBase = path.join(CONFIG.imagesDir, result_id);
  const metaPath = destBase + '.json';

  // Skip if already downloaded
  if (fs.existsSync(destBase + '.jpg') || fs.existsSync(destBase + '.jpeg') || fs.existsSync(destBase + '.png')) {
    return 'skipped';
  }

  const authHeaders = token ? { 'access_token': token } : {};

  const origEntries = original_images && typeof original_images === 'object'
    ? Object.values(original_images).filter(Boolean).map(v =>
        v.startsWith('http') ? v : `https://${CONFIG.base}/fileSvr/get/${v}`)
    : [];

  const candidates = [
    image_url,
    image_url_positive,
    ...origEntries,
  ].filter(Boolean);

  let downloaded = false;
  let savedExt = '.jpg';
  for (const fname of candidates) {
    for (const url of buildImageUrls(fname)) {
      const ext = path.extname(url).toLowerCase().replace(/[^a-z]/g, '') || 'jpg';
      const destPath = destBase + '.' + ext;
      const ok = await downloadFile(url, destPath, authHeaders);
      if (ok) {
        savedExt = '.' + ext;
        downloaded = true;
        break;
      }
    }
    if (downloaded) break;
  }

  if (!downloaded) return 'failed';

  // Map conditions to ML label space
  const CONDITION_MAP = {
    blackhead: 'Acne', pimples: 'Acne', uv_acne: 'Acne',
    spots: 'Hyperpigmentation', uv_spots: 'Hyperpigmentation', pigmentation: 'Hyperpigmentation',
    wrinkles: 'Wrinkles',
    moisture: 'Dehydration',
    sensitivity: 'Redness',
    pores: 'Acne',
    dark_circles: 'Hyperpigmentation',
  };
  const mlConditions = [...new Set(
    (derived_conditions || []).map(c => CONDITION_MAP[c]).filter(Boolean)
  )];
  if (!mlConditions.length) mlConditions.push('None detected');

  const meta = {
    result_id,
    skin_type: derived_skin_type,
    conditions: mlConditions,
    raw_conditions: derived_conditions,
    scores,
    source: 'bitmoji_device',
    image_file: result_id + savedExt,
  };
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
  return 'downloaded';
}

/**
 * Playwright: open a headed browser, navigate to Reports, and for every row
 * capture View Details text + trigger Export Pictures download.
 * Uses page.evaluate(el => el.click()) so dialog backdrops / virtual-scroll
 * visibility never block the action.
 */
async function dismissAnyDialog(page) {
  await page.evaluate(() => {
    const btn = document.querySelector(
      '.el-dialog__headerbtn, .el-dialog__close, [aria-label="Close"]'
    );
    if (btn) btn.click();
  });
  await page.waitForTimeout(700);
}

async function browseReportsAndExport() {
  log('Launching browser for Reports page...');
  const browser = await chromium.launch({ headless: false, slowMo: 40, args: ['--no-sandbox'], executablePath: CHROME_PATH });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
    acceptDownloads: true,
  });
  const page = await ctx.newPage();

  // ── Login ────────────────────────────────────────────────────────────────
  await page.goto(`https://${CONFIG.base}/`, { waitUntil: 'networkidle', timeout: 30000 });

  // Select English via JS
  await page.evaluate(() => { const s = document.querySelector('.el-select'); if (s) s.click(); });
  await page.waitForTimeout(400);
  for (const o of await page.locator('.el-select-dropdown__item').all()) {
    if ((await o.textContent().catch(() => '')).trim().toLowerCase() === 'english') {
      await o.evaluate(el => el.click()); break;
    }
  }
  await page.waitForTimeout(500);

  await page.locator('input[type="text"]:not([readonly])').first().fill(CONFIG.username);
  await page.locator('input[type="password"]').first().fill(CONFIG.password);
  await page.evaluate(() => {
    const btn = document.querySelector('button[type="submit"]') ||
      [...document.querySelectorAll('button')].find(b => /login/i.test(b.textContent));
    if (btn) btn.click();
  });
  try { await page.waitForLoadState('networkidle', { timeout: 15000 }); } catch (_) {}
  await page.waitForTimeout(1500);
  log('  Logged in → ' + page.url());

  // Navigate to Reports
  await page.evaluate(() => {
    const el = [...document.querySelectorAll('a, li, span, div')]
      .find(e => /^Reports?$/i.test((e.textContent || '').trim()) && e.childElementCount <= 2);
    if (el) el.click();
  });
  try { await page.waitForLoadState('networkidle', { timeout: 10000 }); } catch (_) {}
  await page.waitForTimeout(2500);
  await dismissAnyDialog(page);
  await page.screenshot({ path: path.join(CONFIG.rawDir, 'reports-list.png'), fullPage: true });
  log('  Reports page loaded → ' + page.url());

  // Count rows
  const totalBtns = await page.evaluate(() =>
    document.querySelectorAll('.el-table__row button, .el-table__row .el-button').length
  );
  const totalRows = Math.floor(totalBtns / 3);
  log(`  Found ${totalRows} rows (${totalBtns} buttons, 3 per row)`);
  if (totalRows === 0) {
    await page.screenshot({ path: path.join(CONFIG.rawDir, 'reports-empty.png'), fullPage: true });
    await browser.close();
    return;
  }

  const detailsData = [];
  let exportOk = 0, exportFail = 0;

  for (let row = 0; row < totalRows; row++) {
    const viewIdx   = row * 3;     // "View Details"
    const exportIdx = row * 3 + 2; // "exporting pictures"

    // View Details
    try {
      await page.evaluate((idx) => {
        const btn = document.querySelectorAll(
          '.el-table__row button, .el-table__row .el-button'
        )[idx];
        if (btn) btn.click();
      }, viewIdx);
      await page.waitForTimeout(1500);

      await page.screenshot({ path: path.join(CONFIG.rawDir, `detail-${row}.png`) });
      const txt = await page.locator('.el-dialog, .el-drawer, [role="dialog"]').first()
        .innerText({ timeout: 2000 }).catch(() => '');
      if (txt) detailsData.push({ row, text: txt.substring(0, 3000) });

      await dismissAnyDialog(page);
    } catch (e) {
      log(`  Row ${row} View Details error: ${e.message.split('\n')[0]}`);
      await dismissAnyDialog(page);
    }

    // Export Pictures
    try {
      // Register download listener BEFORE the click
      const dlPromise = page.waitForEvent('download', { timeout: 12000 }).catch(() => null);

      await page.evaluate((idx) => {
        const btn = document.querySelectorAll(
          '.el-table__row button, .el-table__row .el-button'
        )[idx];
        if (btn) btn.click();
      }, exportIdx);

      await page.waitForTimeout(900);

      // Click confirm/OK if it appeared
      const confirmed = await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button')]
          .find(b => /^(OK|Confirm|Yes|确定)$/i.test((b.textContent || '').trim()));
        if (btn) { btn.click(); return true; }
        return false;
      });
      if (confirmed) log(`  Row ${row}: confirm dialog clicked`);

      const download = await dlPromise;
      if (download) {
        const fname = download.suggestedFilename() || `row-${row}-export.zip`;
        const savePath = path.join(CONFIG.imagesDir, fname);
        await download.saveAs(savePath);
        log(`  Row ${row}: saved → ${fname}`);
        exportOk++;
      } else {
        log(`  Row ${row}: no download event`);
        await dismissAnyDialog(page);
        exportFail++;
      }
    } catch (e) {
      log(`  Row ${row} export error: ${e.message.split('\n')[0]}`);
      await dismissAnyDialog(page);
      exportFail++;
    }

    await page.waitForTimeout(400);
  }

  fs.writeFileSync(path.join(CONFIG.rawDir, 'reports-details.json'),
    JSON.stringify(detailsData, null, 2), 'utf8');
  log(`  View Details captured: ${detailsData.length}/${totalRows}`);
  log(`  Exports: ${exportOk} ok, ${exportFail} failed`);

  await browser.close();
  log('Browser closed');
}

/** Headless Playwright login — returns a fresh access_token */
async function getFreshToken() {
  log('Getting fresh token via headless login...');
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'], executablePath: CHROME_PATH });
  const ctx = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await ctx.newPage();
  let token = null;

  page.on('response', async (res) => {
    if (res.url().includes('auth2/token')) {
      const body = await res.json().catch(() => null);
      if (body?.access_token) token = body.access_token;
    }
  });

  await page.goto('https://zm.yiyuan.ai/', { waitUntil: 'networkidle', timeout: 25000 });

  // Select English
  await page.locator('.el-select').first().click({ force: true });
  await page.waitForTimeout(400);
  for (const o of await page.locator('.el-select-dropdown__item').all()) {
    if ((await o.textContent().catch(() => '')).trim().toLowerCase() === 'english') {
      await o.click({ force: true }); break;
    }
  }
  await page.waitForTimeout(600);

  // Fill credentials
  await page.locator('input[type="text"]:not([readonly])').first().fill(CONFIG.username);
  await page.locator('input[type="password"]').first().fill(CONFIG.password);
  await page.locator('button[type="submit"], button:has-text("Login")').first().click();

  try { await page.waitForLoadState('networkidle', { timeout: 12000 }); } catch (_) {}
  await page.waitForTimeout(1000);
  await browser.close();

  if (token) {
    // Persist for reuse
    fs.writeFileSync(path.join(CONFIG.rawDir, 'fresh-token.json'),
      JSON.stringify({ access_token: token, ts: Date.now() }, null, 2), 'utf8');
    log('Fresh token obtained: ' + token.slice(0, 30) + '...');
  }
  return token;
}

(async () => {
  let token = null;

  // token CLI argument
  const tokenArg = getArg('--token', null);
  if (tokenArg) {
    token = tokenArg;
    log('Using token from CLI arg');
  }

  // Step 1: Always get a fresh token — API sessions expire in < 1 h
  if (!token) {
    token = await getFreshToken();
  }

  if (!token) {
    log('ERROR: Could not obtain auth token');
    process.exit(1);
  }

  log('Fetching detection schema...');
  const settingsResp = await apiPost('/skinMgrSrv/settings/get', token, {});
  if (settingsResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-settings.json'),
      JSON.stringify(settingsResp.body, null, 2), 'utf8');
    log('Settings saved (' + settingsResp.body.list.length + ' items)');
  }

  log('Fetching surface copywriting...');
  const surfaceResp = await apiPost('/skinMgrSrv/settings/articleList', token,
    { type: 'layer', page: 1, pageSize: 200 });
  if (surfaceResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-surface-copywriting.json'),
      JSON.stringify(surfaceResp.body, null, 2), 'utf8');
    log('Surface copywriting saved (' + surfaceResp.body.list.length + ' entries)');
  }

  log('Fetching deep copywriting...');
  const deepResp = await apiPost('/skinMgrSrv/settings/articleList', token,
    { type: 'deep', page: 1, pageSize: 200 });
  if (deepResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-deep-copywriting.json'),
      JSON.stringify(deepResp.body, null, 2), 'utf8');
    log('Deep copywriting saved (' + deepResp.body.list.length + ' entries)');
  }

  //Fetch records with full analysis 
  const now = new Date();
  const past = new Date(now - 90 * 24 * 3600 * 1000);
  const fmt = d => d.toISOString().slice(0, 16).replace('T', ' ');
  const dateRange = { st: fmt(past), ed: fmt(now) };

  log('Fetching records (limit=' + LIMIT + ', starting page=' + START_PAGE + ')...');
  const allRecords = [];
  const allScores = [];
  let page = START_PAGE;
  let fetched = 0;

  while (fetched < LIMIT) {
    const batchSize = Math.min(CONFIG.pageSize, LIMIT - fetched);
    log('  Fetching page ' + page + ' (size=' + batchSize + ')...');

    const resp = await apiPost('/skinMgrSrv/record/list', token, {
      code: -1, page, pageSize: batchSize, weidu: 'all',
      st: dateRange.st, ed: dateRange.ed,
    });

    if (resp.body?.code !== 0) {
      log('ERROR fetching records: ' + JSON.stringify(resp.body));
      break;
    }

    const records = resp.body?.data?.list || [];
    if (records.length === 0) {
      log('  No more records on page ' + page);
      break;
    }

    for (const record of records) {
      const analysis = record.analysis || {};
      const scores = extractScores(analysis);
      const conditions = scores ? extractConditions(scores) : [];
      const skinType = scores ? deriveSkinType(scores) : 'Unknown';

      // Store full record (including image URLs for download in Step 6)
      allRecords.push({
        id: record.id,
        result_id: record.result_id,
        device: record.code,
        timestamp: record.crt_time,
        status: record.status,
        analysis_keys: Object.keys(analysis),
        // Image URLs — filename is the normal-light original face photo
        image_url: analysis.filename || null,
        image_url_positive: analysis.filename_positive || null,
        original_images: analysis.original_images || null,
        scores,
        derived_skin_type: skinType,
        derived_conditions: conditions,
      });

      // Store simplified score row for ML training
      if (scores) {
        allScores.push({
          id: record.id,
          timestamp: record.crt_time,
          skin_type: skinType,
          conditions: conditions,
          // Raw scores for all 15 metrics
          s_uv_acne:      scores.uv_acne?.score,
          s_blackhead:    scores.blackhead?.score,
          s_collagen:     scores.collagen?.score,
          s_skin_tone:    scores.skin_tone?.score,
          s_dark_circles: scores.dark_circles?.score,
          s_moisture:     scores.moisture?.score,
          s_pigmentation: scores.pigmentation?.score,
          s_pimples:      scores.pimples?.score,
          s_pores:        scores.pores?.score,
          s_sebum:        scores.sebum?.score,
          s_sensitivity:  scores.sensitivity?.score,
          s_spots:        scores.spots?.score,
          s_uv_spots:     scores.uv_spots?.score,
          s_wrinkles:     scores.wrinkles?.score,
          // Levels (1-5 severity)
          l_uv_acne:      scores.uv_acne?.level,
          l_blackhead:    scores.blackhead?.level,
          l_moisture:     scores.moisture?.level,
          l_pimples:      scores.pimples?.level,
          l_pores:        scores.pores?.level,
          l_sebum:        scores.sebum?.level,
          l_sensitivity:  scores.sensitivity?.level,
          l_spots:        scores.spots?.level,
          l_uv_spots:     scores.uv_spots?.level,
          l_wrinkles:     scores.wrinkles?.level,
          // Demographics
          age_estimate:   scores.age_estimate,
          face_score:     scores.face_score,
          ita:            scores.skin_tone?.ita,
        });
      }
    }

    fetched += records.length;
    const total = resp.body?.data?.total || 0;
    log('  Fetched ' + fetched + '/' + Math.min(total, LIMIT) + ' records');

    if (fetched >= total) break;
    page++;
    await new Promise(r => setTimeout(r, 300)); // polite delay
  }

  if (SKIP_EXPORT) {
    log('\n=== STEP 5: Skipping Reports → Export Pictures (--skip-export) ===');
  } else {
    log('\n=== STEP 5: Browse Reports → View Details + Export Pictures ===');
    await browseReportsAndExport();
  }

  log('\n=== STEP 6: Downloading face images ===');
  let dlOk = 0, dlSkipped = 0, dlFailed = 0;
  for (let i = 0; i < allRecords.length; i++) {
    const record = allRecords[i];
    if (i % 10 === 0) log(`  Progress: ${i}/${allRecords.length}`);
    const result = await downloadRecordImage(record, token);
    if (result === 'downloaded') dlOk++;
    else if (result === 'skipped') dlSkipped++;
    else dlFailed++;
    await new Promise(r => setTimeout(r, 150)); // polite delay
  }
  log(`  Images: ${dlOk} downloaded, ${dlSkipped} skipped, ${dlFailed} failed`);
  log(`  Saved to: ${CONFIG.imagesDir}`);

  // Print move command to copy images into the ML training pipeline
  const mlDir = path.resolve(__dirname, '..', 'backend', 'ml', 'data', 'bitmoji');
  log('\n=== STEP 7: Move images to ML training folder ===');
  log('  Run this command to copy images into the training pipeline:');
  log(`  mkdir -p "${mlDir}" && cp -r "${CONFIG.imagesDir}/." "${mlDir}/"`);
  log('  Then retrain with:  docker exec -d skincare-api python ml/train_pipeline.py --skip-download');


  log('\n=== STEP 8: Saving JSON / CSV ===');
  fs.writeFileSync(path.join(CONFIG.rawDir, 'records-full.json'),
    JSON.stringify(allRecords, null, 2), 'utf8');
  fs.writeFileSync(path.join(CONFIG.rawDir, 'records-scores.json'),
    JSON.stringify(allScores, null, 2), 'utf8');

  if (allScores.length > 0) {
    const headers = Object.keys(allScores[0]).join(',');
    const rows = allScores.map(r => Object.values(r).map(v =>
      v === null || v === undefined ? '' : (Array.isArray(v) ? '"' + v.join('|') + '"' : v)
    ).join(','));
    fs.writeFileSync(path.join(CONFIG.rawDir, 'records-scores.csv'),
      [headers, ...rows].join('\n'), 'utf8');
  }

  log('\n=== DONE ===');
  log('Records fetched : ' + allRecords.length);
  log('Images saved to : ' + CONFIG.imagesDir);
  log('Skin type distribution:');
  const dist = {};
  for (const s of allScores) { dist[s.skin_type] = (dist[s.skin_type] || 0) + 1; }
  for (const [k, v] of Object.entries(dist)) log('  ' + k + ': ' + v);
  log('\nFiles:');
  log('  raw/records-full.json     — full analysis objects');
  log('  raw/records-scores.json   — simplified scores per record');
  log('  raw/records-scores.csv    — CSV for ML pipeline');
  log('  raw/images/*.jpg          — original face images');
  log('  raw/images/*.json         — ML label metadata per image');
})();
