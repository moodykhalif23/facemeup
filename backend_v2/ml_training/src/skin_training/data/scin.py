"""SCIN dataset manifest parser.

Expects the layout produced by Google's SCIN download:
    data/raw/
        images/<case_id>_<n>.jpg
        scin_cases.csv             # image-level metadata (case_id, path, ...)
        scin_labels.csv            # dermatologist label rows (case_id, condition, confidence)

We don't bundle the dataset; users download from github.com/google-research-datasets/scin
and point `--manifest` at their local copy. This module just turns the CSVs
into a flat list of `SCINSample`s.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .labels import Fitzpatrick, fitzpatrick_from_str, scin_labels_to_vector


@dataclass(frozen=True)
class SCINSample:
    case_id: str
    image_path: Path
    label_vector: tuple[int, ...]       # 6-dim macro condition vector (0/1)
    raw_conditions: tuple[str, ...]     # original SCIN labels, kept for debugging
    fitzpatrick: Fitzpatrick | None


def parse_scin_manifest(
    root: Path,
    cases_csv: str = "scin_cases.csv",
    labels_csv: str = "scin_labels.csv",
    image_dir: str = "images",
    min_confidence: float = 0.0,
) -> list[SCINSample]:
    """Read SCIN CSVs into SCINSample rows.

    - `root`: directory containing the two CSVs and the image folder.
    - `min_confidence`: drop dermatologist labels below this confidence (0..1).

    CSV column names follow the published SCIN schema. If your copy uses a
    different schema pass through a preprocessing step first.
    """
    root = Path(root)
    cases_path = root / cases_csv
    labels_path = root / labels_csv
    img_root = root / image_dir

    if not cases_path.is_file():
        raise FileNotFoundError(cases_path)
    if not labels_path.is_file():
        raise FileNotFoundError(labels_path)

    # 1. case_id → [condition, ...]
    by_case: dict[str, list[str]] = defaultdict(list)
    with labels_path.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case_id") or row.get("case") or row.get("id")
            condition = row.get("condition") or row.get("label") or row.get("diagnosis")
            conf_raw = row.get("confidence") or row.get("weight") or "1.0"
            if not case_id or not condition:
                continue
            try:
                conf = float(conf_raw)
            except (TypeError, ValueError):
                conf = 1.0
            if conf < min_confidence:
                continue
            by_case[case_id].append(condition.strip())

    # 2. Iterate cases, build SCINSamples
    samples: list[SCINSample] = []
    with cases_path.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case_id") or row.get("case") or row.get("id")
            if not case_id:
                continue
            image_path = _resolve_image(row, img_root, case_id)
            if image_path is None or not image_path.is_file():
                continue
            conditions = by_case.get(case_id, [])
            vec = scin_labels_to_vector(conditions)
            fp = fitzpatrick_from_str(row.get("fitzpatrick") or row.get("skin_type"))
            samples.append(
                SCINSample(
                    case_id=case_id,
                    image_path=image_path,
                    label_vector=tuple(vec),
                    raw_conditions=tuple(conditions),
                    fitzpatrick=fp,
                )
            )
    return samples


def _resolve_image(row: dict, img_root: Path, case_id: str) -> Path | None:
    # If the manifest gives an explicit path, use it; else fall back to <case_id>.jpg
    rel = row.get("image_path") or row.get("filename") or row.get("path")
    if rel:
        candidate = img_root / rel if not Path(rel).is_absolute() else Path(rel)
        if candidate.is_file():
            return candidate
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = img_root / f"{case_id}{ext}"
        if candidate.is_file():
            return candidate
    return None
