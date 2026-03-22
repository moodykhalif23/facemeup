# SkinCare AI — Technical Documentation

> Last updated: 2026-03-22

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Backend](#3-backend)
   - [Tech Stack](#31-tech-stack)
   - [Database Schema](#32-database-schema)
   - [API Reference](#33-api-reference)
   - [Authentication](#34-authentication)
   - [ML Inference](#35-ml-inference)
   - [Recommendation Engine](#36-recommendation-engine)
   - [WooCommerce Integration](#37-woocommerce-integration)
   - [Caching](#38-caching)
   - [Error Handling](#39-error-handling)
4. [Frontend](#4-frontend)
   - [Tech Stack](#41-tech-stack)
   - [Pages & Routes](#42-pages--routes)
   - [State Management](#43-state-management)
   - [API Client](#44-api-client)
   - [Face Capture](#45-face-capture)
5. [Configuration](#5-configuration)
6. [Running Locally](#6-running-locally)
7. [Deployment](#7-deployment)
8. [Key Files](#8-key-files)

---

## 1. System Overview

**SkinCare AI** is an AI-powered skincare platform. Users scan their face, answer a short questionnaire, and receive a skin-type diagnosis plus personalized product recommendations pulled from a live WooCommerce store.

The platform supports **Web, iOS, and Android** from a single React codebase via Capacitor.

**Core user journey:**
```
Register / Login
      ↓
Face Capture (5 poses, MediaPipe)
      ↓
Questionnaire (skin feel, routine, concerns)
      ↓
AI Analysis (TensorFlow model or questionnaire fallback)
      ↓
Skin Profile saved to DB
      ↓
Product Recommendations
      ↓
Add to Cart → Checkout → Order History
      ↓
Loyalty Points earned
```

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│   React + Vite + Ant Design + Redux                         │
│   Capacitor (iOS / Android wrapper)                         │
│   MediaPipe (in-browser face mesh)                          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / REST JSON
┌────────────────────────▼────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│   /api/v1/{auth, analyze, recommend, products,              │
│            orders, loyalty, profile, sync, training}        │
│                                                             │
│   ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│   │  Auth (JWT)  │  │ ML Inference  │  │ Recommendation │  │
│   └──────────────┘  └───────────────┘  └────────────────┘  │
│   ┌──────────────┐  ┌───────────────┐  ┌────────────────┐  │
│   │  WooCommerce │  │  APScheduler  │  │ Redis Cache    │  │
│   │  Sync        │  │  (training)   │  │                │  │
│   └──────────────┘  └───────────────┘  └────────────────┘  │
└───────────┬─────────────────────────────────────────────────┘
            │
  ┌─────────▼──────────┐    ┌──────────────────┐
  │   PostgreSQL DB     │    │   Redis Cache    │
  └────────────────────┘    └──────────────────┘
```

---

## 3. Backend

### 3.1 Tech Stack

| Concern | Library / Version |
|---------|------------------|
| Framework | FastAPI 0.115+ |
| Database ORM | SQLAlchemy (psycopg3 driver) |
| Migrations | Alembic |
| Auth | python-jose (JWT HS256) + bcrypt |
| ML | TensorFlow 2.16+, Keras, OpenCV, Pillow |
| Caching | Redis |
| Background Jobs | APScheduler |
| E-commerce | WooCommerce REST API (OAuth 1.0a) |
| Server | Uvicorn |

---

### 3.2 Database Schema

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| `id` | String(64) PK | UUID |
| `email` | String(255) UNIQUE | Index |
| `password_hash` | String(255) | bcrypt |
| `full_name` | String(255) | Nullable |
| `role` | String(32) | `customer` / `admin` / `advisor` |
| `created_at` | DateTime | Auto |

#### `refresh_tokens`
| Column | Type | Notes |
|--------|------|-------|
| `id` | String(64) PK | |
| `user_id` | FK → users.id | Index |
| `expires_at` | DateTime | 14 days |
| `revoked_at` | DateTime | Nullable; set on rotation |
| `created_at` | DateTime | |

#### `skin_profile_history`
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `user_id` | FK → users.id | Index |
| `skin_type` | String(64) | e.g. `Oily` |
| `conditions_csv` | String(512) | Comma-separated |
| `confidence` | Float | 0.0 – 1.0 |
| `created_at` | DateTime | |

#### `product_catalog`
| Column | Type | Notes |
|--------|------|-------|
| `sku` | String(64) PK | WC SKU or `WC-{id}` |
| `name` | String(255) | |
| `ingredients_csv` | String(1024) | Comma-separated |
| `stock` | Integer | |
| `price` | Float | |
| `description` | Text | |
| `category` | String(255) | |
| `image_url` | String(512) | |
| `wc_id` | Integer | WooCommerce product ID |

#### `orders`
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `user_id` | FK → users.id | Index |
| `channel` | String(32) | e.g. `web`, `ios` |
| `items_json` | Text | Serialized cart array |
| `status` | String(32) | `created` / `paid` / etc. |
| `created_at` | DateTime | |

#### `loyalty_ledger`
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `user_id` | FK → users.id | Index |
| `points` | Integer | Positive = earned, Negative = redeemed |
| `reason` | String(256) | Human-readable label |
| `created_at` | DateTime | |

---

### 3.3 API Reference

All endpoints are prefixed with `/api/v1`.

#### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/signup` | Public | Register a new user |
| POST | `/auth/login` | Public | Returns JWT access + refresh tokens |
| POST | `/auth/refresh` | Public | Rotates refresh token; returns new pair |
| GET | `/auth/me` | Required | Returns current user info |

**Login response:**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "customer"
}
```

---

#### Skin Analysis

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/analyze` | Required | Analyze skin from image + questionnaire |

**Request body:**
```json
{
  "image_base64": "<base64-encoded image>",
  "landmarks": [
    { "x": 0.5, "y": 0.4, "z": 0.0 }
  ],
  "questionnaire": {
    "skin_feel": "oily",
    "routine": "basic",
    "concerns": ["acne", "dark_spots"]
  }
}
```

**Response:**
```json
{
  "profile": {
    "skin_type": "Oily",
    "conditions": ["Acne"],
    "confidence": 0.94,
    "face_quality_score": 0.87,
    "skin_type_scores": { "Oily": 0.94, "Dry": 0.02 },
    "condition_scores": { "Acne": 0.78, "Hyperpigmentation": 0.21 }
  },
  "inference_mode": "server_savedmodel"
}
```

`inference_mode` values:
- `server_savedmodel` — model ran successfully
- `questionnaire_fallback` — model unavailable; questionnaire used

---

#### Recommendations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/recommend` | Required | Get ranked product recommendations |

**Request body:**
```json
{
  "skin_type": "Oily",
  "conditions": ["Acne"]
}
```

**Response:** Array of products with a `score` field (0.0 – 1.0), sorted descending.

---

#### Skin Profile

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/profile/{user_id}` | Required | Get full profile history for a user |
| PUT | `/profile/{user_id}` | Required | Append a new profile entry |

---

#### Products

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/products` | Public | List all products (Redis-cached) |
| GET | `/products/{sku}` | Public | Get single product detail |
| POST | `/products/admin/seed` | Admin | Re-seed product catalog from WooCommerce |

---

#### Orders

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/orders` | Required | Create an order |
| GET | `/orders` | Required | List all orders for the current user |
| GET | `/orders/{order_id}` | Required | Get a specific order |

---

#### Loyalty

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/loyalty` | Required | Get current user's points balance and tier |
| GET | `/loyalty/{user_id}` | Required | Get loyalty data for a specific user |
| POST | `/loyalty/earn` | Admin / Advisor | Award or deduct points |

**Tiers:**
| Tier | Points Required |
|------|----------------|
| Bronze | 0 – 499 |
| Silver | 500 – 999 |
| Gold | 1 000 – 1 999 |
| Platinum | 2 000+ |

**Redeemable rewards:**
| Reward | Cost (pts) |
|--------|-----------|
| 10% discount | 500 |
| Free shipping | 300 |
| Free sample | 750 |
| 20% discount | 1 000 |
| Premium gift set | 1 500 |

---

#### WooCommerce Sync

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/sync/woocommerce` | Admin | Pull products from WooCommerce store |

---

#### Training

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/training/submit` | Required | Upload face image for future model training |

Submitted images are saved to `ml/data/user_captured/{skin_type}/`. APScheduler processes these every 6 hours.

---

#### Utility

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/proxy/image?url=...` | Public | Proxy external image URLs (CORS bypass) |
| GET | `/health` | Public | Health check — returns `{ "status": "ok" }` |

---

### 3.4 Authentication

**Flow:**
1. `POST /auth/signup` — hashes password with bcrypt, stores user.
2. `POST /auth/login` — validates credentials, issues JWT pair.
3. Every request sends `Authorization: Bearer <access_token>`.
4. `POST /auth/refresh` — validates refresh token from DB, revokes it (`revoked_at`), issues a new pair (rotation).

**Token specs:**
| Token | Algorithm | Expiry |
|-------|-----------|--------|
| Access | HS256 | 30 minutes |
| Refresh | HS256 | 14 days |

**Role guards:**
- `customer` — standard user access
- `advisor` — can award loyalty points
- `admin` — all above + sync, seed, admin endpoints

---

### 3.5 ML Inference

**Model:** TensorFlow SavedModel at `app/models_artifacts/saved_model/`
**Input:** 224 × 224 RGB image, normalized to [0, 1]
**Output:** Probability vector → first N values = skin types, remaining = conditions

**Skin types** (5): `Oily`, `Dry`, `Combination`, `Normal`, `Sensitive`
**Conditions** (5): `Acne`, `Hyperpigmentation`, `Uneven tone`, `Dehydration`, `None detected`

**Inference pipeline:**
```
1. Decode base64 → PIL Image
2a. If landmarks provided:
    → Extract face ROI using MediaPipe coordinates
2b. Else:
    → Enhance contrast & sharpness
3. Resize to 224×224
4. Normalize pixels → [0.0, 1.0]
5. Run model.predict()
6. Skin type = argmax of first 5 outputs
7. Conditions = outputs > adaptive threshold (0.35–0.40)
8. Compute face_quality_score from landmark spread
```

**Questionnaire fallback** (model unavailable):
- `skin_feel` → skin type (direct mapping)
- `concerns` → conditions
- Confidence synthesized from questionnaire consistency

---

### 3.6 Recommendation Engine

Matches `skin_type` + `conditions` to products using two signals:

**Ingredient matching** — each skin type and condition maps to a list of beneficial ingredients:
- Oily: Niacinamide, Salicylic Acid, Tea Tree, Zinc, Clay, Charcoal
- Dry: Hyaluronic Acid, Ceramides, Glycerin, Shea Butter
- Sensitive: Panthenol, Aloe Vera, Centella Asiatica
- Acne: Benzoyl Peroxide, Salicylic Acid
- Hyperpigmentation: Vitamin C, Kojic Acid, Niacinamide

**Keyword matching** — searches product name, category, and description.

**Score formula:**
```
score = (keyword_match_ratio × 0.7) + (ingredient_match_ratio × 0.3)
```

Returns top 20 products with `score > 0.1`, sorted descending.

Results are Redis-cached per `{user_id}:{skin_type}:{sorted_conditions}` for 5 minutes.

---

### 3.7 WooCommerce Integration

- **Store URL:** `https://drrashel.co.ke`
- **Auth:** OAuth 1.0a (consumer key + secret)
- **Sync:** Fetches all published products (paginated, 100/page)
- **Field mapping:**

| WooCommerce | `product_catalog` |
|-------------|-------------------|
| `sku` or `WC-{id}` | `sku` |
| `name` | `name` |
| `regular_price` | `price` |
| `stock_quantity` | `stock` |
| `meta_data[ingredients]` | `ingredients_csv` |
| `categories[0].name` | `category` |
| `short_description` | `description` |
| `images[0].src` | `image_url` |
| `id` | `wc_id` |

If no ingredients meta found, defaults to `Natural Extracts, Vitamins, Moisturizers`.

---

### 3.8 Caching

All caching goes through Redis using JSON serialization.

| Cache Key | Content | TTL |
|-----------|---------|-----|
| `products:catalog` | Full product list | 300 s |
| `products:detail:{sku}` | Single product | 300 s |
| `recommend:{user_id}:{skin_type}:{conditions}` | Recommendations | 300 s |

Cache is invalidated on product seed/sync.

---

### 3.9 Error Handling

All errors return a consistent JSON envelope:

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid email or password",
    "details": {}
  }
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 201 | Created |
| 400 | Bad request / validation |
| 401 | Unauthenticated |
| 403 | Insufficient role |
| 404 | Not found |
| 409 | Conflict (e.g. email already exists) |
| 422 | Unprocessable entity (schema error) |
| 500 | Internal server error |

---

## 4. Frontend

### 4.1 Tech Stack

| Concern | Library / Version |
|---------|------------------|
| Framework | React 18 |
| Build tool | Vite 7.3 |
| UI library | Ant Design 5.15 |
| State | Redux Toolkit + redux-persist |
| Routing | React Router v6 |
| HTTP | Axios |
| Face detection | MediaPipe face_mesh (in-browser WASM) |
| Charts | Apache ECharts |
| Mobile | Capacitor 6 (iOS + Android) |

---

### 4.2 Pages & Routes

| Route | Page | Auth Required | Description |
|-------|------|:---:|-------------|
| `/login` | Login.jsx | No | Email/password login |
| `/register` | Register.jsx | No | New account creation |
| `/` | Home.jsx | Yes | Dashboard with feature menu |
| `/analysis` | Analysis.jsx | Yes | Face capture + questionnaire |
| `/results` | Results.jsx | Yes | Diagnosis results + charts |
| `/recommendations` | Recommendations.jsx | Yes | Recommended products grid |
| `/product/:id` | ProductDetail.jsx | Yes | Product detail page |
| `/cart` | Cart.jsx | Yes | Shopping cart |
| `/checkout` | Checkout.jsx | Yes | Order placement |
| `/orders` | Orders.jsx | Yes | Order history |
| `/loyalty` | Loyalty.jsx | Yes | Points balance + rewards |
| `/profile` | Profile.jsx | Yes | Skin profile history |

Routes marked "Auth Required" are wrapped in a `PrivateRoute` component that redirects to `/login` if no token is found in Redux state.

---

### 4.3 State Management

Three Redux slices, all persisted via `redux-persist` to `localStorage` (or Capacitor Storage on mobile).

#### `authSlice`
```
token          — JWT access token
refreshToken   — JWT refresh token
user           — { id, email, role }
```
Actions: `setCredentials(token, refreshToken, user)`, `logout()`

#### `analysisSlice`
```
currentAnalysis  — latest { profile, inference_mode }
history          — last 10 analyses (auto-trimmed)
```
Actions: `setCurrentAnalysis(data)`, `addToHistory(entry)`, `clearAnalysis()`

#### `cartSlice`
```
items  — [{ id, name, price, quantity, image_url, ... }]
```
Actions: `addToCart(product)`, `removeFromCart(id)`, `updateQuantity(id, qty)`, `clearCart()`

---

### 4.4 API Client

`src/services/api.js` exports an Axios instance configured with:

```
baseURL  = VITE_API_URL  (e.g. http://localhost:8000/api/v1)
```

A request interceptor reads the token from Redux store and injects:
```
Authorization: Bearer <token>
```

**Exported functions:**

| Function | Method | Endpoint |
|----------|--------|----------|
| `login(email, password)` | POST | `/auth/login` |
| `register(email, password, fullName)` | POST | `/auth/signup` |
| `getMe()` | GET | `/auth/me` |
| `analyzeImage(base64, questionnaire)` | POST | `/analyze` |
| `getRecommendations(skinType, conditions)` | POST | `/recommend` |
| `getProfile(userId)` | GET | `/profile/{userId}` |
| `getProducts()` | GET | `/products` |
| `getProduct(sku)` | GET | `/products/{sku}` |
| `createOrder(data)` | POST | `/orders` |
| `getOrders()` | GET | `/orders` |
| `getOrder(id)` | GET | `/orders/{id}` |
| `getLoyalty(userId)` | GET | `/loyalty/{userId}` |

---

### 4.5 Face Capture

`FaceMeshCapture.jsx` guides the user through **5 poses** (center, left, right, up, down) using the device camera:

1. Opens `getUserMedia` (or Capacitor Camera on native).
2. Streams video to an off-screen canvas.
3. Runs MediaPipe `FaceMesh` on every frame.
4. When a valid face mesh is detected with a sufficient quality score:
   - Captures the frame as a base64 PNG.
   - Extracts 468 landmark coordinates.
5. After all 5 poses are captured, the best-quality frame + landmarks are sent to `/analyze`.

`face_quality_score` is derived from landmark spread — a tight cluster of landmarks on a small face region scores lower than a well-centered, large face.

---

## 5. Configuration

### Backend `.env`

```env
APP_NAME=SkinCare AI API
ENV=dev                        # dev | prod

# Server
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/skincare

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL_SECONDS=300

# JWT
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

# ML Model
MODEL_SAVED_PATH=app/models_artifacts/saved_model
MODEL_INPUT_SIZE=224
MODEL_SKIN_TYPES=Oily,Dry,Combination,Normal,Sensitive
MODEL_CONDITIONS=Acne,Hyperpigmentation,Uneven tone,Dehydration,None detected

# WooCommerce
WOOCOMMERCE_URL=https://drrashel.co.ke
WOOCOMMERCE_CONSUMER_KEY=ck_...
WOOCOMMERCE_CONSUMER_SECRET=cs_...
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 6. Running Locally

### Prerequisites
- Python 3.10+
- Node 18+
- PostgreSQL
- Redis

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Copy and fill in .env
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

### With Docker

```bash
cd backend
docker-compose up --build
```

Starts FastAPI, PostgreSQL, and Redis in containers.

---

## 7. Deployment

### Mobile Builds

```bash
cd frontend
npm run build

# iOS
npx cap sync ios
npx cap open ios          # Opens Xcode

# Android
npx cap sync android
npx cap open android      # Opens Android Studio
```

### Production Checklist

- [ ] Set `ENV=prod` in backend `.env`
- [ ] Replace `JWT_SECRET` with a strong random value
- [ ] Set `CORS` origins to specific domains (currently allows all)
- [ ] Use HTTPS for all endpoints
- [ ] Configure `VITE_API_URL` to production API URL before frontend build
- [ ] Run `alembic upgrade head` on production DB before deploying
- [ ] Ensure Redis is running and `REDIS_URL` is correct
- [ ] Place TensorFlow SavedModel at `MODEL_SAVED_PATH`

---

## 8. Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app entry point; CORS, exception handlers, lifespan hooks |
| `backend/app/api/v1/router.py` | Assembles all route modules |
| `backend/app/core/security.py` | JWT creation/validation, bcrypt hashing |
| `backend/app/core/deps.py` | `get_current_user` dependency; role enforcement |
| `backend/app/core/redis_client.py` | Redis connection + JSON cache helpers |
| `backend/app/services/inference.py` | TensorFlow model loading, image preprocessing, questionnaire fallback |
| `backend/app/services/recommendation.py` | Ingredient + keyword scoring engine |
| `backend/app/services/woocommerce_service.py` | WooCommerce REST client + product sync |
| `backend/alembic/` | Database migration scripts |
| `frontend/src/App.jsx` | Router setup + `PrivateRoute` wrapper |
| `frontend/src/store/index.js` | Redux store + redux-persist configuration |
| `frontend/src/services/api.js` | Axios instance + all API call functions |
| `frontend/src/pages/Analysis.jsx` | Face capture flow + questionnaire + calls `/analyze` |
| `frontend/src/components/FaceMeshCapture.jsx` | MediaPipe integration, 5-pose guided capture |
| `frontend/src/components/SkinCharts.jsx` | ECharts visualizations for skin analysis results |
