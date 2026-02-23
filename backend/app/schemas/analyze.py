from pydantic import BaseModel, Field


class Questionnaire(BaseModel):
    skin_feel: str | None = None
    routine: str | None = None
    concerns: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    image_base64: str
    questionnaire: Questionnaire | None = None


class SkinProfile(BaseModel):
    skin_type: str
    conditions: list[str]
    confidence: float


class AnalyzeResponse(BaseModel):
    profile: SkinProfile
    inference_mode: str
