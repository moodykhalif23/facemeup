# Skincare AI — System Analysis: Findings & Gaps

> Deep analysis of frontend (React), backend (FastAPI), and ML pipeline (EfficientNetB0).  
> Date: 2026-04-08

---

## Executive Summary

The system is architecturally coherent but has **critical gaps in the ML pipeline, several security vulnerabilities, missing feedback loops, and dead/incomplete features** that collectively undermine model accuracy, user trust, and production reliability. The most severe issue: **the SavedModel is not deployed** — every user currently gets questionnaire-fallback responses, not real ML inference.

---

## 1. ML / Model — Findings & Gaps

### 1.1 Critical: No Model Deployed in Production
- `backend/app/models_artifacts/` is **empty** — no SavedModel present.
- `inference.py` silently falls back to questionnaire heuristics (`mode: questionnaire_fallback`).
- All users receive heuristic-only results. ML model is trained but never serving.

### 1.2 Training ↔ Inference Preprocessing Mismatch
| Step | Training | Inference |
|------|----------|-----------|
| Illumination normalization (CLAHE) | ❌ Not applied | ✅ Applied |
| Contrast + sharpness enhancement | ❌ Not applied | ✅ Applied (1.2×, 1.3×) |
| Face alignment (MediaPipe) | ❌ Not applied | ✅ Applied if landmarks |
| Resize method | Bilinear (TF) | LANCZOS (PIL) |

Model was trained on plain JPEGs; inference applies transformations the model never saw → distribution shift → unreliable predictions.

### 1.3 Broken Feedback Loop
- `POST /analyze/feedback` stores `confirmed`/`rejected` in DB — **that's where the loop ends**.
- No pipeline reads feedback records to retrain or fine-tune.
- `training_scheduler.py` exists as a stub; no actual retraining job runs.
- 9,789 training samples collected but never re-ingested.

### 1.4 Severe Class Imbalance — Unaddressed
- 68.1% of training data is "Normal + None detected".
- No class weights, no oversampling/undersampling.
- Model likely biased toward predicting "Normal" regardless of input.

### 1.5 Fundamental Domain Gap
- **Training domain**: HAM10000 — close-up dermatoscopic lesion images (clinical).
- **Inference domain**: full-face selfies from phone cameras.
- These are visually incompatible domains. Generalization is untested and highly suspect.
- Label mapping is speculative (e.g., `melanoma → Sensitive`, `basal cell carcinoma → Oily`).

### 1.6 Questionnaire Override Is Untrained Heuristic
- When model confidence < 0.60, questionnaire heuristics override the model prediction.
- `_derive_skin_type_from_new_fields()` uses hardcoded point rules — never validated on real data.
- Questionnaire-stated concerns are **always appended** to conditions regardless of model score → forced false positives.

### 1.7 Phase 2 Fine-Tuning Did Not Improve the Model
- Phase 2 initial val loss: 0.525 (worse than Phase 1 final: 0.328).
- Early stopping triggered at epoch 4/15 — fine-tuning added no benefit.
- Learning rate (1e-5) may be too low; unfreezing only top 30 layers may be insufficient.

### 1.8 No Bias / Fairness Audit
- `config.yaml` references `fitzpatrick_stratification: true` — **not implemented**.
- No demographic stratification in evaluation.
- HAM10000 skews toward lighter skin tones; model fairness across Fitzpatrick types unknown.

### 1.9 Multi-Zone Aggregation Is Heuristic, Not Learned
- Zone scores aggregated via: avg(skin-type), max(conditions).
- Not trained or validated; max-condition pooling inflates condition detections.

### 1.10 Face Quality Score Unused
- `face_quality_score` computed and returned but never used to gate or weight predictions.
- Low-quality captures (blurry, dark) pass through with the same weight as high-quality ones.

---

## 2. Backend — Findings & Gaps

### 2.1 Security: Missing Image Size Validation (Critical)
- `AnalyzeRequest.image_base64` has no `max_length` constraint.
- A user can POST a 10 GB base64 string → OOM crash / server DoS.
- `base64.b64decode()` has no try-except → crash on malformed input.
- **File**: `backend/app/schemas/analyze.py`

### 2.2 Security: No Rate Limiting
- `/auth/login` — brute-force possible, no throttling.
- `/analyze` — ML inference is expensive; unlimited calls per user → compute DoS.
- No `slowapi`, `limits`, or middleware rate limiter in place.

### 2.3 Security: Wildcard CORS
- `CORS_ORIGINS=*` set in `.env`.
- Any origin can make credentialed requests to the API.

### 2.4 Security: Refresh Token Not Checked at Request Time
- Revoked refresh tokens remain valid; logout doesn't invalidate in-flight JWT if `jti` not checked per request.

### 2.5 No Pagination on List Endpoints
- `GET /admin/users`, `GET /admin/orders`, `GET /admin/reports` — return **all records**.
- No `skip`/`limit` params. Could load millions of rows.
- **File**: `backend/app/api/v1/endpoints/admin.py`

### 2.6 ML Inference Blocks Uvicorn Worker
- `/analyze` runs ML inference synchronously on the web worker.
- Blocks the async event loop; should use `BackgroundTasks` or a task queue.
- **File**: `backend/app/api/v1/endpoints/analyze.py`

### 2.7 Health Check Is a Stub
- `GET /health` returns static `{"status": "ok"}` — does not probe DB, Redis, or model.
- Load balancers report healthy even when dependencies are down.
- **File**: `backend/app/main.py`

### 2.8 No Audit Logging
- User deletions, role changes, analysis deletions — no audit table or event log.

### 2.9 No Soft Deletes
- `DELETE /admin/users/{id}` and `DELETE /admin/reports/{id}` permanently destroy records.
- No `deleted_at` column; no recovery path.

### 2.10 WooCommerce Order Fulfillment Gap
- Orders created in app DB but status never synced back from WooCommerce.
- `sync.py` pushes products to WooCommerce; no reverse sync for order status.

### 2.11 Loyalty Reward Redemption Not Implemented
- `GET /loyalty` lists rewards but no `POST /loyalty/redeem` endpoint exists.
- Users can see rewards but cannot spend points.

### 2.12 Model Cache Never Invalidates
- `_load_model()` uses `@lru_cache(maxsize=1)` — updated SavedModel won't load until server restart.
- **File**: `backend/app/services/inference.py`

### 2.13 Transaction Rollback Missing on Errors
- Most endpoints lack explicit rollback on DB session exceptions.
- Partial writes can leave DB in inconsistent state.

---

## 3. Frontend — Findings & Gaps

### 3.1 Security: XSS via `dangerouslySetInnerHTML`
- `ProductDetail.jsx:175` renders `product.description` as raw HTML without sanitization.
- Stored XSS vector if backend data is ever compromised.
- **Fix**: wrap with `DOMPurify.sanitize()`

### 3.2 No Token Refresh / No 401 Handler
- `refreshToken` stored in Redux but never used.
- Expired JWT causes silent API failures — no re-auth prompt.
- No Axios response interceptor for 401.
- **File**: `frontend/src/services/api.js`

### 3.3 Training Submission Errors Silently Swallowed
- `Analysis.jsx` uses `Promise.allSettled` for `/training/submit` — errors only `console.warn`.
- Training data may silently fail to reach backend with no indication.

### 3.4 Hardcoded Mock Data Fallback (Loyalty)
- `Loyalty.jsx` error handler sets state to `{ points: 850, tier: 'Gold', ... }`.
- Users see fabricated data when the endpoint fails.

### 3.5 Hardcoded Product Count in Admin UI
- `AdminProducts.jsx:283` says `"This wipes all 106 local products..."` — hardcoded, not dynamic.

### 3.6 Dead Code
| File | Status |
|------|--------|
| `frontend/src/pages/Checkout.jsx` | Only redirects to `/cart` |
| `frontend/src/pages/Orders.jsx` | Only redirects to `/cart` |
| `frontend/src/components/WebCamera.jsx` | Never imported |
| `frontend/src/components/FaceMeshAnalysis.jsx` | Never used |

### 3.7 No Image Fallback Placeholder
- Product images that fail to load disappear silently — no `onError` handler.

### 3.8 No Pagination on Profile History
- `GET /profile/{userId}` fetches all analyses at once.

### 3.9 Missing User-Facing Features
- No password reset / forgot-password flow.
- No user profile editing (name, email).
- No user-facing order history (admin-only currently).
- No offline/PWA mode despite Capacitor being installed.

---

## 4. Cross-Cutting Concerns

| Concern | Impact |
|---------|--------|
| No structured logging | Logs not parseable; hard to debug in production |
| No request ID / tracing | Cannot correlate frontend error to backend log |
| No test coverage | Only 2 basic tests; no integration or E2E tests |
| Secrets in `.env` tracked by git | JWT secret, Postgres password, WooCommerce keys exposed |
| No model versioning / registry | Checkpoints timestamped but no semantic version tracking |
| `inference_mode` not surfaced to user | Users don't know if result is AI or heuristic fallback |

---

## 5. Structured Task List

### P0 — Blocks Core Functionality

- [ ] **ML-001** Export `phase2_best.keras` → SavedModel, deploy to `backend/app/models_artifacts/saved_model/`
- [ ] **ML-002** Fix preprocessing mismatch: apply CLAHE + contrast/sharpness during training OR remove from inference path
- [ ] **BE-001** Add `max_length` to `AnalyzeRequest.image_base64`; wrap `base64.b64decode` in try-except
- [ ] **BE-002** Add per-user rate limiting: `/analyze` (10/hour), `/auth/login` (5/min) via `slowapi`
- [ ] **FE-001** Add Axios 401 response interceptor → dispatch `logout()` and redirect to `/login`

### P1 — Security & Reliability

- [ ] **BE-003** Fix wildcard CORS: set explicit `CORS_ORIGINS` list for production
- [ ] **BE-004** Add `skip`/`limit` pagination to all admin list endpoints
- [ ] **BE-005** Move ML inference off the request thread (use `BackgroundTasks` or return job ID + polling)
- [ ] **BE-006** Fix `/health` to probe DB connection, Redis ping, and SavedModel file presence
- [ ] **BE-007** Add soft-delete (`deleted_at`) to users and reports; replace hard-delete endpoints
- [ ] **FE-002** Sanitize `product.description` with DOMPurify before `dangerouslySetInnerHTML`
- [ ] **FE-003** Replace hardcoded mock fallback in `Loyalty.jsx` with real error state

### P2 — Model Quality & Feedback Loop

- [ ] **ML-003** Add class weights to training loss (inverse frequency) to address 68% Normal imbalance
- [ ] **ML-004** Build feedback export pipeline: query confirmed/rejected records → CSV → retrain trigger
- [ ] **ML-005** Audit HAM10000 label mappings against domain expert; validate or replace speculative mappings
- [ ] **ML-006** Gate inference on `face_quality_score`: reject captures below threshold, prompt user to retake
- [ ] **ML-007** Remove questionnaire concern force-append; only add concerns corroborated by model score ≥ threshold
- [ ] **ML-008** Surface `inference_mode` in Results UI ("Analysed by AI" vs "Based on your answers")
- [ ] **ML-009** Collect face selfie training data to supplement/replace HAM10000 for skin-type classification

### P3 — Feature Completion

- [ ] **FE-004** Implement token refresh using stored `refreshToken` (call `/auth/refresh` before retry)
- [ ] **FE-005** Implement forgot-password / reset-password flow
- [ ] **FE-006** Add `onError` fallback image to all product `<img>` tags
- [ ] **FE-007** Add pagination to profile history (10 per page)
- [ ] **FE-008** Fix hardcoded `"106 local products"` → `products.length` in `AdminProducts.jsx:283`
- [ ] **FE-009** Remove dead files: `Checkout.jsx`, `Orders.jsx`, `WebCamera.jsx`, `FaceMeshAnalysis.jsx`
- [ ] **BE-008** Implement `POST /loyalty/redeem` endpoint
- [ ] **BE-009** Add WooCommerce order status reverse sync (webhook → update order in DB)
- [ ] **BE-010** Add audit log table for all destructive admin actions

### P4 — Observability & Code Quality

- [ ] **BE-011** Add structured JSON logging with `X-Request-ID` middleware
- [ ] **BE-012** Add `POST /admin/model/reload` to force model cache invalidation without restart
- [ ] **BE-013** Add explicit DB session rollback in all endpoint exception handlers
- [ ] **ML-010** Implement Fitzpatrick skin-tone stratification in `evaluate.py`
- [ ] **ML-011** Tune Phase 2 fine-tuning: try LR 5e-5, unfreeze top 60 layers, or use cyclic LR schedule
- [ ] **INFRA-001** Remove `.env` from git tracking; add to `.gitignore`; document required env vars in README
- [ ] **TEST-001** Add integration tests for `/auth/login`, `/analyze`, `/recommend`, `/loyalty/{id}`

---

## Quick Reference: Critical Files

| Task | Primary File |
|------|-------------|
| ML-001 | `backend/ml/export_savedmodel.py` |
| ML-002 | `backend/ml/train_pipeline.py`, `backend/app/services/inference.py` |
| ML-004 | `backend/app/api/v1/endpoints/training.py` |
| BE-001 | `backend/app/schemas/analyze.py` |
| BE-002 | `backend/app/main.py` |
| BE-004 | `backend/app/api/v1/endpoints/admin.py` |
| BE-005 | `backend/app/api/v1/endpoints/analyze.py` |
| BE-006 | `backend/app/main.py` |
| FE-001 | `frontend/src/services/api.js` |
| FE-002 | `frontend/src/pages/ProductDetail.jsx` |
| FE-003 | `frontend/src/pages/Loyalty.jsx` |
| FE-008 | `frontend/src/pages/admin/AdminProducts.jsx` |
