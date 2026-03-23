import base64
import io
from fastapi import APIRouter, Depends
from PIL import Image
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.inference import run_skin_inference
from app.services.profile_service import append_profile


router = APIRouter()

def _make_report_thumbnail(image_base64: str) -> str | None:
    try:
        raw = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        image.thumbnail((220, 220))
        buff = io.BytesIO()
        image.save(buff, format="JPEG", quality=75)
        thumb = base64.b64encode(buff.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{thumb}"
    except Exception:
        return None


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
    thumbnail = _make_report_thumbnail(payload.image_base64)
    append_profile(
        db,
        current_user.id,
        profile.skin_type,
        profile.conditions,
        profile.confidence,
        questionnaire=questionnaire,
        skin_type_scores=profile.skin_type_scores,
        condition_scores=profile.condition_scores,
        inference_mode=mode,
        report_image_base64=thumbnail,
    )
    return AnalyzeResponse(profile=profile, inference_mode=mode)
