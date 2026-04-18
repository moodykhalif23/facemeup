"""Skin segmentation.

Phase 1 uses a YCrCb skin-colour threshold as a fallback so the pipeline runs
without model artefacts. Phase 4 swaps in a BiSeNet face-parsing ONNX model
(class indices 1,2,3,4,5,6,7,10,11,12,13 = skin-adjacent regions; we keep class 1
"skin" and optionally 10 "nose"). The public API stays the same.
"""

import cv2
import numpy as np


def skin_mask_ycrcb(image_bgr: np.ndarray) -> np.ndarray:
    """Return a binary uint8 mask (0/255) covering plausible skin pixels.

    Thresholds are drawn from the classic Hsu/Abdel-Mottaleb range; they work
    reasonably across Fitzpatrick I–VI. Not a substitute for BiSeNet, but good
    enough to exclude obvious non-skin (hair shadows, clothing) in Phase 1.
    """
    ycrcb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)

    # Morphological closing removes small holes (e.g. specular highlights).
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask


def segment_skin(image_bgr: np.ndarray, onnx_session=None) -> np.ndarray:
    """Return a binary skin mask for the aligned face crop.

    If an ONNX BiSeNet face-parsing session is supplied, use it; otherwise fall
    back to YCrCb thresholding.
    """
    if onnx_session is not None:
        return _segment_bisenet(image_bgr, onnx_session)
    return skin_mask_ycrcb(image_bgr)


def _segment_bisenet(image_bgr: np.ndarray, session) -> np.ndarray:
    """Run BiSeNet face-parsing ONNX → binary skin mask.

    The concrete session handle is passed from `runner.py`; we keep the logic
    here so Phase 4 just drops the ONNX file into place.
    """
    h, w = image_bgr.shape[:2]
    input_size = 512
    resized = cv2.resize(image_bgr, (input_size, input_size), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    tensor = ((rgb - mean) / std).transpose(2, 0, 1)[None, ...]

    input_name = session.get_inputs()[0].name
    out = session.run(None, {input_name: tensor.astype(np.float32)})[0]
    # BiSeNet output is (1, C, H, W); class 1 == facial skin.
    cls = np.argmax(out[0], axis=0).astype(np.uint8)
    skin = np.where(cls == 1, 255, 0).astype(np.uint8)
    return cv2.resize(skin, (w, h), interpolation=cv2.INTER_NEAREST)
