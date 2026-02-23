from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import AppError
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_service import append_profile, get_profile_history


router = APIRouter()


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    if user_id != current_user.id:
        raise AppError(status_code=403, code="forbidden", message="Cannot access another user profile")

    history = get_profile_history(db, user_id)
    return ProfileResponse(user_id=user_id, history=history)


@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(
    user_id: str,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    if user_id != current_user.id:
        raise AppError(status_code=403, code="forbidden", message="Cannot update another user profile")

    append_profile(db, user_id, payload.skin_type, payload.conditions, payload.confidence)
    history = get_profile_history(db, user_id)
    return ProfileResponse(user_id=user_id, history=history)
