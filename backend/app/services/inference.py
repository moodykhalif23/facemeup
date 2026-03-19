import base64
import io
from functools import lru_cache
from typing import Optional, List, Dict

import numpy as np
from PIL import Image, ImageEnhance
import cv2

from app.core.config import settings
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
    "wrinkles": "Uneven tone",
    "redness": "Sensitive",
    "dryness": "Dehydration",
    "oiliness": "Acne",
}


def _questionnaire_profile(questionnaire: Optional[Dict]) -> SkinProfile:
    """Derive skin profile from questionnaire when model is unavailable"""
    q = questionnaire or {}
    skin_type = _SKIN_FEEL_MAP.get((q.get("skin_feel") or "").lower(), "Combination")
    raw_concerns = q.get("concerns") or []
    conditions = list({_CONCERN_MAP[c] for c in raw_concerns if c in _CONCERN_MAP})
    if not conditions:
        conditions = ["None detected"]

    confidence = 0.72
    all_skin = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
    all_cond  = ["Acne", "Hyperpigmentation", "Uneven tone", "Dehydration", "None detected"]

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


def run_skin_inference(
    image_base64: str,
    landmarks: Optional[List[Dict]] = None,
    questionnaire: Optional[Dict] = None,
) -> tuple[SkinProfile, str]:
    """
    Run skin analysis inference on the provided image
    
    Args:
        image_base64: Base64 encoded image string
        landmarks: Optional MediaPipe face landmarks for better face extraction
        
    Returns:
        Tuple of (SkinProfile, inference_mode)
    """
    skin_labels = [v.strip() for v in settings.model_skin_types.split(",") if v.strip()]
    condition_labels = [v.strip() for v in settings.model_conditions.split(",") if v.strip()]

    # Calculate face quality score if landmarks provided
    face_quality_score = None
    if landmarks:
        face_quality_score = face_processor.get_face_quality_score(landmarks)

    try:
        import tensorflow as tf

        model = _load_model()
        batch = _preprocess_image(image_base64, landmarks)
        infer = model.signatures.get("serving_default")
        if infer is None:
            return _questionnaire_profile(questionnaire), "savedmodel_missing_signature"

        tensor = tf.convert_to_tensor(batch, dtype=tf.float32)
        input_args = infer.structured_input_signature[1]
        if input_args:
            input_key = next(iter(input_args.keys()))
            outputs = infer(**{input_key: tensor})
        else:
            outputs = infer(tensor)

        values = list(outputs.values())
        if not values:
            return _questionnaire_profile(questionnaire), "savedmodel_empty_output"

        probs = np.array(values[0].numpy()[0], dtype=np.float32)
        if probs.size == 0:
            return _questionnaire_profile(questionnaire), "savedmodel_empty_probs"

        # Determine skin type (first N labels)
        top_skin_idx = int(np.argmax(probs[: len(skin_labels)])) if len(probs) >= len(skin_labels) else 0
        skin_type = skin_labels[top_skin_idx] if skin_labels else "Unknown"
        skin_confidence = float(probs[top_skin_idx]) if top_skin_idx < len(probs) else 0.5

        # Determine conditions (remaining labels)
        cond_start = len(skin_labels)
        cond_scores = probs[cond_start : cond_start + len(condition_labels)]
        
        # Use adaptive threshold based on confidence
        # Higher threshold for more confident predictions
        threshold = 0.40 if skin_confidence > 0.7 else 0.35
        
        conditions = [
            condition_labels[i]
            for i, score in enumerate(cond_scores)
            if i < len(condition_labels) 
            and float(score) >= threshold 
            and condition_labels[i] != "None detected"
        ]
        
        # If no conditions detected, mark as "None detected"
        if not conditions:
            conditions = ["None detected"]
        
        # Use the highest confidence score as overall confidence
        confidence = float(max(skin_confidence, np.max(cond_scores) if len(cond_scores) > 0 else 0.5))
        
        skin_type_scores = {
            skin_labels[i]: round(float(probs[i]), 4)
            for i in range(len(skin_labels))
            if i < len(probs)
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
            "server_savedmodel",
        )
    except Exception as e:
        print(f"Inference error: {e}")
        return _questionnaire_profile(questionnaire), "questionnaire_fallback"
