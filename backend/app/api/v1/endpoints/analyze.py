import base64
import io
import logging
from fastapi import APIRouter, Depends, HTTPException
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.profile import SkinProfileHistory
from app.models.user import User
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.inference import run_skin_inference
from app.services.profile_service import append_profile

logger = logging.getLogger(__name__)


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


class FeedbackRequest(BaseModel):
    profile_id: int
    confirmed: bool  # True = user agrees with analysis, False = user rejects it


class FeedbackResponse(BaseModel):
    profile_id: int
    user_feedback: str


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """Store user confirmation/rejection of an analysis result.

    Spec §9 (Continuous Learning Feedback Loop): user confirms or rejects
    the AI-generated analysis so it can be fed back into the retraining
    pipeline.
    """
    record = db.get(SkinProfileHistory, payload.profile_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis record not found")
    if record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your analysis record")

    record.user_feedback = "confirmed" if payload.confirmed else "rejected"
    db.commit()
    logger.info(
        "User %s %s analysis %d",
        current_user.id,
        record.user_feedback,
        payload.profile_id,
    )
    return FeedbackResponse(profile_id=payload.profile_id, user_feedback=record.user_feedback)


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
