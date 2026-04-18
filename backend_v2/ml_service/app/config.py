from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ML_", env_file=".env", extra="ignore")

    env: str = "development"
    port: int = 8000

    models_dir: Path = Path("/app/models")
    face_detector_model: str = "retinaface_mnet.onnx"
    segmenter_model: str = "face_parsing_bisenet.onnx"
    classifier_model: str = "skin_classifier_mobilenet.onnx"

    input_size: int = 224
    skin_types: tuple[str, ...] = ("Oily", "Dry", "Combination", "Normal", "Sensitive")
    conditions: tuple[str, ...] = (
        "Acne",
        "Dryness",
        "Oiliness",
        "Hyperpigmentation",
        "Wrinkles",
        "Redness",
    )

    onnx_providers: tuple[str, ...] = ("CPUExecutionProvider",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
