from fastapi import APIRouter

from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile_service import append_profile, get_profile_history


router = APIRouter()


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str) -> ProfileResponse:
    history = get_profile_history(user_id)
    return ProfileResponse(user_id=user_id, history=history)


@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(user_id: str, payload: ProfileUpdate) -> ProfileResponse:
    append_profile(user_id, payload.skin_type, payload.conditions, payload.confidence)
    history = get_profile_history(user_id)
    return ProfileResponse(user_id=user_id, history=history)
