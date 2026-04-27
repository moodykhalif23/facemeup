"""Load Fitzpatrick17k from HuggingFace (streaming) or CSV fallback.

HuggingFace repo: mattgroh/fitzpatrick17k
  If that 404s, search HuggingFace for "fitzpatrick17k" and update HF_REPO.

Same streaming approach as SCIN — no large download needed.
"""

from __future__ import annotations

import csv
import logging
import os
import urllib.request
from io import BytesIO
from pathlib import Path

from ..labels import FACE_BODY_PARTS, fitzpatrick_from_str, scin_labels_to_vector
from ..scin import SCINSample, _is_face_region

log = logging.getLogger(__name__)

HF_REPO  = "mattgroh/fitzpatrick17k"
CSV_URL  = (
    "https://raw.githubusercontent.com/mattgroh/fitzpatrick17k"
    "/main/fitzpatrick17k.csv"
)


def load_fitzpatrick17k(
    strategy: str = "hf",
    hf_repo: str = HF_REPO,
    hf_split: str = "train",
    cache_dir: str | None = None,
    token: str | None = None,
    body_parts: frozenset[str] | None = FACE_BODY_PARTS,
    csv_url: str = CSV_URL,
    download_dir: Path | None = None,
    max_samples: int | None = None,
) -> list[SCINSample]:
    """Return Fitzpatrick17k as list[SCINSample] (streaming, no full download).

    Args:
        strategy:    ``"hf"`` tries HuggingFace first, falls back to CSV.
                     ``"csv"`` goes straight to CSV+URL download (very slow).
        max_samples: Cap total samples (useful for smoke tests).
    """
    if strategy == "hf":
        try:
            return _load_hf(hf_repo, hf_split, cache_dir, token,
                            body_parts, max_samples)
        except Exception as e:
            log.warning("Fitzpatrick17k HF failed (%s) — falling back to CSV", e)

    return _load_csv(csv_url, download_dir, body_parts, max_samples)


# ── HuggingFace (streaming) ───────────────────────────────────────────────────

def _load_hf(
    repo: str, split: str, cache_dir: str | None,
    token: str | None, body_parts, max_samples,
) -> list[SCINSample]:
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError("pip install datasets") from e

    hf_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")

    log.info("streaming %s/%s…", repo, split)
    ds = load_dataset(repo, split=split, streaming=True,
                      cache_dir=cache_dir, token=hf_token)

    features = ds.features or {}
    cols  = set(features.keys())
    img_col   = _pick(cols, ("image", "img", "pixel_values"))
    url_col   = _pick(cols, ("url",))
    label_col = _pick(cols, ("label", "condition", "nine_partition_label",
                             "three_partition_label", "low_fitzpatrick_scale"))
    fp_col    = _pick(cols, ("fitzpatrick", "fitzpatrick_scale", "fst",
                             "high_fitzpatrick_scale", "low_fitzpatrick_scale"))
    body_col  = _pick(cols, ("body_part", "anatom_site", "location"))

    log.info("fp17k column map → img=%s url=%s label=%s fp=%s body=%s",
             img_col, url_col, label_col, fp_col, body_col)

    samples: list[SCINSample] = []
    for i, row in enumerate(ds):
        if max_samples and len(samples) >= max_samples:
            break
        if i % 500 == 0:
            log.info("fp17k: row %d, collected %d", i, len(samples))

        raw_body = str(row.get(body_col, "")).lower().strip() if body_col else ""
        if body_parts and body_col and not _is_face_region(raw_body, body_parts):
            continue

        img_bytes = _row_to_bytes(row, img_col, url_col)
        if img_bytes is None:
            continue

        raw_label = str(row.get(label_col, "") or "") if label_col else ""
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


# ── CSV fallback ─────────────────────────────────────────────────────────────

def _load_csv(csv_url, download_dir, body_parts, max_samples) -> list[SCINSample]:
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
        if max_samples and len(samples) >= max_samples:
            break
        url   = row.get("url", "").strip()
        label = row.get("label") or row.get("three_partition_label") or ""
        fp_raw = row.get("fitzpatrick") or row.get("fitzpatrick_scale")
        if not url:
            continue
        img_path  = download_dir / f"{i}.jpg"
        img_bytes = _fetch_url(url, img_path)
        if img_bytes is None:
            failed += 1
            continue
        samples.append(SCINSample(
            case_id=f"fp17k_csv_{i}",
            image_path=None,
            image_bytes=img_bytes,
            label_vector=tuple(scin_labels_to_vector([label] if label else [])),
            raw_conditions=(label,) if label else (),
            fitzpatrick=fitzpatrick_from_str(fp_raw),
            body_part=None,
        ))
    log.info("Fitzpatrick17k CSV: %d samples, %d failures", len(samples), failed)
    return samples


# ── helpers ───────────────────────────────────────────────────────────────────

def _pick(cols: set[str], options: tuple[str, ...]) -> str | None:
    for o in options:
        if o in cols:
            return o
    return None


def _row_to_bytes(row, img_col, url_col) -> bytes | None:
    if img_col and (raw := row.get(img_col)) is not None:
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, dict) and raw.get("bytes"):
            return raw["bytes"]
        if hasattr(raw, "save"):
            buf = BytesIO()
            raw.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
    if url_col and (url := row.get(url_col)):
        return _fetch_url(str(url))
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
