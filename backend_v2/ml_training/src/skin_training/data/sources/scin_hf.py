"""Load Google SCIN from HuggingFace using streaming.

SCIN's actual HuggingFace schema (2024):
  - Images:     NOT embedded as bytes — stored as paths (image_1_path, image_2_path, image_3_path)
                Fetched per-row via HF HTTP API.
  - Body parts: multi-hot boolean columns: body_parts_head_or_neck, body_parts_arm, ...
  - Diagnosis:  dermatologist_skin_condition_on_label_name  (consensus of 3 dermatologists)
                weighted_skin_condition_label                (alternative)
  - Fitzpatrick: fitzpatrick_skin_type
  - NOTE: condition_symptoms_* columns are patient-reported symptoms, NOT diagnoses.

streaming=True: parquet metadata streams on demand, no 13 GB download.
Images are fetched individually only for face-region rows (~20-30% of total).
"""

from __future__ import annotations

import logging
import os
import urllib.request

from ..labels import fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample

log = logging.getLogger(__name__)

FACE_MULTIHOT_COLS: frozenset[str] = frozenset({
    "body_parts_head_or_neck",
    "body_parts_face",
    "body_parts_scalp",
    "body_parts_neck",
})

_IMAGE_PATH_COLS = ("image_1_path", "image_path", "image_2_path", "image_3_path")

_DIAGNOSIS_COLS = (
    "dermatologist_skin_condition_on_label_name",
    "weighted_skin_condition_label",
    "labels", "label",
)

_FP_FIELDS = (
    "fitzpatrick_skin_type",
    "dermatologist_fitzpatrick_skin_type_label_1",
    "fitzpatrick_scale", "fitzpatrick", "fst",
    "monk_skin_tone_label_us",
)


def load_scin_hf(
    hf_repo: str = "google/scin",
    split: str = "train",
    body_parts=None,
    cache_dir: str | None = None,
    token: str | None = None,
    max_samples: int | None = None,
) -> list[SCINSample]:
    """Stream SCIN metadata, fetch face images on demand via HF HTTP."""
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets huggingface-hub") from e

    hf_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token:
        log.warning("No HF_TOKEN — image downloads may fail on gated dataset")

    log.info("streaming %s/%s…", hf_repo, split)
    ds = load_dataset(hf_repo, split=split, streaming=True,
                      cache_dir=cache_dir, token=hf_token)

    cols = set((ds.features or {}).keys())
    id_col       = _pick(cols, ("case_id", "id", "image_id"))
    img_path_col = _pick(cols, _IMAGE_PATH_COLS)
    label_col    = _pick(cols, _DIAGNOSIS_COLS)
    fp_col       = _pick(cols, _FP_FIELDS)
    face_bp_cols = sorted(c for c in cols if c in FACE_MULTIHOT_COLS)
    all_bp_cols  = sorted(c for c in cols if c.startswith("body_parts_"))

    log.info(
        "schema: id=%s  img_path=%s  label=%s  fitzpatrick=%s  face_bp=%s",
        id_col, img_path_col, label_col, fp_col, face_bp_cols,
    )
    if img_path_col is None:
        raise ValueError(
            f"No image path column found in {hf_repo}. "
            f"Expected one of {_IMAGE_PATH_COLS}. Available: {sorted(cols)}"
        )

    samples: list[SCINSample] = []
    skipped_body = 0
    skipped_img  = 0

    for i, row in enumerate(ds):
        if i % 500 == 0:
            log.info("  row %d | kept %d | body-skip %d | img-skip %d",
                     i, len(samples), skipped_body, skipped_img)
        if max_samples and len(samples) >= max_samples:
            break

        # Body-part filter
        if face_bp_cols:
            if not any(_truthy(row.get(c)) for c in face_bp_cols):
                skipped_body += 1
                continue
        elif all_bp_cols:
            face_like = [c for c in all_bp_cols
                         if any(t in c for t in ("face","head","neck","scalp"))]
            if face_like and not any(_truthy(row.get(c)) for c in face_like):
                skipped_body += 1
                continue

        # Fetch image bytes via HF HTTP
        img_path = row.get(img_path_col)
        if not img_path:
            skipped_img += 1
            continue
        img_bytes = _fetch_hf_image(str(img_path), hf_repo, hf_token)
        if img_bytes is None:
            skipped_img += 1
            continue

        # Diagnosis labels (dermatologist consensus, NOT condition_symptoms_*)
        raw_labels = _extract_diagnosis(row, label_col)

        # Fitzpatrick
        fp_raw = row.get(fp_col) if fp_col else None
        if fp_col and fp_raw and "monk" in fp_col.lower():
            try:
                fp_raw = str(max(1, min(6, round(float(fp_raw) * 0.6))))
            except (TypeError, ValueError):
                fp_raw = None

        case_id = str(row.get(id_col, i) if id_col else i)
        samples.append(SCINSample(
            case_id=f"scin_{case_id}",
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(scin_labels_to_vector(raw_labels)),
            raw_conditions=tuple(raw_labels),
            fitzpatrick=fitzpatrick_from_str(fp_raw),
            body_part="head_or_neck" if face_bp_cols else None,
        ))

    log.info(
        "SCIN-HF: examined=%d  kept=%d  body-skip=%d  img-skip=%d",
        i + 1, len(samples), skipped_body, skipped_img,
    )
    return samples


def _pick(cols: set[str], options) -> str | None:
    for o in options:
        if o in cols:
            return o
    return None


def _truthy(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).lower().strip() in ("true", "1", "yes", "y")


def _fetch_hf_image(path: str, repo_id: str, token: str | None) -> bytes | None:
    """Download one image from a HuggingFace dataset repo (no local caching).

    HF dataset files are served at:
        https://huggingface.co/datasets/{repo}/resolve/main/{path}
    """
    url = f"https://huggingface.co/datasets/{repo_id}/resolve/main/{path.lstrip('/')}"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        log.debug("image fetch failed %s: %s", url, e)
        return None


def _extract_diagnosis(row: dict, label_col: str | None) -> list[str]:
    """Return dermatologist diagnosis strings.

    Deliberately ignores condition_symptoms_* (itching/bleeding/etc.)
    which are patient-reported symptoms, not skin conditions.
    """
    if label_col is None:
        return []
    val = row.get(label_col)
    if val is None:
        return []
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    if isinstance(val, list):
        return [str(v).strip() for v in val if v]
    return []
