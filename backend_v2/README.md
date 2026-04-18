# backend_v2 — Go API + PyTorch/ONNX ML sidecar

Clean-slate rewrite of the skincare backend following `docs/AI_Skin_Analysis_Platform.pdf`.
Runs **alongside** the existing `backend/` stack until cutover is complete.

## Architecture

```
client (frontend, unchanged)
        |
        v
Go API (chi)  ──────────────── auth, products, orders, loyalty, admin, sync
        │                      -> PostgreSQL (shared with backend/)
        │                      -> Redis (shared with backend/)
        │
        │   POST /v1/analyze   (HTTP/JSON, localhost compose network)
        v
Python ML sidecar (FastAPI)
        │
        └─ RetinaFace (ONNX)    face detect + landmarks
           BiSeNet   (ONNX)    skin segmentation
           MobileNetV3 (ONNX)  multi-label classifier (sigmoid + BCE)
           Grad-CAM            heatmaps
```

Why split: the Go API handles 35 of 36 endpoints (pure CRUD). Only `/analyze`
needs heavy Python ML libraries. HTTP localhost call adds ~1–3ms.

## Layout

```
backend_v2/
├── cmd/api/main.go          # Go entry point
├── internal/
│   ├── config/              # env loading
│   ├── server/              # chi router, middleware, handlers
│   ├── db/                  # pgx pool (Phase 5)
│   └── mlclient/            # HTTP client to ml-service (Phase 4)
├── ml_service/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # settings (pydantic-settings)
│   │   └── schemas.py       # request/response models
│   ├── models/              # .onnx artifacts (gitignored, released separately)
│   └── Dockerfile
├── ml_training/             # PyTorch training code (runs in Colab/Kaggle, not in prod)
├── docker-compose.yml       # additive to ../docker-compose.yml
├── Dockerfile               # Go API multi-stage build
└── .env.example
```

## Run locally

### 1. Start shared infra from the old stack

```bash
# From repo root
docker compose up -d db redis
```

### 2. Bring up backend_v2

```bash
cd backend_v2
docker compose up --build
```

Endpoints:
- Go API:       http://localhost:8012/health
- ML sidecar:   http://localhost:8013/healthz  (normally internal-only)
- Old backend:  http://localhost:8011 (still running, unaffected)

### 3. Point frontend at the new backend (when ready)

Set `VITE_API_URL=http://localhost:8012/api/v1` in `frontend/.env`.
During cutover, run both and route a % of traffic via reverse proxy.

## Phase plan

| Phase | Scope | Status |
|-------|-------|--------|
| 0     | Scaffolding: Go skeleton, Python sidecar skeleton, compose wiring | ✅ |
| 1     | Preprocessing: face detect → align → CLAHE → segment → patches    | ⏳ |
| 2     | Training infra: SCIN loader, augmentation, PyTorch trainer        | ⏳ |
| 3     | Baseline EfficientNet-B0 checkpoint + fairness audit (Colab)      | ⏳ |
| 4     | ONNX export + Grad-CAM + full `/v1/analyze` pipeline              | ⏳ |
| 5     | Port the other 35 endpoints to Go (auth, CRUD, WC sync, admin)    | ⏳ |
| 6     | Knowledge distillation → MobileNetV3 + INT8 quantization          | ⏳ |
| 7     | Cutover: shadow traffic → dual-run → retire old backend           | ⏳ |

## Decisions locked in

- Parallel build (this directory) next to `backend/`
- SCIN dataset + small labeled bootstrap for training
- Colab/Kaggle for training, CPU ONNX for inference
- Go for API layer, Python FastAPI sidecar for ML
- Keep existing Postgres schema; richer analysis output lands in a new `analysis_v2` table (Phase 4)

## Safety / compliance (spec §12)

Every `/analyze` response includes:

> This analysis is informational and does not replace professional dermatology advice.

Bias audit (Fitzpatrick I–VI) is part of Phase 3's evaluation. Images are not
retained by default; opt-in training data storage is a Phase 5 concern.
