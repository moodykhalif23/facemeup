"""Patch extraction from an aligned face crop.

Spec §4: forehead (oiliness), L/R cheek (acne/pigmentation), nose (sebum),
chin (hormonal acne). Coordinates are defined on the ArcFace canonical template
(112x112) and scaled to whatever `size` the alignment stage used.
"""

from dataclasses import dataclass

import cv2
import numpy as np

# (cx, cy, half_w, half_h) in the 112×112 canonical template.
_CANONICAL_BOXES: dict[str, tuple[float, float, float, float]] = {
    "forehead":   (56.0, 32.0, 22.0, 14.0),
    "left_cheek": (35.0, 72.0, 14.0, 16.0),
    "right_cheek":(77.0, 72.0, 14.0, 16.0),
    "nose":       (56.0, 68.0, 10.0, 18.0),
    "chin":       (56.0, 100.0, 16.0, 10.0),
}


@dataclass(frozen=True)
class Patch:
    region: str
    image: np.ndarray      # BGR uint8
    skin_ratio: float      # fraction of pixels inside the skin mask; 0..1


def extract_patches(
    aligned_bgr: np.ndarray,
    skin_mask: np.ndarray,
    patch_size: int = 224,
) -> list[Patch]:
    """Crop the five canonical patches from an aligned face and resize to `patch_size`.

    `aligned_bgr` is assumed square (size × size); `skin_mask` must match.
    """
    if aligned_bgr.shape[:2] != skin_mask.shape[:2]:
        raise ValueError("mask/image shape mismatch")
    h, w = aligned_bgr.shape[:2]
    if h != w:
        raise ValueError("aligned face must be square")
    scale = h / 112.0

    patches: list[Patch] = []
    for region, (cx, cy, hw, hh) in _CANONICAL_BOXES.items():
        x0 = max(0, int(round((cx - hw) * scale)))
        y0 = max(0, int(round((cy - hh) * scale)))
        x1 = min(w, int(round((cx + hw) * scale)))
        y1 = min(h, int(round((cy + hh) * scale)))
        if x1 <= x0 or y1 <= y0:
            continue
        crop = aligned_bgr[y0:y1, x0:x1]
        mask_crop = skin_mask[y0:y1, x0:x1]
        skin_ratio = float(np.count_nonzero(mask_crop)) / mask_crop.size
        resized = cv2.resize(crop, (patch_size, patch_size), interpolation=cv2.INTER_AREA)
        patches.append(Patch(region=region, image=resized, skin_ratio=skin_ratio))

    return patches
