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

const CONFIG = {
  base: 'zm.yiyuan.ai',
  username: 'Cyrus',
  password: 'Zhuri',
  rawDir: path.join(__dirname, 'raw'),
  pageSize: 20,
};

const args = process.argv.slice(2);
const LIMIT = parseInt(args[args.indexOf('--limit') + 1] || '100');
const START_PAGE = parseInt(args[args.indexOf('--page') + 1] || '1');

if (!fs.existsSync(CONFIG.rawDir)) fs.mkdirSync(CONFIG.rawDir, { recursive: true });

function log(msg) { console.log('[' + new Date().toISOString().substring(11, 19) + '] ' + msg); }

function apiGet(path, token) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: CONFIG.base,
      path: path,
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {}),
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
    req.end();
  });
}


/**
 * Extract the 15 standardized skin metric scores from a record's analysis object.
 * Returns an object with score (0-100) and level (1-5) for each metric.
 */
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
    uv_acne:      metricScore('acne'),       // UV Acne (deep layer)
    blackhead:    metricScore('blackhead'),   // Blackheads (surface)
    collagen:     metricScore('collagen'),    // Collagen Fibers
    skin_tone:    {                           // Skin Color (ITA-based, special case)
      score: analysis.color?.score ?? null,
      level: analysis.color?.level ?? null,
      ita:   analysis.color?.ita ?? null,
      result: analysis.color?.result ?? null,  // e.g. "xiaomai", "ziran"
    },
    dark_circles: metricScore('dark_circle'),
    moisture:     metricScore('ext_water'),
    pigmentation: metricScore('pigment'),
    pimples:      metricScore('pockmark'),    // Acne marks / pimples
    pores:        metricScore('pore'),
    sebum:        metricScore('skin_type'),   // Sebum / oiliness
    sensitivity:  metricScore('sensitive'),   // PL Sensitivity
    spots:        metricScore('spot'),        // Dark spots
    uv_spots:     metricScore('uv_spot'),     // UV spots
    wrinkles:     metricScore('wrinkle'),

    // Additional derived metrics
    face_score:   analysis.appearance?.score ?? null,  // Overall appearance score
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

(async () => {
  let token = null;

  // token CLI argument
  const tokenArg = args[args.indexOf('--token') + 1];
  if (tokenArg) {
    token = tokenArg;
    log('Using token from CLI arg');
  }

  if (!token) {
    const rawFiles = ['p2-all-api-responses.json', 'all-api-responses.json', 'all-api-calls.json'];
    for (const f of rawFiles) {
      const fp = path.join(CONFIG.rawDir, f);
      if (!fs.existsSync(fp)) continue;
      try {
        const saved = JSON.parse(fs.readFileSync(fp, 'utf8'));
        const authEntry = saved.find(e => e.url?.includes('auth2/token') && e.body?.access_token);
        if (authEntry) {
          token = authEntry.body.access_token;
          log('Using token from ' + f + ': ' + token.slice(0, 30) + '...');
          break;
        }
      } catch (_) {}
    }
  }

  if (!token) {
    log('ERROR: No auth token found. Run scraper.js first, or pass --token <token>');
    process.exit(1);
  }

  // ── Step 2: Fetch detection schema (settings) ───────────────────────────
  log('Fetching detection schema...');
  const settingsResp = await apiGet('/skinMgrSrv/settings/get', token);
  if (settingsResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-settings.json'),
      JSON.stringify(settingsResp.body, null, 2), 'utf8');
    log('Settings saved (' + settingsResp.body.list.length + ' items)');
  }

  // ── Step 3: Fetch copywriting (all conditions, all levels) ─────────────
  log('Fetching surface copywriting...');
  const surfaceResp = await apiGet('/skinMgrSrv/settings/articleList?type=layer&page=1&pageSize=200', token);
  if (surfaceResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-surface-copywriting.json'),
      JSON.stringify(surfaceResp.body, null, 2), 'utf8');
    log('Surface copywriting saved (' + surfaceResp.body.list.length + ' entries)');
  }

  log('Fetching deep copywriting...');
  const deepResp = await apiGet('/skinMgrSrv/settings/articleList?type=deep&page=1&pageSize=200', token);
  if (deepResp.body?.list) {
    fs.writeFileSync(path.join(CONFIG.rawDir, 'api-deep-copywriting.json'),
      JSON.stringify(deepResp.body, null, 2), 'utf8');
    log('Deep copywriting saved (' + deepResp.body.list.length + ' entries)');
  }

  // ── Step 4: Fetch records with full analysis ────────────────────────────
  log('Fetching records (limit=' + LIMIT + ', starting page=' + START_PAGE + ')...');
  const allRecords = [];
  const allScores = [];
  let page = START_PAGE;
  let fetched = 0;

  while (fetched < LIMIT) {
    const batchSize = Math.min(CONFIG.pageSize, LIMIT - fetched);
    log('  Fetching page ' + page + ' (size=' + batchSize + ')...');

    const resp = await apiGet(
      '/skinMgrSrv/record/list?page=' + page + '&pageSize=' + batchSize + '&status=2',
      token
    );

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

      // Store full record
      allRecords.push({
        id: record.id,
        result_id: record.result_id,
        device: record.code,
        timestamp: record.crt_time,
        status: record.status,
        analysis_keys: Object.keys(analysis),
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

  // ── Step 5: Save ─────────────────────────────────────────────────────────
  fs.writeFileSync(path.join(CONFIG.rawDir, 'records-full.json'),
    JSON.stringify(allRecords, null, 2), 'utf8');
  fs.writeFileSync(path.join(CONFIG.rawDir, 'records-scores.json'),
    JSON.stringify(allScores, null, 2), 'utf8');

  // Also write CSV for ML pipeline ingestion
  if (allScores.length > 0) {
    const headers = Object.keys(allScores[0]).join(',');
    const rows = allScores.map(r => Object.values(r).map(v =>
      v === null || v === undefined ? '' : (Array.isArray(v) ? '"' + v.join('|') + '"' : v)
    ).join(','));
    fs.writeFileSync(path.join(CONFIG.rawDir, 'records-scores.csv'),
      [headers, ...rows].join('\n'), 'utf8');
  }

  log('=== DONE ===');
  log('Records fetched: ' + allRecords.length);
  log('Skin type distribution:');
  const dist = {};
  for (const s of allScores) { dist[s.skin_type] = (dist[s.skin_type] || 0) + 1; }
  for (const [k, v] of Object.entries(dist)) log('  ' + k + ': ' + v);
  log('\nFiles:');
  log('  raw/records-full.json     — full analysis objects');
  log('  raw/records-scores.json   — simplified scores per record');
  log('  raw/records-scores.csv    — CSV for ML pipeline');
})();
