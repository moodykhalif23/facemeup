"""Load Google SCIN from HuggingFace using streaming.

SCIN's actual HuggingFace schema (2024 release):
  body parts  -> multi-hot boolean columns: body_parts_head_or_neck, body_parts_arm, ...
  Fitzpatrick -> fitzpatrick_skin_type  (not 'fitzpatrick')
  conditions  -> individual boolean columns (condition_acne, ...) OR a labels list
  No single 'body_part' string column.

streaming=True: images fetch on demand, no 13 GB local download.
"""

from __future__ import annotations

import logging
import os
from io import BytesIO

from ..labels import fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample

log = logging.getLogger(__name__)

# Which body_parts_* columns count as "face/neck/head" region.
FACE_MULTIHOT_COLS: frozenset[str] = frozenset({
    "body_parts_head_or_neck",
    "body_parts_face",
    "body_parts_scalp",
    "body_parts_neck",
})

_BODY_PREFIX = "body_parts_"
_COND_PREFIX = "condition_"

_FP_FIELDS = (
    "fitzpatrick_skin_type", "fitzpatrick_scale", "fitzpatrick",
    "skin_type", "fst",
    "monk_skin_tone_label_us", "monk_skin_tone_label",
)
_LABEL_FIELDS = (
    "labels", "label", "condition", "conditions",
    "diagnoses", "diagnosis",
    "dermatologist_diagnoses", "dermatologist_diagnosis",
    "skin_conditions", "patient_reported_conditions",
)


def load_scin_hf(
    hf_repo: str = "google/scin",
    split: str = "train",
    body_parts=None,          # kept for API compat; filtering via FACE_MULTIHOT_COLS
    cache_dir: str | None = None,
    token: str | None = None,
    max_samples: int | None = None,
) -> list[SCINSample]:
    """Stream SCIN from HuggingFace — no 13 GB download required."""
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets huggingface-hub") from e

    hf_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token:
        log.warning("No HF_TOKEN — rate limits may apply")

    ds = load_dataset(hf_repo, split=split, streaming=True,
                      cache_dir=cache_dir, token=hf_token)
    cols = set((ds.features or {}).keys())

    # ── Detect schema columns ─────────────────────────────────────────────────
    img_col        = _pick(cols, ("image", "img", "pixel_values"))
    id_col         = _pick(cols, ("case_id", "id", "image_id"))
    label_col      = _pick(cols, _LABEL_FIELDS)
    fp_col         = _pick(cols, _FP_FIELDS)
    face_bp_cols   = sorted(c for c in cols if c in FACE_MULTIHOT_COLS)
    all_bp_cols    = sorted(c for c in cols if c.startswith(_BODY_PREFIX))
    cond_bool_cols = sorted(c for c in cols if c.startswith(_COND_PREFIX))

    log.info(
        "SCIN schema detected:\n"
        "  image=%s  id=%s  label=%s  fitzpatrick=%s\n"
        "  face body-part cols: %s\n"
        "  condition bool cols (%d): %s…",
        img_col, id_col, label_col, fp_col,
        face_bp_cols,
        len(cond_bool_cols), cond_bool_cols[:8],
    )
    if img_col is None:
        raise ValueError(f"No image column in {hf_repo}. Cols: {sorted(cols)}")

    # Warn if no body-part filter available (will rely on face detector alone).
    if not face_bp_cols and not all_bp_cols:
        log.warning(
            "No body_parts_* columns found — ALL rows will enter precompute. "
            "Face detector will filter non-face images (slower, higher skip rate)."
        )

    samples: list[SCINSample] = []
    skipped_body = 0
    skipped_img  = 0

    for i, row in enumerate(ds):
        if i % 500 == 0:
            log.info("  row %d | collected %d | body-skipped %d", i, len(samples), skipped_body)
        if max_samples and len(samples) >= max_samples:
            break

        # ── Body-part filter ─────────────────────────────────────────────────
        if face_bp_cols:
            # Keep only rows where at least one face/neck column is True.
            if not any(_truthy(row.get(c)) for c in face_bp_cols):
                skipped_body += 1
                continue
        elif all_bp_cols:
            # Fallback: check any body-part col whose name contains a face term.
            face_like = [c for c in all_bp_cols if _face_in_name(c)]
            if face_like and not any(_truthy(row.get(c)) for c in face_like):
                skipped_body += 1
                continue

        # ── Image bytes ───────────────────────────────────────────────────────
        img_bytes = _to_bytes(row.get(img_col))
        if img_bytes is None:
            skipped_img += 1
            continue

        # ── Labels ───────────────────────────────────────────────────────────
        raw_labels = _extract_labels(row, label_col, cond_bool_cols)

        # ── Fitzpatrick ───────────────────────────────────────────────────────
        fp_raw = row.get(fp_col) if fp_col else None
        if fp_col and fp_raw and "monk" in fp_col.lower():
            # Monk 1-10 scale -> approximate Fitzpatrick 1-6
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


# ── helpers ───────────────────────────────────────────────────────────────────

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


def _face_in_name(col: str) -> bool:
    n = col.lower()
    return any(t in n for t in
               ("face", "head", "neck", "scalp", "cheek", "forehead",
                "perioral", "periorbital", "nose", "chin"))


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
    if hasattr(raw, "save"):
        buf = BytesIO()
        raw.save(buf, format="JPEG", quality=95)
        return buf.getvalue()
    return None


def _extract_labels(row: dict, label_col: str | None,
                    cond_bool_cols: list[str]) -> list[str]:
    if label_col:
        val = row.get(label_col)
        if isinstance(val, str) and val:
            return [val]
        if isinstance(val, list):
            return [str(v) for v in val if v]

    if cond_bool_cols:
        return [
            col[len(_COND_PREFIX):].replace("_", " ")
            for col in cond_bool_cols
            if _truthy(row.get(col))
        ]
    return []
