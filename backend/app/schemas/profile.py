from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProfileRecord(BaseModel):
    id: int
    created_at: datetime
    skin_type: str
    conditions: list[str]
    confidence: float
    user_feedback: str | None = None
    questionnaire: dict[str, Any] | None = None
    skin_type_scores: dict[str, float] | None = None
    condition_scores: dict[str, float] | None = None
    inference_mode: str | None = None
    report_image_base64: str | None = None


class ProfileUpdate(BaseModel):
    skin_type: str
    conditions: list[str]
    confidence: float


class ProfileResponse(BaseModel):
    user_id: str
    history: list[ProfileRecord]
