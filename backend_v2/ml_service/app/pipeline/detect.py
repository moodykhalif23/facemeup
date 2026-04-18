"""Face detection + 5-point landmarks.

Priority order:
  1. Landmarks supplied by the client (MediaPipe FaceMesh from the frontend).
  2. RetinaFace ONNX model, if installed.
  3. OpenCV Haar cascade as a last-resort bbox → heuristic 5-point fallback.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .landmarks import FivePoint, from_mediapipe


@dataclass(frozen=True)
class Detection:
    bbox: tuple[int, int, int, int]   # x0, y0, x1, y1
    landmarks: FivePoint
    source: str                        # "client" | "retinaface" | "haar"


def detect(
    image_bgr: np.ndarray,
    client_landmarks: list[dict] | None = None,
    retinaface_session=None,
) -> Detection | None:
    h, w = image_bgr.shape[:2]

    if client_landmarks:
        lm = from_mediapipe(client_landmarks, w, h)
        if lm is not None:
            bbox = _bbox_from_5pt(lm, w, h)
            return Detection(bbox=bbox, landmarks=lm, source="client")

    if retinaface_session is not None:
        det = _detect_retinaface(image_bgr, retinaface_session)
        if det is not None:
            return det

    return _detect_haar(image_bgr)


def _bbox_from_5pt(lm: FivePoint, w: int, h: int) -> tuple[int, int, int, int]:
    pts = lm.as_array()
    x0 = float(pts[:, 0].min())
    x1 = float(pts[:, 0].max())
    y0 = float(pts[:, 1].min())
    y1 = float(pts[:, 1].max())
    face_w = x1 - x0
    face_h = y1 - y0
    pad_x = face_w * 0.6
    pad_y_top = face_h * 1.2
    pad_y_bot = face_h * 0.7
    return (
        int(max(0, x0 - pad_x)),
        int(max(0, y0 - pad_y_top)),
        int(min(w, x1 + pad_x)),
        int(min(h, y1 + pad_y_bot)),
    )


def _detect_haar(image_bgr: np.ndarray) -> Detection | None:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.py"
    # cv2.data.haarcascades points at ".../cv2/data/"; the actual file is .xml.
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    lm = _estimate_5pt_from_bbox(x, y, w, h)
    return Detection(bbox=(int(x), int(y), int(x + w), int(y + h)), landmarks=lm, source="haar")


def _estimate_5pt_from_bbox(x: int, y: int, w: int, h: int) -> FivePoint:
    """Rough 5-point estimate from a frontal face bbox.

    Anchors are drawn from the ArcFace canonical template normalised to the
    bounding box. Accuracy is poor for tilted faces; good enough to keep the
    pipeline alive when MediaPipe and RetinaFace are both unavailable.
    """
    def at(nx: float, ny: float) -> tuple[float, float]:
        return x + nx * w, y + ny * h

    return FivePoint(
        left_eye=at(0.341, 0.461),
        right_eye=at(0.656, 0.459),
        nose=at(0.500, 0.640),
        left_mouth=at(0.370, 0.825),
        right_mouth=at(0.630, 0.824),
    )


def _detect_retinaface(image_bgr: np.ndarray, session) -> Detection | None:
    """Stub for the RetinaFace ONNX inference path.

    The standard insightface RetinaFace ONNX expects (1,3,H,W) with ImageNet
    normalisation and returns bboxes + 5-point landmarks + scores. A full
    implementation (anchor decoding, NMS) lands in Phase 4 when we pin a
    specific model file. For now we return None so the Haar fallback runs.
    """
    _ = (image_bgr, session)
    return None
