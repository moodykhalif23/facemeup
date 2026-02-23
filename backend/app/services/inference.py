import base64
import io
from functools import lru_cache

import numpy as np
from PIL import Image

from app.core.config import settings
from app.schemas.analyze import SkinProfile


@lru_cache(maxsize=1)
def _load_model():
    import tensorflow as tf

    return tf.saved_model.load(settings.model_saved_path)


def _decode_image(image_base64: str) -> np.ndarray:
    raw = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    image = image.resize((settings.model_input_size, settings.model_input_size))
    arr = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def _default_profile() -> SkinProfile:
    return SkinProfile(
        skin_type="Combination",
        conditions=["Acne", "Dehydration"],
        confidence=0.81,
    )


def run_skin_inference(image_base64: str) -> tuple[SkinProfile, str]:
    skin_labels = [v.strip() for v in settings.model_skin_types.split(",") if v.strip()]
    condition_labels = [v.strip() for v in settings.model_conditions.split(",") if v.strip()]

    try:
        import tensorflow as tf

        model = _load_model()
        batch = _decode_image(image_base64)
        infer = model.signatures.get("serving_default")
        if infer is None:
            return _default_profile(), "savedmodel_missing_signature"

        tensor = tf.convert_to_tensor(batch, dtype=tf.float32)
        input_args = infer.structured_input_signature[1]
        if input_args:
            input_key = next(iter(input_args.keys()))
            outputs = infer(**{input_key: tensor})
        else:
            outputs = infer(tensor)

        values = list(outputs.values())
        if not values:
            return _default_profile(), "savedmodel_empty_output"

        probs = np.array(values[0].numpy()[0], dtype=np.float32)
        if probs.size == 0:
            return _default_profile(), "savedmodel_empty_probs"

        top_skin_idx = int(np.argmax(probs[: len(skin_labels)])) if len(probs) >= len(skin_labels) else 0
        skin_type = skin_labels[top_skin_idx] if skin_labels else "Unknown"

        cond_start = len(skin_labels)
        cond_scores = probs[cond_start : cond_start + len(condition_labels)]
        conditions = [
            condition_labels[i]
            for i, score in enumerate(cond_scores)
            if i < len(condition_labels) and float(score) >= 0.35 and condition_labels[i] != "None detected"
        ]
        if not conditions:
            conditions = ["None detected"]

        confidence = float(np.max(probs))
        return (
            SkinProfile(
                skin_type=skin_type,
                conditions=conditions,
                confidence=round(confidence, 4),
            ),
            "server_savedmodel",
        )
    except Exception:
        return _default_profile(), "server_savedmodel_fallback"
