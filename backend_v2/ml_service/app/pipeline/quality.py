"""Image-quality gates for phone-captured selfies.

Cheap visible-light heuristics designed to reject inputs that we *know* will
produce unreliable analysis: blurry shots, severely under/over-exposed shots,
and images where the face occupies a tiny fraction of the frame. Returning a
warning early lets the frontend ask the user to retake before we burn Groq
tokens on a bad shot.

Each check returns a `QualityIssue` (or None). The caller decides whether to
hard-fail or continue with degraded confidence — see runner.assess_quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np


Severity = Literal["warn", "block"]


@dataclass(frozen=True)
class QualityIssue:
    code: str            # stable machine-readable code
    severity: Severity   # "warn" → continue; "block" → 422 to client
    message: str         # human-readable, shown to the user


# Tunable thresholds. Conservative defaults — calibrate on real phone captures
# once we have a labelled set. Bumping `BLUR_LAPLACIAN_MIN` aggressively cuts
# false negatives; lowering hurts agreement with Bitmoji.
BLUR_LAPLACIAN_MIN = 60.0     # Laplacian variance under this → blocked as blurry.
BLUR_LAPLACIAN_WARN = 120.0   # Below this → warn but continue.
EXPOSURE_MEAN_MIN = 40.0       # Avg luminance under this → underexposed.
EXPOSURE_MEAN_MAX = 220.0      # Avg luminance above this → overexposed / blown.
EXPOSURE_CLIP_FRAC = 0.25      # >25% pixels at 0 or 255 → severe clipping.
FACE_AREA_MIN = 0.06           # Face bbox area < 6% of frame → too far.
FACE_AREA_WARN = 0.10          # Below this → warn.


def assess_blur(image_bgr: np.ndarray) -> QualityIssue | None:
    """Variance of Laplacian — standard cheap focus measure."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if var < BLUR_LAPLACIAN_MIN:
        return QualityIssue(
            code="image_blurry",
            severity="block",
            message=("The photo looks blurry. Hold the phone steady, tap the "
                     "face on screen to focus, and retake."),
        )
    if var < BLUR_LAPLACIAN_WARN:
        return QualityIssue(
            code="image_soft",
            severity="warn",
            message=("Image is slightly soft — results may be less accurate. "
                     "For best results, retake with sharper focus."),
        )
    return None


def assess_exposure(image_bgr: np.ndarray) -> QualityIssue | None:
    """Mean luminance + clipped-pixel ratio."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    total = gray.size
    clipped = float(np.count_nonzero((gray == 0) | (gray == 255))) / total

    if mean < EXPOSURE_MEAN_MIN:
        return QualityIssue(
            code="image_underexposed",
            severity="block",
            message=("The photo is too dark. Move into brighter, even light "
                     "(facing a window works well) and retake."),
        )
    if mean > EXPOSURE_MEAN_MAX or clipped > EXPOSURE_CLIP_FRAC:
        return QualityIssue(
            code="image_overexposed",
            severity="block",
            message=("Bright spots are washing out skin detail. Move out of "
                     "direct sunlight or harsh flash and retake."),
        )
    return None


def assess_face_coverage(
    image_shape: tuple[int, int],
    face_bbox: tuple[float, float, float, float] | None,
) -> QualityIssue | None:
    """Face area as fraction of full frame."""
    if face_bbox is None:
        return None
    h, w = image_shape[:2]
    if h == 0 or w == 0:
        return None
    x0, y0, x1, y1 = face_bbox
    bw = max(0.0, x1 - x0)
    bh = max(0.0, y1 - y0)
    frac = (bw * bh) / float(w * h)

    if frac < FACE_AREA_MIN:
        return QualityIssue(
            code="face_too_small",
            severity="block",
            message=("Your face is too small in the frame. Hold the phone "
                     "closer so your face fills most of the shot."),
        )
    if frac < FACE_AREA_WARN:
        return QualityIssue(
            code="face_small",
            severity="warn",
            message=("Your face is small in the frame — fine details may be "
                     "missed. Move the camera closer for best results."),
        )
    return None


def assess_all(
    image_bgr: np.ndarray,
    face_bbox: tuple[float, float, float, float] | None = None,
) -> list[QualityIssue]:
    """Run every check and return all issues found (empty list = pass)."""
    issues: list[QualityIssue] = []
    for check in (
        lambda: assess_blur(image_bgr),
        lambda: assess_exposure(image_bgr),
        lambda: assess_face_coverage(image_bgr.shape, face_bbox),
    ):
        issue = check()
        if issue is not None:
            issues.append(issue)
    return issues


def has_blocking(issues: list[QualityIssue]) -> bool:
    return any(i.severity == "block" for i in issues)
