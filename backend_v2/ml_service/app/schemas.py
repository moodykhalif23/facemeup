from typing import Any

from pydantic import BaseModel, Field


class Landmark(BaseModel):
    x: float
    y: float
    z: float = 0.0


class AnalyzeRequest(BaseModel):
    image_base64: str = Field(..., description="Raw base64 (no data: prefix)")
    landmarks: list[Landmark] | None = None
    questionnaire: dict[str, Any] = Field(default_factory=dict)


class ConditionScore(BaseModel):
    label: str
    probability: float


class HeatmapPayload(BaseModel):
    label: str
    image_base64: str


class AnalyzeResponse(BaseModel):
    skin_type: str
    skin_type_scores: dict[str, float]
    conditions: list[str]
    condition_scores: dict[str, float]
    confidence: float
    inference_mode: str
    heatmaps: list[HeatmapPayload] = Field(default_factory=list)
    disclaimer: str = (
        "This analysis is informational and does not replace professional dermatology advice."
    )


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    providers: list[str]
