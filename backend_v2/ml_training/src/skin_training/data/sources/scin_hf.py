"""Load the Google SCIN dataset directly from HuggingFace.

Usage:
    from skin_training.data.sources.scin_hf import load_scin_hf
    samples = load_scin_hf()

HuggingFace repo: google/scin
Requires:  pip install datasets

The caller must already be authenticated:
    huggingface-cli login              # interactive
    # OR set env var HUGGINGFACE_TOKEN
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

from ..labels import FACE_BODY_PARTS, fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample, _is_face_region

log = logging.getLogger(__name__)

# HuggingFace SCIN field names. SCIN has evolved through dataset card versions;
# we probe for each alternative at load time.
_ID_FIELDS        = ("case_id", "id", "image_id", "idx")
_LABEL_FIELDS     = ("labels", "label", "condition", "conditions", "diagnoses",
                     "dermatologist_diagnoses", "diagnosis")
_FP_FIELDS        = ("fitzpatrick_scale", "fitzpatrick", "skin_type", "fst",
                     "fitzpatrick_skin_type")
_BODY_FIELDS      = ("body_part", "body_location", "anatom_site", "location",
                     "site", "region", "anatomy")
_IMAGE_FIELDS     = ("image", "img", "pixel_values")
_CONFIDENCE_FIELD = "confidence"


def load_scin_hf(
    hf_repo: str = "google/scin",
    split: str = "train",
    body_parts: frozenset[str] | None = FACE_BODY_PARTS,
    cache_dir: str | None = None,
    token: str | None = None,
) -> list[SCINSample]:
    """Download and filter SCIN from HuggingFace.

    Args:
        hf_repo:    HuggingFace dataset repository (default ``google/scin``).
        split:      Dataset split to load.
        body_parts: Face-region filter. Pass ``None`` to accept all body parts.
        cache_dir:  Optional HF cache directory (useful for Colab + Drive persistence).
        token:      HuggingFace access token. Reads ``HUGGINGFACE_TOKEN`` env var if None.
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets  (huggingface datasets library)") from e

    log.info("loading %s/%s from HuggingFace …", hf_repo, split)
    ds = load_dataset(hf_repo, split=split, cache_dir=cache_dir, token=token)
    log.info("HF dataset loaded: %d rows, features: %s", len(ds), list(ds.features.keys()))

    cols = set(ds.features.keys())
    id_col    = _pick(cols, _ID_FIELDS)
    label_col = _pick(cols, _LABEL_FIELDS)
    fp_col    = _pick(cols, _FP_FIELDS)
    body_col  = _pick(cols, _BODY_FIELDS)
    img_col   = _pick(cols, _IMAGE_FIELDS)

    log.info(
        "column mapping → id=%s labels=%s fitzpatrick=%s body=%s image=%s",
        id_col, label_col, fp_col, body_col, img_col,
    )
    if img_col is None:
        raise ValueError(
            f"No image column found in {hf_repo}. Available: {cols}. "
            f"Expected one of: {_IMAGE_FIELDS}"
        )

    samples: list[SCINSample] = []
    skipped_body = 0
    skipped_img  = 0

    for i, row in enumerate(ds):
        case_id = str(row.get(id_col, i) if id_col else i)

        raw_body = str(row[body_col]).lower().strip() if body_col else ""
        if body_parts and body_col and not _is_face_region(raw_body, body_parts):
            skipped_body += 1
            continue

        raw_img = row[img_col]
        img_bytes = _to_bytes(raw_img)
        if img_bytes is None:
            skipped_img += 1
            continue

        raw_labels: list[str] = _extract_labels(row, label_col)
        label_vec = scin_labels_to_vector(raw_labels)
        fp = fitzpatrick_from_str(row.get(fp_col) if fp_col else None)

        samples.append(SCINSample(
            case_id=f"scin_{case_id}",
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(label_vec),
            raw_conditions=tuple(raw_labels),
            fitzpatrick=fp,
            body_part=raw_body or None,
        ))

    log.info(
        "SCIN-HF: %d kept, %d skipped by body-part, %d skipped bad image",
        len(samples), skipped_body, skipped_img,
    )
    return samples


# ── helpers ─────────────────────────────────────────────────────────────────

def _pick(cols: set[str], options: tuple[str, ...]) -> str | None:
    for o in options:
        if o in cols:
            return o
    return None


def _to_bytes(raw) -> bytes | None:
    """Convert whatever HuggingFace gives us for an image into raw JPEG bytes."""
    from PIL import Image as PilImage

    if isinstance(raw, bytes):
        return raw
    if isinstance(raw, dict):
        # Datasets sometimes wraps as {"bytes": b"...", "path": ...}
        if "bytes" in raw and raw["bytes"]:
            return raw["bytes"]
        if "path" in raw and raw["path"]:
            p = Path(raw["path"])
            return p.read_bytes() if p.is_file() else None
    if hasattr(raw, "save"):  # PIL.Image.Image
        buf = BytesIO()
        raw.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    return None


def _extract_labels(row: dict, label_col: str | None) -> list[str]:
    if label_col is None:
        return []
    val = row.get(label_col)
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(v) for v in val if v]
    return [str(val)]
