from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import JWTError, decode_access_token
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_token",
                message="Token subject is missing",
            )
    except JWTError as exc:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
            message="Could not validate credentials",
        ) from exc

    user = db.execute(select(User).where(User.email == subject)).scalar_one_or_none()
    if not user:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="user_not_found",
            message="Authenticated user no longer exists",
        )
    return user
