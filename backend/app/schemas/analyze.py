from pydantic import BaseModel, Field


class Questionnaire(BaseModel):
    skin_feel: str | None = None
    skin_texture: str | None = None
    moisture_level: str | None = None
    oil_levels: str | None = None
    routine: str | None = None
    routine_other: str | None = None
    concerns: list[str] = Field(default_factory=list)
    gender: str | None = None
    age: int | None = None


class FaceLandmark(BaseModel):
    x: float
    y: float
    z: float = 0.0


class AnalyzeRequest(BaseModel):
    image_base64: str
    questionnaire: Questionnaire | None = None
    landmarks: list[FaceLandmark] | None = None


class SkinProfile(BaseModel):
    skin_type: str
    conditions: list[str]
    confidence: float
    face_quality_score: float | None = None
    skin_type_scores: dict[str, float] | None = None   # probability per skin type
    condition_scores: dict[str, float] | None = None   # probability per condition


class AnalyzeResponse(BaseModel):
    profile: SkinProfile
    inference_mode: str
    disclaimer: str = (
        "This analysis is informational and does not replace professional "
        "dermatology advice. Consult a qualified dermatologist for medical concerns."
    )
