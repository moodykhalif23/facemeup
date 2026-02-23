# Backend

## Run locally
1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -e .[dev]`
4. `copy .env.example .env`
5. `alembic upgrade head`
6. `uvicorn app.main:app --reload`

## API
- Swagger: `http://localhost:8000/docs`
- Health: `GET /health`

## Auth flow
1. `POST /api/v1/auth/signup`
2. `POST /api/v1/auth/login`
3. Send `Authorization: Bearer <token>` for protected endpoints.
