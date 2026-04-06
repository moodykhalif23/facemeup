import base64
import io
import logging
from functools import lru_cache
from typing import Optional, List, Dict

import numpy as np
from PIL import Image, ImageEnhance
import cv2

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.schemas.analyze import SkinProfile
from app.services.face_processor import face_processor


@lru_cache(maxsize=1)
def _load_model():
    import tensorflow as tf

    return tf.saved_model.load(settings.model_saved_path)


def _preprocess_image(image_base64: str, landmarks: Optional[List[Dict]] = None) -> np.ndarray:
    """
    Preprocess image for better skin analysis accuracy
    - Decode base64
    - Extract face region using landmarks (if provided)
    - Convert to RGB
    - Enhance contrast and sharpness
    - Resize to model input size
    - Normalize pixel values
    """
    if landmarks:
        # Use face processor for landmark-based extraction
        arr = face_processor.process_image_with_landmarks(image_base64, landmarks)
        return np.expand_dims(arr, axis=0)
    
    # Fallback to original preprocessing
    raw = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Increase sharpness for better detail detection
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)
    
    # Resize to model input size
    image = image.resize((settings.model_input_size, settings.model_input_size), Image.Resampling.LANCZOS)
    
    # Convert to array and normalize
    arr = np.asarray(image, dtype=np.float32) / 255.0
    
    return np.expand_dims(arr, axis=0)


_SKIN_FEEL_MAP = {
    "oily": "Oily",
    "dry": "Dry",
    "combination": "Combination",
    "normal": "Normal",
    "sensitive": "Sensitive",
}

_CONCERN_MAP = {
    "acne": "Acne",
    "dark_spots": "Hyperpigmentation",
    "wrinkles": "Wrinkles",         # now a first-class model label
    "redness": "Redness",           # now a first-class model label
    "dryness": "Dehydration",
    "oiliness": "Acne",
    "sensitivity": "Redness",
    "dark_circles": "Hyperpigmentation",
    "blackheads": "Acne",
    "pigmentation": "Hyperpigmentation",
    "pores": "Acne",
}


def _derive_skin_type_from_new_fields(q: Dict) -> str:
    scores = {
        "Oily": 0,
        "Dry": 0,
        "Combination": 0,
        "Normal": 0,
        "Sensitive": 0,
    }

    oil = (q.get("oil_levels") or "").lower()
    moisture = (q.get("moisture_level") or "").lower()
    texture = (q.get("skin_texture") or "").lower()

    if oil == "very_oily":
        scores["Oily"] += 2
    elif oil == "slightly_oily":
        scores["Oily"] += 1
        scores["Combination"] += 1
    elif oil == "mixed":
        scores["Combination"] += 2

    if moisture == "dry":
        scores["Dry"] += 2
    elif moisture == "hydrated":
        scores["Normal"] += 1
    elif moisture == "balanced":
        scores["Normal"] += 1
        scores["Combination"] += 1

    if texture == "rough":
        scores["Dry"] += 1
        scores["Sensitive"] += 1
    elif texture == "smooth":
        scores["Normal"] += 1
    elif texture == "mixed":
        scores["Combination"] += 1

    raw_concerns = set((q.get("concerns") or []))
    if "sensitivity" in raw_concerns or "redness" in raw_concerns:
        scores["Sensitive"] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "Combination"


def _questionnaire_profile(questionnaire: Optional[Dict]) -> SkinProfile:
    """Derive skin profile from questionnaire when model is unavailable"""
    q = questionnaire or {}
    skin_feel = (q.get("skin_feel") or "").lower()
    skin_type = _SKIN_FEEL_MAP.get(skin_feel) if skin_feel else _derive_skin_type_from_new_fields(q)
    skin_type = skin_type or "Combination"
    raw_concerns = q.get("concerns") or []
    conditions = list({_CONCERN_MAP[c] for c in raw_concerns if c in _CONCERN_MAP})
    if not conditions:
        conditions = ["None detected"]

    confidence = 0.72
    all_skin = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
    all_cond  = ["Acne", "Hyperpigmentation", "Uneven tone", "Dehydration", "Wrinkles", "Redness", "None detected"]

    # Synthesise scores: detected label gets `confidence`, rest share remainder equally
    remainder = round((1.0 - confidence) / (len(all_skin) - 1), 4)
    skin_type_scores = {s: (round(confidence, 4) if s == skin_type else remainder) for s in all_skin}

    cond_detected = set(conditions) - {"None detected"}
    remainder_c = round((1.0 - 0.65 * len(cond_detected)) / max(1, len(all_cond) - len(cond_detected)), 4)
    condition_scores = {
        c: (0.65 if c in cond_detected else remainder_c)
        for c in all_cond
    }
    if "None detected" in conditions:
        condition_scores["None detected"] = round(confidence, 4)

    return SkinProfile(
        skin_type=skin_type,
        conditions=conditions,
        confidence=confidence,
        skin_type_scores=skin_type_scores,
        condition_scores=condition_scores,
    )


def _run_single_inference(
    infer,
    batch: np.ndarray,
    skin_labels: List[str],
    condition_labels: List[str],
) -> Optional[np.ndarray]:
    """Run the SavedModel signature on a single preprocessed batch.
    Returns raw probability vector or None on error.
    """
    import tensorflow as tf

    tensor = tf.convert_to_tensor(batch, dtype=tf.float32)
    input_args = infer.structured_input_signature[1]
    try:
        if input_args:
            input_key = next(iter(input_args.keys()))
            outputs = infer(**{input_key: tensor})
        else:
            outputs = infer(tensor)
        values = list(outputs.values())
        if not values:
            return None
        probs = np.array(values[0].numpy()[0], dtype=np.float32)
        return probs if probs.size else None
    except Exception as exc:
        logger.debug("Single inference failed: %s", exc)
        return None


def _aggregate_zone_probs(
    all_probs: List[np.ndarray],
    skin_labels: List[str],
) -> np.ndarray:
    """Average probability vectors across zones.

    Skin-type scores are averaged uniformly; condition scores are
    taken as the per-condition maximum across zones (spec §4 intent:
    a condition showing up in *any* zone should be surfaced).
    """
    n_skin = len(skin_labels)
    stacked = np.stack(all_probs, axis=0)          # [zones, num_classes]

    skin_avg  = stacked[:, :n_skin].mean(axis=0)   # average skin type probabilities
    cond_max  = stacked[:, n_skin:].max(axis=0)    # max condition probability per zone

    return np.concatenate([skin_avg, cond_max])


def run_skin_inference(
    image_base64: str,
    landmarks: Optional[List[Dict]] = None,
    questionnaire: Optional[Dict] = None,
) -> tuple[SkinProfile, str]:
    """Run skin analysis using multi-zone patch inference (spec §4).

    Pipeline:
      1. Extract per-zone patches (forehead, cheeks, nose, chin) from landmarks
      2. Run model inference on each patch independently
      3. Aggregate: average skin-type scores, max condition scores across zones
      4. Fall back to full-face inference if zone extraction fails
      5. Fall back to questionnaire if model is unavailable
    """
    skin_labels = [v.strip() for v in settings.model_skin_types.split(",") if v.strip()]
    condition_labels = [v.strip() for v in settings.model_conditions.split(",") if v.strip()]

    face_quality_score = None
    if landmarks:
        face_quality_score = face_processor.get_face_quality_score(landmarks)

    try:
        import tensorflow as tf

        model = _load_model()
        infer = model.signatures.get("serving_default")
        if infer is None:
            return _questionnaire_profile(questionnaire), "savedmodel_missing_signature"

        # ── Multi-zone patch inference ───────────────────────────────────
        inference_mode = "server_savedmodel"
        all_probs: List[np.ndarray] = []

        if landmarks:
            raw_image = face_processor.decode_base64_image(image_base64)
            raw_image = face_processor.align_face(raw_image, landmarks)
            raw_image = face_processor.normalize_illumination(raw_image)

            patches = face_processor.extract_skin_patches(raw_image, landmarks)
            for zone_name, patch in patches.items():
                batch = np.expand_dims(patch, axis=0)
                probs = _run_single_inference(infer, batch, skin_labels, condition_labels)
                if probs is not None and len(probs) == len(skin_labels) + len(condition_labels):
                    all_probs.append(probs)
                    logger.debug("Zone '%s' inference ok, probs shape %s", zone_name, probs.shape)

            if all_probs:
                inference_mode = f"server_savedmodel_zones:{len(all_probs)}"

        # ── Full-face fallback when no zone patches available ────────────
        if not all_probs:
            batch = _preprocess_image(image_base64, landmarks)
            probs = _run_single_inference(infer, batch, skin_labels, condition_labels)
            if probs is None or len(probs) == 0:
                return _questionnaire_profile(questionnaire), "savedmodel_empty_output"
            all_probs = [probs]
            inference_mode = "server_savedmodel_fullface"

        # ── Aggregate ────────────────────────────────────────────────────
        final_probs = _aggregate_zone_probs(all_probs, skin_labels) if len(all_probs) > 1 else all_probs[0]

        top_skin_idx = int(np.argmax(final_probs[: len(skin_labels)]))
        skin_type = skin_labels[top_skin_idx] if skin_labels else "Unknown"
        skin_confidence = float(final_probs[top_skin_idx])

        cond_start  = len(skin_labels)
        cond_scores = final_probs[cond_start : cond_start + len(condition_labels)]

        # Adaptive threshold: higher confidence → tighter threshold
        threshold = 0.40 if skin_confidence > 0.7 else 0.35

        conditions = [
            condition_labels[i]
            for i, score in enumerate(cond_scores)
            if i < len(condition_labels)
            and float(score) >= threshold
            and condition_labels[i] != "None detected"
        ]
        if not conditions:
            conditions = ["None detected"]

        confidence = float(max(skin_confidence, np.max(cond_scores) if len(cond_scores) > 0 else 0.5))

        skin_type_scores = {
            skin_labels[i]: round(float(final_probs[i]), 4)
            for i in range(len(skin_labels))
            if i < len(final_probs)
        }
        condition_scores = {
            condition_labels[i]: round(float(cond_scores[i]), 4)
            for i in range(len(condition_labels))
            if i < len(cond_scores)
        }

        return (
            SkinProfile(
                skin_type=skin_type,
                conditions=conditions,
                confidence=round(confidence, 4),
                face_quality_score=round(face_quality_score, 4) if face_quality_score else None,
                skin_type_scores=skin_type_scores,
                condition_scores=condition_scores,
            ),
            inference_mode,
        )
    except Exception as e:
        logger.warning("Inference error, falling back to questionnaire: %s", e)
        return _questionnaire_profile(questionnaire), "questionnaire_fallback"
