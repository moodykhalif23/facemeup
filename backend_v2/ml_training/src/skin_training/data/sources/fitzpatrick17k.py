"""Load the Fitzpatrick17k dataset.

Fitzpatrick17k (Groh et al. 2021):
  - 16,577 clinical dermatology images
  - 114 skin conditions, Fitzpatrick skin-type I–VI labels
  - All images are photographs of skin ON ANY BODY PART

Two loading strategies (tried in order):
  A. HuggingFace ``load_dataset``  (fast, no scraping)
  B. CSV + URL download fallback  (slow but always works)

Strategy A (HuggingFace):
    The canonical repo at the time of writing is ``mattgroh/fitzpatrick17k``.
    If that 404s, search HuggingFace for "fitzpatrick17k" and update HF_REPO below.

Strategy B (CSV):
    Downloads the raw CSV from GitHub then fetches each image URL.
    Slow (~2 h for 16k images on Colab), but does not require HF access.

Condition labels map to our 6-class taxonomy through the same SCIN_MACRO_MAP
table — the condition name strings are similar enough to work directly.
"""

from __future__ import annotations

import base64
import csv
import logging
import time
import urllib.request
from io import BytesIO
from pathlib import Path

from ..labels import FACE_BODY_PARTS, fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample, _is_face_region

log = logging.getLogger(__name__)

# Verify this repo name on huggingface.co if you hit 404 or GatedRepo errors.
HF_REPO = "mattgroh/fitzpatrick17k"

CSV_URL = (
    "https://raw.githubusercontent.com/mattgroh/fitzpatrick17k"
    "/main/fitzpatrick17k.csv"
)

# Fitzpatrick17k body-part values (best-effort mapping; the dataset does not
# always carry a body-part field — if absent we include all images and rely on
# the face detector to filter at precompute time).
FP17K_FACE_VALUES: frozenset[str] = frozenset({
    "face", "head", "neck", "scalp", "cheek", "forehead",
    "nose", "chin", "perioral", "periorbital",
})


def load_fitzpatrick17k(
    strategy: str = "hf",
    hf_repo: str = HF_REPO,
    hf_split: str = "train",
    cache_dir: str | None = None,
    token: str | None = None,
    body_parts: frozenset[str] | None = FACE_BODY_PARTS,
    csv_url: str = CSV_URL,
    download_dir: Path | None = None,
    max_images: int | None = None,
) -> list[SCINSample]:
    """Return Fitzpatrick17k as a list of SCINSample (image_bytes populated).

    Args:
        strategy: ``"hf"`` tries HuggingFace first, then falls back to CSV.
                  ``"csv"`` goes straight to CSV+download (slower).
        body_parts: Face-region filter. ``None`` = accept all regions.
        max_images: Cap total samples (useful for quick smoke tests).
    """
    if strategy == "hf":
        try:
            return _load_hf(hf_repo, hf_split, cache_dir, token,
                            body_parts, max_images)
        except Exception as e:
            log.warning("HuggingFace load failed (%s) — falling back to CSV", e)

    return _load_csv(csv_url, download_dir, body_parts, max_images)


# ── Strategy A — HuggingFace ─────────────────────────────────────────────────

def _load_hf(
    repo: str,
    split: str,
    cache_dir: str | None,
    token: str | None,
    body_parts: frozenset[str] | None,
    max_images: int | None,
) -> list[SCINSample]:
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets") from e

    log.info("loading %s/%s from HuggingFace …", repo, split)
    ds = load_dataset(repo, split=split, cache_dir=cache_dir, token=token)
    log.info("Fitzpatrick17k HF: %d rows, features: %s", len(ds), list(ds.features))

    cols = set(ds.features.keys())
    img_col   = _pick(cols, ("image", "img", "pixel_values"))
    url_col   = _pick(cols, ("url",))
    label_col = _pick(cols, ("label", "condition", "nine_partition_label",
                             "three_partition_label", "low_fitzpatrick_scale"))
    fp_col    = _pick(cols, ("fitzpatrick", "fitzpatrick_scale", "fst",
                             "high_fitzpatrick_scale", "low_fitzpatrick_scale"))
    body_col  = _pick(cols, ("body_part", "anatom_site", "location"))

    samples: list[SCINSample] = []
    for i, row in enumerate(ds):
        if max_images and len(samples) >= max_images:
            break

        raw_body = str(row[body_col]).lower().strip() if body_col else ""
        if body_parts and body_col and not _is_face_region(raw_body, body_parts):
            continue

        img_bytes = _row_to_bytes(row, img_col, url_col)
        if img_bytes is None:
            continue

        raw_label = _extract_label(row, label_col)
        samples.append(SCINSample(
            case_id=f"fp17k_{i}",
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(scin_labels_to_vector([raw_label] if raw_label else [])),
            raw_conditions=(raw_label,) if raw_label else (),
            fitzpatrick=fitzpatrick_from_str(row.get(fp_col) if fp_col else None),
            body_part=raw_body or None,
        ))

    log.info("Fitzpatrick17k HF: %d face-region samples", len(samples))
    return samples


# ── Strategy B — CSV + download ───────────────────────────────────────────────

def _load_csv(
    csv_url: str,
    download_dir: Path | None,
    body_parts: frozenset[str] | None,
    max_images: int | None,
) -> list[SCINSample]:
    """Download CSV, then fetch each image URL. Very slow; use only if HF is unavailable."""
    if download_dir is None:
        download_dir = Path("/content/fp17k_images")
    download_dir.mkdir(parents=True, exist_ok=True)

    log.info("downloading Fitzpatrick17k CSV from %s", csv_url)
    csv_data = urllib.request.urlopen(csv_url, timeout=30).read().decode("utf8")
    rows = list(csv.DictReader(csv_data.splitlines()))
    log.info("CSV: %d rows", len(rows))

    samples: list[SCINSample] = []
    failed = 0
    for i, row in enumerate(rows):
        if max_images and len(samples) >= max_images:
            break

        label = row.get("label") or row.get("three_partition_label") or ""
        fp_raw = row.get("fitzpatrick") or row.get("fitzpatrick_scale")
        url = row.get("url", "").strip()
        case_id = f"fp17k_csv_{i}"

        if not url:
            continue

        # No body_part column in the raw CSV — rely on face detector at precompute.
        img_path = download_dir / f"{i}.jpg"
        img_bytes = _fetch_url(url, img_path)
        if img_bytes is None:
            failed += 1
            if failed % 100 == 0:
                log.warning("Fitzpatrick17k CSV: %d download failures so far", failed)
            continue

        samples.append(SCINSample(
            case_id=case_id,
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(scin_labels_to_vector([label] if label else [])),
            raw_conditions=(label,) if label else (),
            fitzpatrick=fitzpatrick_from_str(fp_raw),
            body_part=None,
        ))

    log.info("Fitzpatrick17k CSV: %d samples loaded, %d download failures", len(samples), failed)
    return samples


# ── helpers ───────────────────────────────────────────────────────────────────

def _pick(cols: set[str], options: tuple[str, ...]) -> str | None:
    for o in options:
        if o in cols:
            return o
    return None


def _row_to_bytes(row: dict, img_col: str | None, url_col: str | None) -> bytes | None:
    if img_col:
        raw = row[img_col]
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, dict) and raw.get("bytes"):
            return raw["bytes"]
        if hasattr(raw, "save"):
            buf = BytesIO()
            raw.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
    if url_col:
        return _fetch_url(row[url_col])
    return None


def _fetch_url(url: str, cache_path: Path | None = None) -> bytes | None:
    if cache_path and cache_path.is_file():
        return cache_path.read_bytes()
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read()
        if cache_path:
            cache_path.write_bytes(data)
        return data
    except Exception as e:
        log.debug("fetch failed %s: %s", url, e)
        return None


def _extract_label(row: dict, col: str | None) -> str:
    if col is None:
        return ""
    val = row.get(col)
    if isinstance(val, list):
        return val[0] if val else ""
    return str(val) if val else ""
