# scrappy — Bitmoji Device Data Collector

Scrapes and normalizes data from the Bitmoji AI skin analysis device portal (zm.yiyuan.ai)
so that the mobile app ML model can be aligned with the device's output schema.

## Structure

```
scrappy/
├── scraper.js          # Main Playwright scraper — run to refresh raw data
├── collector.js        # API client — fetches full record details directly
├── extract.js          # Normalizes raw → output/ (schema, copywriting, records)
├── raw/                # Raw captures (screenshots, HTML, JSON, text)
└── output/             # Cleaned, normalized data consumed by ML pipeline
    ├── detection_schema.json      # 15 detection items with English names & API keys
    ├── product_efficacy_map.json  # Condition → recommended product effects mapping
    ├── copywriting_surface.json   # Surface-layer advice per condition per level (1-5)
    ├── copywriting_deep.json      # Deep-layer advice per condition per level (1-5)
    ├── content_settings.json      # Algorithm config (chart type, age mode, water mode)
    ├── records_sample.json        # Sample analyzed records with full score payloads
    └── label_alignment.json       # Mapping: Bitmoji field → our model label
```

## Usage

```bash
# 1. Re-scrape fresh data from portal
node scraper.js

# 2. Fetch fresh record details via API
node collector.js

# 3. Normalize all raw → output/
node extract.js
```

## Key Schema (Bitmoji → Our Model)

| Bitmoji Field | English Label   | Our Label      | Score Range | Level Range |
|--------------|-----------------|----------------|-------------|-------------|
| acne         | UV acne         | Acne           | 0-100       | 1-5         |
| blackhead    | Blackhead       | Blackheads     | 0-100       | 1-5         |
| collagen     | Collagen fiber  | Collagen       | 0-100       | 1-5         |
| color        | Skin color      | Skin Tone      | 0-100       | 1-6 (ITA)   |
| dark_circle  | Dark Eye Circles| Dark Circles   | 0-100       | 1-5         |
| ext_water    | Moisture        | Moisture       | 0-100       | 1-5         |
| pigment      | Pigmentation    | Pigmentation   | 0-100       | 1-5         |
| pockmark     | Acne marks      | Pimples/Scars  | 0-100       | 1-5         |
| pore         | Pores           | Enlarged Pores | 0-100       | 1-5         |
| sebum        | Sebum           | Oiliness       | 0-100       | 1-5         |
| sensitive    | PL Sensitivity  | Sensitivity    | 0-100       | 1-5         |
| skin_type    | Skin type       | Skin Type      | 0-100       | 1-5         |
| spot         | Spots           | Dark Spots     | 0-100       | 1-5         |
| uv_spot      | UV spot         | UV Spots       | 0-100       | 1-5         |
| wrinkle      | Wrinkles        | Wrinkles       | 0-100       | 1-5         |
