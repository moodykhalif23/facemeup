import base64
from io import BytesIO

import cv2
import numpy as np
import pytest
from PIL import Image


def _synthetic_face(size: int = 512) -> np.ndarray:
    """Return a BGR uint8 image containing a skin-coloured oval with face-like features.

    Not a real face; just enough structure for Haar to reject (good — exercises
    the failure path) or for a landmarks-supplied run to succeed.
    """
    rng = np.random.default_rng(42)
    img = np.full((size, size, 3), 240, dtype=np.uint8)  # light background

    # Skin oval (warm beige, Fitzpatrick III-ish)
    cv2.ellipse(img, (size // 2, size // 2), (size // 3, int(size * 0.42)),
                0, 0, 360, (165, 185, 220), -1)

    # Eyes
    cv2.ellipse(img, (int(size * 0.38), int(size * 0.45)), (25, 12), 0, 0, 360, (70, 60, 60), -1)
    cv2.ellipse(img, (int(size * 0.62), int(size * 0.45)), (25, 12), 0, 0, 360, (70, 60, 60), -1)

    # Nose
    cv2.line(img, (size // 2, int(size * 0.47)), (size // 2, int(size * 0.62)),
             (140, 160, 195), 4)

    # Mouth
    cv2.ellipse(img, (size // 2, int(size * 0.72)), (40, 10), 0, 0, 180, (90, 90, 140), 2)

    # Add a bit of grain so CLAHE/WB have something to work with
    noise = rng.integers(-6, 6, size=img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def _b64_encode(bgr: np.ndarray) -> str:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    buf = BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode("ascii")


@pytest.fixture(scope="session")
def synthetic_face_bgr() -> np.ndarray:
    return _synthetic_face()


@pytest.fixture(scope="session")
def synthetic_face_b64(synthetic_face_bgr) -> str:
    return _b64_encode(synthetic_face_bgr)


@pytest.fixture(scope="session")
def fake_mediapipe_landmarks() -> list[dict]:
    """Generate a plausible 468-point FaceMesh set for the synthetic face.

    Only the 5 key indices (eyes, nose, mouth corners) need to be accurate for
    our purposes; the rest are filled with interpolated positions.
    """
    lm = [{"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(468)]
    def set_pt(i: int, x: float, y: float) -> None:
        lm[i] = {"x": x, "y": y, "z": 0.0}

    # Left eye cluster
    set_pt(33, 0.34, 0.45)
    set_pt(133, 0.42, 0.45)
    set_pt(159, 0.38, 0.44)
    set_pt(145, 0.38, 0.46)
    # Right eye cluster
    set_pt(263, 0.66, 0.45)
    set_pt(362, 0.58, 0.45)
    set_pt(386, 0.62, 0.44)
    set_pt(374, 0.62, 0.46)
    # Nose tip
    set_pt(1, 0.50, 0.62)
    # Mouth corners
    set_pt(61, 0.42, 0.72)
    set_pt(291, 0.58, 0.72)

    return lm
