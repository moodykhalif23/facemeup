from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.inference import run_skin_inference
from app.services.profile_service import append_profile


router = APIRouter()


@router.post("", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    profile, mode = run_skin_inference(payload.image_base64)
    append_profile(db, current_user.id, profile.skin_type, profile.conditions, profile.confidence)
    return AnalyzeResponse(profile=profile, inference_mode=mode)
