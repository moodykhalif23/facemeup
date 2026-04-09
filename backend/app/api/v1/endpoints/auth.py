from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.limiter import limiter

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse, UserResponse


router = APIRouter()


def _issue_token_pair(user: User, db: Session) -> TokenResponse:
    access_token = create_access_token(user.id)
    refresh_token, token_id = create_refresh_token(user.id)

    db.add(
        RefreshToken(
            id=token_id,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
            revoked_at=None,
        )
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
    )


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> UserResponse:
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise AppError(status_code=409, code="email_exists", message="Email already registered")

    user = User(
        id=uuid4().hex,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="customer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError(status_code=401, code="invalid_credentials", message="Invalid email or password")

    return _issue_token_pair(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        decoded = decode_token(payload.refresh_token)
    except JWTError as exc:
        raise AppError(status_code=401, code="invalid_refresh_token", message="Invalid refresh token") from exc

    if decoded.get("type") != "refresh":
        raise AppError(status_code=401, code="invalid_refresh_token", message="Refresh token required")

    token_id = decoded.get("jti")
    user_id = decoded.get("sub")
    if not token_id or not user_id:
        raise AppError(status_code=401, code="invalid_refresh_token", message="Malformed refresh token")

    token_row = db.execute(select(RefreshToken).where(RefreshToken.id == token_id)).scalar_one_or_none()
    if not token_row or token_row.revoked_at is not None:
        raise AppError(status_code=401, code="invalid_refresh_token", message="Refresh token revoked")

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AppError(status_code=401, code="user_not_found", message="User not found")

    token_row.revoked_at = datetime.utcnow()
    db.add(token_row)
    db.commit()

    return _issue_token_pair(user, db)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        created_at=current_user.created_at,
    )
