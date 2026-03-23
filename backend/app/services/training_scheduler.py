"""
Training data scheduler.

Runs a background job that periodically moves images from
ml/data/user_captured/ into the main training data folders so the
model can be retrained with real user face captures.
"""
import logging
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)
from app.services.training_metadata import export_training_metadata_csv

# Base paths (relative to the backend/ directory)
USER_CAPTURED_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "ml", "data", "user_captured"
)
TRAINING_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "ml", "data", "ham10000"
)
# Minimum new images before we bother moving them
MIN_NEW_IMAGES = 5


def process_user_captured_images() -> dict:
    """
    Move user-captured images from the staging folder into the main
    training data directory, organised by skin type subfolder.
    Returns a summary of files processed.
    """
    if not os.path.exists(USER_CAPTURED_DIR):
        logger.info("No user_captured directory yet – skipping training data sync")
        return {"processed": 0, "skipped": 0}

    processed = 0
    skipped = 0

    for skin_type in os.listdir(USER_CAPTURED_DIR):
        src_folder = os.path.join(USER_CAPTURED_DIR, skin_type)
        if not os.path.isdir(src_folder):
            continue

        images = [
            f for f in os.listdir(src_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if len(images) < MIN_NEW_IMAGES:
            logger.info(
                "Skin type '%s' has only %d new images (min %d) – skipping",
                skin_type, len(images), MIN_NEW_IMAGES
            )
            skipped += len(images)
            continue

        dest_folder = os.path.join(TRAINING_DATA_DIR, f"user_{skin_type}")
        os.makedirs(dest_folder, exist_ok=True)

        for img_name in images:
            src_path = os.path.join(src_folder, img_name)
            dest_path = os.path.join(dest_folder, img_name)
            try:
                shutil.move(src_path, dest_path)
                processed += 1
                meta_src = f"{src_path}.json"
                if os.path.exists(meta_src):
                    meta_dest = f"{dest_path}.json"
                    try:
                        shutil.move(meta_src, meta_dest)
                    except Exception as exc:
                        logger.warning("Failed to move %s: %s", meta_src, exc)
            except Exception as exc:
                logger.warning("Failed to move %s: %s", src_path, exc)
                skipped += 1

    logger.info(
        "Training data sync complete — processed: %d, skipped: %d",
        processed, skipped
    )
    try:
        export_training_metadata_csv(
            TRAINING_DATA_DIR,
            os.path.join(TRAINING_DATA_DIR, "user_captured_metadata.csv"),
        )
    except Exception as exc:
        logger.warning("Failed to export user metadata CSV: %s", exc)
    return {"processed": processed, "skipped": skipped}
