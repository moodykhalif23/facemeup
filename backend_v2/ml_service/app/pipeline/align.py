import cv2
import numpy as np

from .landmarks import FivePoint

# ArcFace canonical 5-point template for a 112x112 face crop. Scaled to
# arbitrary output size inside `align_face`.
_ARCFACE_112 = np.array(
    [
        [38.2946, 51.6963],  # left eye
        [73.5318, 51.5014],  # right eye
        [56.0252, 71.7366],  # nose tip
        [41.5493, 92.3655],  # left mouth
        [70.7299, 92.2041],  # right mouth
    ],
    dtype=np.float32,
)


def align_face(image_bgr: np.ndarray, landmarks: FivePoint, size: int = 256) -> np.ndarray:
    """Warp the input image so that the canonical 5 landmarks match a fixed template.

    Uses similarity transform (scale + rotation + translation, no shear).
    Output is a `size x size` BGR crop centered on the face.
    """
    if size < 64:
        raise ValueError("size too small")
    src = landmarks.as_array()
    dst = _ARCFACE_112 * (size / 112.0)

    M, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)
    if M is None:
        raise RuntimeError("alignment failed: could not estimate transform")
    return cv2.warpAffine(image_bgr, M, (size, size), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
