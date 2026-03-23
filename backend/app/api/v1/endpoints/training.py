import base64
import json
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.training_metadata import export_training_metadata_csv

router = APIRouter()

TRAINING_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "ml", "data", "user_captured"
)

VALID_SKIN_TYPES = {"Oily", "Dry", "Combination", "Normal", "Sensitive"}


class TrainingSubmitRequest(BaseModel):
    image_base64: str
    skin_type: str
    conditions: list[str] = []
    questionnaire: dict | None = None


def _save_training_image(image_base64: str, skin_type: str) -> str:
    """Save a captured face image to the user_captured training directory."""
    # Normalise skin type to a safe folder name
    safe_skin_type = skin_type if skin_type in VALID_SKIN_TYPES else "Unknown"
    dest_dir = os.path.join(TRAINING_DIR, safe_skin_type)
    os.makedirs(dest_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(dest_dir, filename)

    image_bytes = base64.b64decode(image_base64)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    return filepath


def _save_training_metadata(filepath: str, payload: TrainingSubmitRequest, user_id: int | None) -> None:
    metadata = {
        "skin_type": payload.skin_type,
        "conditions": payload.conditions,
        "questionnaire": payload.questionnaire,
        "user_id": user_id,
        "captured_at": datetime.utcnow().isoformat() + "Z",
    }
    meta_path = f"{filepath}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)


@router.post("/submit")
def submit_training_image(
    payload: TrainingSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Accept a captured face image for model training.
    Image is saved to ml/data/user_captured/{skin_type}/ for inclusion in next training run.
    """
    def _save_all() -> None:
        filepath = _save_training_image(payload.image_base64, payload.skin_type)
        _save_training_metadata(filepath, payload, current_user.id if current_user else None)
        export_training_metadata_csv(TRAINING_DIR, os.path.join(TRAINING_DIR, "metadata.csv"))

    background_tasks.add_task(_save_all)
    return {"status": "queued", "message": "Image submitted for training"}
