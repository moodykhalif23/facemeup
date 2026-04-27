from __future__ import annotations

import cv2
import numpy as np

from skin_training.data.precompute import _fallback_face_crop_from_bytes


def test_fallback_face_crop_returns_square_uint8_bgr() -> None:
    image = np.zeros((320, 200, 3), dtype=np.uint8)
    image[:120, :, :] = (20, 40, 60)
    image[120:, :, :] = (180, 200, 220)

    ok, encoded = cv2.imencode(".jpg", image)
    assert ok

    crop = _fallback_face_crop_from_bytes(encoded.tobytes(), 256)

    assert crop.shape == (256, 256, 3)
    assert crop.dtype == np.uint8
    # The portrait crop should preserve some of the upper-region content rather
    # than collapsing to the lower half of the frame.
    assert float(crop[:64].mean()) < float(crop[-64:].mean())
