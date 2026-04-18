from dataclasses import dataclass

import numpy as np

# MediaPipe Face Mesh (468-point) key indices we need to reduce to the
# 5-point canonical set (left-eye, right-eye, nose, left-mouth, right-mouth)
# used by RetinaFace / ArcFace alignment.
MP_LEFT_EYE = (33, 133, 159, 145)  # outer, inner, top, bottom
MP_RIGHT_EYE = (263, 362, 386, 374)
MP_NOSE_TIP = 1
MP_LEFT_MOUTH = 61
MP_RIGHT_MOUTH = 291


@dataclass(frozen=True)
class FivePoint:
    """5-point face landmarks in pixel coordinates (x, y)."""

    left_eye: tuple[float, float]
    right_eye: tuple[float, float]
    nose: tuple[float, float]
    left_mouth: tuple[float, float]
    right_mouth: tuple[float, float]

    def as_array(self) -> np.ndarray:
        return np.array(
            [self.left_eye, self.right_eye, self.nose, self.left_mouth, self.right_mouth],
            dtype=np.float32,
        )


def from_mediapipe(landmarks: list[dict], width: int, height: int) -> FivePoint | None:
    """Convert MediaPipe FaceMesh normalized landmarks to 5-point pixel coords.

    The frontend sends landmarks as [{"x": 0..1, "y": 0..1, "z": float}, ...].
    We require the full 468-point set (or 478 with iris) to extract canonical points.
    """
    if not landmarks or len(landmarks) < 468:
        return None

    def pt(idx: int) -> tuple[float, float]:
        lm = landmarks[idx]
        return float(lm["x"]) * width, float(lm["y"]) * height

    def centroid(indices: tuple[int, ...]) -> tuple[float, float]:
        xs = [landmarks[i]["x"] for i in indices]
        ys = [landmarks[i]["y"] for i in indices]
        return float(np.mean(xs)) * width, float(np.mean(ys)) * height

    return FivePoint(
        left_eye=centroid(MP_LEFT_EYE),
        right_eye=centroid(MP_RIGHT_EYE),
        nose=pt(MP_NOSE_TIP),
        left_mouth=pt(MP_LEFT_MOUTH),
        right_mouth=pt(MP_RIGHT_MOUTH),
    )


def from_retinaface(pts: np.ndarray) -> FivePoint:
    """Wrap a (5, 2) array from RetinaFace ONNX output."""
    if pts.shape != (5, 2):
        raise ValueError(f"expected (5,2) landmarks, got {pts.shape}")
    return FivePoint(
        left_eye=(float(pts[0, 0]), float(pts[0, 1])),
        right_eye=(float(pts[1, 0]), float(pts[1, 1])),
        nose=(float(pts[2, 0]), float(pts[2, 1])),
        left_mouth=(float(pts[3, 0]), float(pts[3, 1])),
        right_mouth=(float(pts[4, 0]), float(pts[4, 1])),
    )
