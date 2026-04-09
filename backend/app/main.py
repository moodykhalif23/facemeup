import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.limiter import limiter

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.errors import register_exception_handlers
from app.services.bootstrap import seed_products
from app.services.seed_admin import seed_admin
from app.services.training_scheduler import process_user_captured_images, refresh_training_assets


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        seed_products(db)
        seed_admin(db)
    except Exception:
        logger.exception("Startup seed skipped because database is unavailable")
    finally:
        db.close()

    # Start APScheduler for training data sync
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_user_captured_images,
        trigger="interval",
        hours=6,
        id="training_data_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        refresh_training_assets,
        trigger="interval",
        hours=24,
        id="training_manifest_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Training data scheduler started (runs every 6 hours)")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Training data scheduler stopped")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Rate limiting — raises 429 with Retry-After header on breach
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origins are read from CORS_ORIGINS in .env
# Development default: * (all origins)
# Production: set CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
_wildcard = _origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=not _wildcard,  # credentials require explicit origins
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health")
def health() -> dict:
    """Probe DB, Redis, and SavedModel — used by load balancers and uptime monitors."""
    from pathlib import Path
    checks: dict[str, str] = {}

    # Database
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    # Redis
    try:
        from app.core.redis_client import get_redis_client
        r = get_redis_client()
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    # SavedModel
    model_path = Path(settings.model_saved_path) / "saved_model.pb"
    checks["model"] = "ok" if model_path.exists() else "missing"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    status_code = 200 if overall == "ok" else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": overall, **checks}, status_code=status_code)


app.include_router(api_router, prefix=settings.api_v1_prefix)
