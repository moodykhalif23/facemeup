"""
Creates the default admin account on first startup if it does not exist.
Credentials are read from ADMIN_EMAIL / ADMIN_PASSWORD env vars (see config.py).
"""
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User

logger = logging.getLogger(__name__)


def seed_admin(db: Session) -> None:
    existing = db.execute(
        select(User).where(User.email == settings.admin_email)
    ).scalar_one_or_none()

    if existing:
        # Ensure it keeps admin role in case it was downgraded by accident
        if existing.role != "admin":
            existing.role = "admin"
            db.commit()
            logger.info("Admin role restored for %s", settings.admin_email)
        return

    admin = User(
        id=uuid4().hex,
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        full_name="System Admin",
        role="admin",
    )
    db.add(admin)
    db.commit()
    logger.info(
        "Default admin created — email: %s  password: %s",
        settings.admin_email,
        settings.admin_password,
    )
