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
    # Convert landmarks to dict format if provided
    landmarks = None
    if payload.landmarks:
        landmarks = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in payload.landmarks]
    
    questionnaire = payload.questionnaire.model_dump() if payload.questionnaire else None
    profile, mode = run_skin_inference(payload.image_base64, landmarks, questionnaire)
    append_profile(db, current_user.id, profile.skin_type, profile.conditions, profile.confidence)
    return AnalyzeResponse(profile=profile, inference_mode=mode)
