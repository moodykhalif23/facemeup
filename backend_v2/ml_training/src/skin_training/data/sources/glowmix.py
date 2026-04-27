"""Load the GlowMix facial skincare dataset from a local Kaggle extract.

Supports two common layouts:
1. CSV/manifest-driven datasets with image-path and label columns.
2. Directory trees where folder names encode the cosmetic concern.
"""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

from ..labels import cosmetic_labels_to_vector
from ..scin import SCINSample

log = logging.getLogger(__name__)

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_IMAGE_COLS = ("image", "image_path", "path", "filepath", "filename", "file", "img")
_LABEL_COLS = (
    "label", "labels", "class", "classes", "condition", "conditions",
    "concern", "concerns", "category", "categories", "issue", "issues",
)
_LABEL_SPLIT_RE = re.compile(r"[|;,]+")


def load_glowmix(root: str | Path, max_samples: int | None = None) -> list[SCINSample]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(root)

    manifest_samples = _load_from_manifests(root, max_samples)
    if manifest_samples:
        log.info("GlowMix: loaded %d samples from manifest files", len(manifest_samples))
        return manifest_samples

    folder_samples = _load_from_folders(root, max_samples)
    log.info("GlowMix: loaded %d samples from folder labels", len(folder_samples))
    return folder_samples


def _load_from_manifests(root: Path, max_samples: int | None) -> list[SCINSample]:
    samples: list[SCINSample] = []
    seen_paths: set[Path] = set()

    for manifest in sorted(root.rglob("*.csv")):
        with manifest.open(encoding="utf8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            image_col = _pick(fieldnames, _IMAGE_COLS)
            label_cols = [c for c in fieldnames if c.lower() in _LABEL_COLS]
            if image_col is None or not label_cols:
                continue

            for row in reader:
                image_path = _resolve_image_path(root, manifest.parent, row.get(image_col, ""))
                if image_path is None or image_path in seen_paths:
                    continue
                raw_labels = _extract_row_labels(row, label_cols)
                vec = cosmetic_labels_to_vector(raw_labels)
                if sum(vec) == 0:
                    continue
                seen_paths.add(image_path)
                samples.append(_make_sample(len(samples), image_path, raw_labels, vec))
                if max_samples and len(samples) >= max_samples:
                    return samples
    return samples


def _load_from_folders(root: Path, max_samples: int | None) -> list[SCINSample]:
    samples: list[SCINSample] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _IMAGE_EXTS:
            continue
        label_parts = [part.replace("_", " ").replace("-", " ") for part in path.relative_to(root).parts[:-1]]
        raw_labels = [part for part in label_parts if sum(cosmetic_labels_to_vector([part])) > 0]
        vec = cosmetic_labels_to_vector(raw_labels)
        if sum(vec) == 0:
            continue
        samples.append(_make_sample(len(samples), path, raw_labels, vec))
        if max_samples and len(samples) >= max_samples:
            break
    return samples


def _pick(fieldnames: list[str], options: tuple[str, ...]) -> str | None:
    lower = {name.lower(): name for name in fieldnames}
    for option in options:
        if option in lower:
            return lower[option]
    return None


def _resolve_image_path(root: Path, base_dir: Path, raw: str) -> Path | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    candidate = Path(raw)
    paths_to_try = [
        candidate,
        base_dir / candidate,
        root / candidate,
    ]
    for path in paths_to_try:
        if path.is_file():
            return path.resolve()
    return None


def _extract_row_labels(row: dict[str, str], label_cols: list[str]) -> list[str]:
    labels: list[str] = []
    for col in label_cols:
        raw = (row.get(col) or "").strip()
        if not raw:
            continue
        parts = [part.strip() for part in _LABEL_SPLIT_RE.split(raw) if part.strip()]
        labels.extend(parts or [raw])
    return labels


def _make_sample(index: int, image_path: Path, raw_labels: list[str], vec: list[int]) -> SCINSample:
    case_id = f"glowmix_{index:06d}_{image_path.stem}"
    return SCINSample(
        case_id=case_id,
        image_path=image_path,
        label_vector=tuple(vec),
        raw_conditions=tuple(raw_labels),
        fitzpatrick=None,
        body_part="face",
    )
