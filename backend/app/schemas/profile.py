from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProfileRecord(BaseModel):
    timestamp: datetime
    skin_type: str
    conditions: list[str]
    confidence: float
    questionnaire: dict[str, Any] | None = None
    skin_type_scores: dict[str, float] | None = None
    condition_scores: dict[str, float] | None = None
    inference_mode: str | None = None


class ProfileUpdate(BaseModel):
    skin_type: str
    conditions: list[str]
    confidence: float


class ProfileResponse(BaseModel):
    user_id: str
    history: list[ProfileRecord]
