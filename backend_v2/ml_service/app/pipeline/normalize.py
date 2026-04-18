import cv2
import numpy as np


def clahe_on_luminance(image_bgr: np.ndarray, clip_limit: float = 2.0, tile: int = 8) -> np.ndarray:
    """Apply CLAHE to the L channel of the LAB colour space.

    Improves local contrast without the noise amplification of global histogram eq.
    Spec §3.3: lighting is the largest error source; CLAHE is the recommended mitigation.
    """
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile, tile))
    l_eq = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l_eq, a, b]), cv2.COLOR_LAB2BGR)


def grey_world_white_balance(image_bgr: np.ndarray) -> np.ndarray:
    """Grey-world white balance: scale each channel so its mean matches the global mean.

    Cheap, assumption-free (apart from grey-world), handles most phone-camera colour shifts.
    """
    img = image_bgr.astype(np.float32)
    means = img.reshape(-1, 3).mean(axis=0)
    grey = float(means.mean())
    if grey <= 1e-6:
        return image_bgr
    gain = grey / np.maximum(means, 1e-6)
    balanced = np.clip(img * gain, 0, 255).astype(np.uint8)
    return balanced


def normalize(image_bgr: np.ndarray) -> np.ndarray:
    """Full illumination normalization: white balance first, then CLAHE on L."""
    wb = grey_world_white_balance(image_bgr)
    return clahe_on_luminance(wb)
