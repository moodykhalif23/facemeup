# SkinCare AI Platform

Backend-first scaffold derived from `technical.docx` with Phase 2 hardening.

## Monorepo Layout
- `backend/`: FastAPI + PostgreSQL + Redis + Alembic
- `frontend/`: React Native (Expo) connected to auth/analyze/recommend/profile APIs

## Quick Start
1. Copy `backend/.env.example` to `backend/.env`.
2. Run: `docker compose up --build`.
3. Backend docs: `http://localhost:8000/docs`.
4. In `frontend/`, install deps and run Expo.

## Hardened Backend
- Real DB persistence for users, profiles, orders, loyalty, and product catalog.
- Alembic migration at `backend/alembic/versions/0001_initial.py`.
- Redis caching for recommendation + product catalog endpoints.
- JWT auth guard dependencies for protected endpoints.
- Centralized error handling with normalized error payloads.
