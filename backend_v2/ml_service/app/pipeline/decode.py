import base64
import binascii
from io import BytesIO

import cv2
import numpy as np
from PIL import ExifTags, Image


def decode_base64_image(b64: str) -> np.ndarray:
    """Decode a base64 image string to a BGR uint8 ndarray, applying EXIF orientation."""
    if not b64:
        raise ValueError("empty image payload")
    payload = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        raw = base64.b64decode(payload, validate=False)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"invalid base64: {e}") from e

    try:
        img = Image.open(BytesIO(raw))
        img = _apply_exif_orientation(img)
        img = img.convert("RGB")
    except Exception as e:
        raise ValueError(f"cannot decode image: {e}") from e

    arr_rgb = np.asarray(img, dtype=np.uint8)
    return cv2.cvtColor(arr_rgb, cv2.COLOR_RGB2BGR)


def _apply_exif_orientation(img: Image.Image) -> Image.Image:
    try:
        exif = img.getexif()
        if not exif:
            return img
        orientation_tag = next(
            (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
        )
        if orientation_tag is None:
            return img
        orientation = exif.get(orientation_tag)
        if orientation == 3:
            return img.rotate(180, expand=True)
        if orientation == 6:
            return img.rotate(270, expand=True)
        if orientation == 8:
            return img.rotate(90, expand=True)
    except Exception:
        return img
    return img
