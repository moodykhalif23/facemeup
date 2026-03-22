import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.errors import register_exception_handlers
from app.services.bootstrap import seed_products
from app.services.seed_admin import seed_admin
from app.services.training_scheduler import process_user_captured_images


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
    scheduler.start()
    logger.info("Training data scheduler started (runs every 6 hours)")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Training data scheduler stopped")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

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
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
