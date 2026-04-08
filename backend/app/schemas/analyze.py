import base64

from pydantic import BaseModel, Field, field_validator


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


_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB decoded


class AnalyzeRequest(BaseModel):
    image_base64: str
    questionnaire: Questionnaire | None = None
    landmarks: list[FaceLandmark] | None = None
    # All pose captures submitted during the session (up to 5)
    capture_images: list[str] | None = None

    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, v: str) -> str:
        if "," in v:
            v = v.split(",", 1)[1]
        try:
            raw = base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("image_base64 is not valid base64")
        if len(raw) < 1024:
            raise ValueError("image_base64 is too small to be a valid image")
        if len(raw) > _MAX_IMAGE_BYTES:
            raise ValueError(
                f"Image too large ({len(raw) // 1024} KB). Maximum is {_MAX_IMAGE_BYTES // 1024} KB."
            )
        return v

    @field_validator("capture_images")
    @classmethod
    def validate_captures(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if len(v) > 5:
            raise ValueError("capture_images: maximum 5 captures per session")
        for i, img in enumerate(v):
            raw = img.split(",", 1)[1] if "," in img else img
            try:
                base64.b64decode(raw, validate=True)
            except Exception:
                raise ValueError(f"capture_images[{i}] is not valid base64")
        return v


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
    # condition_name → base64 JPEG Grad-CAM overlay (spec §7)
    # Only populated when a trained SavedModel is available
    heatmaps: dict[str, str] | None = None
    disclaimer: str = (
        "This analysis is informational and does not replace professional "
        "dermatology advice. Consult a qualified dermatologist for medical concerns."
    )
