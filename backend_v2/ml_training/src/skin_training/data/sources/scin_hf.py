"""Load the Google SCIN dataset from HuggingFace using streaming.

streaming=True means NO full download — images are processed one at a time
directly from the parquet files. Free Colab (15 GB disk) would run out of space
downloading all 26 parquet shards (~13 GB). With streaming we only need disk
space for the processed .npy files (~400 MB for ~2k face images).

HuggingFace repo: google/scin
Requires: pip install datasets huggingface-hub

Authentication:
    Set the HF_TOKEN environment variable before importing:
        import os; os.environ["HF_TOKEN"] = "hf_YOUR_TOKEN"
    OR call huggingface_hub.login() in an environment that supports the vault.
"""

from __future__ import annotations

import logging
import os
from io import BytesIO

from ..labels import FACE_BODY_PARTS, fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample, _is_face_region

log = logging.getLogger(__name__)

_ID_FIELDS    = ("case_id", "id", "image_id", "idx")
_LABEL_FIELDS = ("labels", "label", "condition", "conditions", "diagnoses",
                 "dermatologist_diagnoses", "diagnosis")
_FP_FIELDS    = ("fitzpatrick_scale", "fitzpatrick", "skin_type", "fst",
                 "fitzpatrick_skin_type")
_BODY_FIELDS  = ("body_part", "body_location", "anatom_site", "location",
                 "site", "region", "anatomy")
_IMAGE_FIELDS = ("image", "img", "pixel_values")


def load_scin_hf(
    hf_repo: str = "google/scin",
    split: str = "train",
    body_parts: frozenset[str] | None = FACE_BODY_PARTS,
    cache_dir: str | None = None,
    token: str | None = None,
    max_samples: int | None = None,
) -> list[SCINSample]:
    """Stream SCIN from HuggingFace — no full dataset download required.

    Args:
        max_samples: Stop after collecting this many face-region samples.
                     Useful for quick smoke tests (e.g. max_samples=200).
    """
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets huggingface-hub") from e

    hf_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token:
        log.warning(
            "No HuggingFace token set. Set os.environ['HF_TOKEN'] = 'hf_...' "
            "before calling this function. Downloads may be rate-limited."
        )

    log.info("streaming google/scin/%s (no full download)…", split)
    ds = load_dataset(
        hf_repo,
        split=split,
        streaming=True,       # <-- key: no 13 GB disk hit
        cache_dir=cache_dir,
        token=hf_token,
    )

    # With streaming datasets, features are available immediately (no data downloaded).
    features = ds.features or {}
    cols = set(features.keys())
    id_col    = _pick(cols, _ID_FIELDS)
    label_col = _pick(cols, _LABEL_FIELDS)
    fp_col    = _pick(cols, _FP_FIELDS)
    body_col  = _pick(cols, _BODY_FIELDS)
    img_col   = _pick(cols, _IMAGE_FIELDS)

    log.info(
        "column map → id=%s label=%s fitzpatrick=%s body=%s image=%s",
        id_col, label_col, fp_col, body_col, img_col,
    )
    if img_col is None:
        raise ValueError(
            f"No image column in {hf_repo}. Available: {cols}. "
            f"Expected one of: {_IMAGE_FIELDS}"
        )

    samples: list[SCINSample] = []
    skipped_body = 0
    skipped_img  = 0
    examined     = 0

    for i, row in enumerate(ds):
        examined += 1
        if examined % 500 == 0:
            log.info("scin_hf: examined %d rows, collected %d samples", examined, len(samples))

        if max_samples and len(samples) >= max_samples:
            log.info("reached max_samples=%d, stopping", max_samples)
            break

        case_id  = str(row.get(id_col, i) if id_col else i)
        raw_body = str(row[body_col]).lower().strip() if body_col else ""

        if body_parts and body_col and not _is_face_region(raw_body, body_parts):
            skipped_body += 1
            continue

        img_bytes = _to_bytes(row.get(img_col))
        if img_bytes is None:
            skipped_img += 1
            continue

        raw_labels = _extract_labels(row, label_col)
        samples.append(SCINSample(
            case_id=f"scin_{case_id}",
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(scin_labels_to_vector(raw_labels)),
            raw_conditions=tuple(raw_labels),
            fitzpatrick=fitzpatrick_from_str(row.get(fp_col) if fp_col else None),
            body_part=raw_body or None,
        ))

    log.info(
        "SCIN-HF done: examined=%d kept=%d skipped_body=%d skipped_img=%d",
        examined, len(samples), skipped_body, skipped_img,
    )
    return samples


# ── helpers ──────────────────────────────────────────────────────────────────

def _pick(cols: set[str], options: tuple[str, ...]) -> str | None:
    for o in options:
        if o in cols:
            return o
    return None


def _to_bytes(raw) -> bytes | None:
    if raw is None:
        return None
    if isinstance(raw, bytes):
        return raw
    if isinstance(raw, dict):
        if raw.get("bytes"):
            return raw["bytes"]
        if raw.get("path"):
            import pathlib
            p = pathlib.Path(raw["path"])
            return p.read_bytes() if p.is_file() else None
    if hasattr(raw, "save"):          # PIL.Image.Image
        buf = BytesIO()
        raw.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    return None


def _extract_labels(row: dict, col: str | None) -> list[str]:
    if col is None:
        return []
    val = row.get(col)
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(v) for v in val if v]
    return [str(val)]
