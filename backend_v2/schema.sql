-- Skincare v2 schema
-- Run once against a fresh database. Safe to re-run (all CREATE TABLE IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    email        TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name    TEXT,
    role         TEXT NOT NULL DEFAULT 'customer',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (lower(email));

CREATE TABLE IF NOT EXISTS skin_profile_history (
    id                      SERIAL PRIMARY KEY,
    user_id                 TEXT NOT NULL REFERENCES users(id),
    skin_type               TEXT NOT NULL,
    conditions_csv          TEXT NOT NULL DEFAULT '',
    confidence              DOUBLE PRECISION NOT NULL DEFAULT 0,
    questionnaire_json      TEXT,
    skin_type_scores_json   TEXT,
    condition_scores_json   TEXT,
    inference_mode          TEXT,
    report_image_base64     TEXT,
    user_feedback           TEXT,
    capture_images_json     TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sph_user_id ON skin_profile_history (user_id);

CREATE TABLE IF NOT EXISTS product_catalog (
    sku             TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    price           DOUBLE PRECISION,
    wc_id           INTEGER,
    stock           INTEGER NOT NULL DEFAULT 0,
    description     TEXT,
    category        TEXT,
    image_url       TEXT,
    ingredients_csv TEXT NOT NULL DEFAULT '',
    suitable_for    TEXT NOT NULL DEFAULT 'all',
    effects_csv     TEXT NOT NULL DEFAULT '',
    benefits_csv    TEXT,
    usage           TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    wc_order_id INTEGER,
    channel     TEXT NOT NULL DEFAULT 'app',
    status      TEXT NOT NULL DEFAULT 'created',
    total       DOUBLE PRECISION,
    items_json  TEXT NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id);

CREATE TABLE IF NOT EXISTS loyalty_ledger (
    id         SERIAL PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id),
    points     INTEGER NOT NULL,
    reason     TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_loyalty_user_id ON loyalty_ledger (user_id);
