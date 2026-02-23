# SkinCare AI Platform

Backend-first scaffold derived from `technical.docx`.

## Monorepo Layout
- `backend/`: FastAPI + PostgreSQL + Redis + TensorFlow-serving stubs
- `frontend/`: React Native (Expo) starter shell for future module build-out

## Quick Start
1. Copy `backend/.env.example` to `backend/.env`.
2. Run: `docker compose up --build`.
3. Backend docs: `http://localhost:8000/docs`.

## Current Status
- Backend endpoints scaffolded for:
  - `/api/v1/analyze`
  - `/api/v1/recommend`
  - `/api/v1/profile`
  - `/api/v1/orders`
  - `/api/v1/sync/bitmoji`
  - `/api/v1/loyalty`
  - `/api/v1/products`
- Recommendation engine includes rule-based ingredient mapping baseline.
- Frontend initialized as module placeholders, ready for deep implementation next.
