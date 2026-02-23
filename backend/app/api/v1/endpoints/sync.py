from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.sync import BitmojiSyncRequest, BitmojiSyncResponse
from app.services.profile_service import append_profile


router = APIRouter()


@router.post("/bitmoji", response_model=BitmojiSyncResponse)
def sync_bitmoji(
    payload: BitmojiSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BitmojiSyncResponse:
    append_profile(db, current_user.id, payload.skin_type, payload.conditions, confidence=0.95)
    return BitmojiSyncResponse(synced=True)
