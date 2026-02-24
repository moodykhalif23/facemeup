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


def _default_profile() -> SkinProfile:
    """Fallback profile when model inference fails"""
    return SkinProfile(
        skin_type="Combination",
        conditions=["Dehydration"],
        confidence=0.65,
    )


def run_skin_inference(image_base64: str, landmarks: Optional[List[Dict]] = None) -> tuple[SkinProfile, str]:
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
        
        return (
            SkinProfile(
                skin_type=skin_type,
                conditions=conditions,
                confidence=round(confidence, 4),
                face_quality_score=round(face_quality_score, 4) if face_quality_score else None,
            ),
            "server_savedmodel",
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Inference error: {e}")
        return _default_profile(), "server_savedmodel_fallback"
