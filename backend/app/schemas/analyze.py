from pydantic import BaseModel, Field


class Questionnaire(BaseModel):
    skin_feel: str | None = None
    routine: str | None = None
    concerns: list[str] = Field(default_factory=list)


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
