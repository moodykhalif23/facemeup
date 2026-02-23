from datetime import datetime

from pydantic import BaseModel


class ProfileRecord(BaseModel):
    timestamp: datetime
    skin_type: str
    conditions: list[str]
    confidence: float


class ProfileUpdate(BaseModel):
    skin_type: str
    conditions: list[str]
    confidence: float


class ProfileResponse(BaseModel):
    user_id: str
    history: list[ProfileRecord]
