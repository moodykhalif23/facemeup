/**
 * scrappy/extract.js
 * Normalizes raw/ data into clean output/ files consumed by the ML pipeline.
 *
 * Usage: node extract.js
 */
const fs = require('fs');
const path = require('path');

const RAW = path.join(__dirname, 'raw');
const OUT = path.join(__dirname, 'output');
if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

function log(msg) { console.log('[extract] ' + msg); }
function readJson(file) {
  const p = path.join(RAW, file);
  if (!fs.existsSync(p)) { log('MISSING: ' + file); return null; }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}
function save(name, data) {
  fs.writeFileSync(path.join(OUT, name), JSON.stringify(data, null, 2), 'utf8');
  log('Saved: output/' + name);
}

// ── 1. Detection Schema ──────────────────────────────────────────────────────
log('=== Building detection_schema.json ===');
const settings = readJson('api-settings.json');
const DETECTION_SCHEMA = {
  _description: 'Bitmoji device detection items. score=0-100 (higher=healthier), level=1-5 (higher=worse).',
  items: [
    { typename: 'acne',       label: 'UV Acne',         our_label: 'Acne',            type: 'deep',    score_range: [0,100], level_range: [1,5] },
    { typename: 'blackhead',  label: 'Blackhead',        our_label: 'Blackheads',      type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'collagen',   label: 'Collagen Fiber',   our_label: 'Collagen',        type: 'deep',    score_range: [0,100], level_range: [1,5] },
    { typename: 'color',      label: 'Skin Color',       our_label: 'Skin Tone',       type: 'surface', score_range: [0,100], level_range: [1,6], note: 'ITA-based Fitzpatrick-like scale' },
    { typename: 'dark_circle',label: 'Dark Eye Circles', our_label: 'Dark Circles',    type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'ext_water',  label: 'Moisture',         our_label: 'Moisture',        type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'pigment',    label: 'Pigmentation',     our_label: 'Pigmentation',    type: 'deep',    score_range: [0,100], level_range: [1,5] },
    { typename: 'pockmark',   label: 'Acne Marks',       our_label: 'Pimples/Scars',   type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'pore',       label: 'Pores',            our_label: 'Enlarged Pores',  type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'sebum',      label: 'Sebum',            our_label: 'Oiliness',        type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'sensitive',  label: 'PL Sensitivity',   our_label: 'Sensitivity',     type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'skin_type',  label: 'Skin Type',        our_label: 'Sebum/Skin Type', type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'spot',       label: 'Dark Spots',       our_label: 'Dark Spots',      type: 'surface', score_range: [0,100], level_range: [1,5] },
    { typename: 'uv_spot',    label: 'UV Spots',         our_label: 'UV Spots',        type: 'deep',    score_range: [0,100], level_range: [1,5] },
    { typename: 'wrinkle',    label: 'Wrinkles',         our_label: 'Wrinkles',        type: 'surface', score_range: [0,100], level_range: [1,5] },
  ],
};
if (settings?.list) {
  // Merge API-sourced rate/ratename if present
  for (const item of DETECTION_SCHEMA.items) {
    const apiItem = settings.list.find(s => s.typename === item.typename);
    if (apiItem) {
      item.current_rate = apiItem.rate;
      item.rate_label = apiItem.ratename;
      item.api_category = apiItem.categray;
    }
  }
}
save('detection_schema.json', DETECTION_SCHEMA);

// ── 2. Product Efficacy Map ──────────────────────────────────────────────────
log('=== Building product_efficacy_map.json ===');
const EFFICACY_MAP = {
  _description: 'Maps detected skin conditions to recommended product effect categories.',
  _source: 'Config → product efficacy on zm.yiyuan.ai',
  mappings: {
    Sebum:        ['cleansing', 'oil_control', 'water_oil_balance'],
    Acne:         ['repair', 'acne_treatment', 'fade_acne_marks'],
    Pigmentation: ['lightening', 'sunscreen'],
    Wrinkles:     ['firming', 'anti_wrinkle', 'anti_aging', 'antioxidant'],
    Pores:        ['cleansing', 'pore_minimizing'],
    Blackheads:   ['cleansing', 'pore_minimizing'],
    'Skin Tone':  ['brightening', 'sunscreen', 'rejuvenation', 'antioxidant'],
    Moisture:     ['hydration', 'moisturizing', 'water_locking'],
    Sensitivity:  ['repair', 'soothing'],
    'UV Spots':   ['lightening', 'sunscreen'],
    'Dark Spots': ['lightening', 'sunscreen', 'detoxification', 'brightening'],
    'UV Acne':    ['cleansing', 'repair', 'detoxification'],
    'Dark Circles': ['repair', 'brightening', 'firming'],
    Collagen:     ['firming', 'anti_aging', 'collagen_boosting'],
  },
};
save('product_efficacy_map.json', EFFICACY_MAP);

// ── 3. Surface Copywriting ────────────────────────────────────────────────────
log('=== Building copywriting_surface.json ===');
const surfaceRaw = readJson('api-surface-copywriting.json');
if (surfaceRaw?.list) {
  const surfaceMap = {};
  for (const item of surfaceRaw.list) {
    const key = item.service;
    if (!surfaceMap[key]) surfaceMap[key] = { service_name: item.service_name, levels: {} };
    surfaceMap[key].levels[item.value] = {
      level: Number(item.value),
      introduction: item.introduction,
      advice: item.advice,
    };
  }
  save('copywriting_surface.json', {
    _description: 'Surface-layer detection advice per condition per severity level (1=mild, 5=severe).',
    conditions: surfaceMap,
  });
} else {
  log('  WARNING: No surface copywriting data found');
}

// ── 4. Deep Copywriting ────────────────────────────────────────────────────────
log('=== Building copywriting_deep.json ===');
const deepRaw = readJson('api-deep-copywriting.json');
if (deepRaw?.list) {
  const deepMap = {};
  for (const item of deepRaw.list) {
    const key = item.service;
    if (!deepMap[key]) deepMap[key] = { service_name: item.service_name, levels: {} };
    deepMap[key].levels[item.value] = {
      level: Number(item.value),
      introduction: item.introduction,
      advice: item.advice,
    };
  }
  save('copywriting_deep.json', {
    _description: 'Deep-layer detection advice per condition per severity level.',
    conditions: deepMap,
  });
} else {
  log('  WARNING: No deep copywriting data found');
}

// ── 5. Content Settings ───────────────────────────────────────────────────────
log('=== Building content_settings.json ===');
// Parse from all-api-responses
const allResp = readJson('all-api-responses.json') || readJson('p2-all-api-responses.json') || [];
const configResp = allResp.find(r => r.url?.includes('config/get') && r.body?.data_show_type !== undefined);
const CONTENT_SETTINGS = {
  _description: 'Device algorithm configuration',
  _source: 'Config → content settings on zm.yiyuan.ai',
  data_show_type: configResp?.body?.data_show_type || null,  // 1=column chart, 2=rose chart
  age_mode: configResp?.body?.age_mode || null,              // 1=AI prediction, 0=customer age
  age_type: configResp?.body?.age_type || null,
  color_show_type: configResp?.body?.color_show_type || null, // 0=5-level, 1=unevenness
  water_mode: configResp?.body?.water_mode || null,           // 1=Water Pen, 0=Algorithm
  chart_types: { '1': 'column_chart', '2': 'rose_chart' },
  age_modes: { '1': 'AI_prediction_algorithm', '0': 'reference_customer_age' },
  water_modes: { '1': 'water_pen_sensor', '0': 'algorithm_only' },
};
save('content_settings.json', CONTENT_SETTINGS);

// ── 6. Records Sample ─────────────────────────────────────────────────────────
log('=== Building records_sample.json ===');
const recordsFull = readJson('records-full.json');
if (recordsFull) {
  save('records_sample.json', {
    _description: 'Sample of analyzed records with scores and derived labels',
    _count: recordsFull.length,
    records: recordsFull.slice(0, 20),
  });
  log('  ' + recordsFull.length + ' records found');
} else {
  log('  WARNING: No records data. Run: node collector.js first');
}

// ── 7. Label Alignment Map ────────────────────────────────────────────────────
log('=== Building label_alignment.json ===');
save('label_alignment.json', {
  _description: 'Maps Bitmoji API field names to our ML model output labels',
  _note: 'Use this to align training labels with device output labels',
  skin_types: {
    'Oily':        { bitmoji_indicator: 'sebum.score < 50 OR skin_type.score < 50', conditions_typical: ['Acne','Blackheads','Enlarged Pores','UV Acne'] },
    'Dry':         { bitmoji_indicator: 'ext_water.score < 50', conditions_typical: ['Wrinkles','Dark Spots','Sensitivity'] },
    'Combination': { bitmoji_indicator: 'sebum.score 50-65 AND ext_water.score 50-65', conditions_typical: ['Blackheads','Pores','Oiliness'] },
    'Normal':      { bitmoji_indicator: 'all scores > 65', conditions_typical: [] },
    'Sensitive':   { bitmoji_indicator: 'sensitive.level >= 3', conditions_typical: ['Sensitivity','Redness'] },
  },
  condition_map: {
    'acne':        { bitmoji_field: 'pockmark', our_label: 'Acne',            threshold_level: 2 },
    'blackhead':   { bitmoji_field: 'blackhead', our_label: 'Blackheads',     threshold_level: 2 },
    'dark_spot':   { bitmoji_field: 'spot',      our_label: 'Dark Spots',     threshold_level: 2 },
    'pore':        { bitmoji_field: 'pore',      our_label: 'Enlarged Pores', threshold_level: 2 },
    'wrinkle':     { bitmoji_field: 'wrinkle',   our_label: 'Wrinkles',       threshold_level: 2 },
    'oiliness':    { bitmoji_field: 'sebum',     our_label: 'Oiliness',       threshold_level: 2 },
    'sensitivity': { bitmoji_field: 'sensitive', our_label: 'Sensitivity',    threshold_level: 2 },
    'pigment':     { bitmoji_field: 'pigment',   our_label: 'Pigmentation',   threshold_level: 2 },
    'uv_acne':     { bitmoji_field: 'acne',      our_label: 'UV Acne',        threshold_level: 2 },
    'collagen':    { bitmoji_field: 'collagen',  our_label: 'Collagen',       threshold_level: 2 },
    'dark_circle': { bitmoji_field: 'dark_circle', our_label: 'Dark Circles', threshold_level: 2 },
    'moisture':    { bitmoji_field: 'ext_water', our_label: 'Dryness',        threshold_level: 2 },
  },
});

log('=== EXTRACTION COMPLETE ===');
log('Output files in: ' + OUT);
fs.readdirSync(OUT).forEach(f => log('  ' + f));
