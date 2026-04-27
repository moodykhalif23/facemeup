"""SCIN dataset manifest parser.

SCIN covers skin conditions across ALL body parts — face, scalp, neck, arms,
torso, legs, hands, etc. For a face-based skincare app we must filter to
face-region images before running the face-detection pipeline, otherwise the
vast majority of images won't contain a detectable face and will be skipped.

Key filter: `body_parts` param — keeps only rows whose body-location column
contains one of the accepted terms. Default is FACE_BODY_PARTS.
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .labels import Fitzpatrick, fitzpatrick_from_str, scin_labels_to_vector

log = logging.getLogger(__name__)

# SCIN body-location values (column may be named "body_part", "anatom_site",
# "location", "site", or "region" depending on the release). We keep only
# images where the value contains one of these substrings (case-insensitive).
FACE_BODY_PARTS: frozenset[str] = frozenset({
    "face",
    "neck",
    "scalp",
    "cheek",
    "forehead",
    "chin",
    "nose",
    "perioral",
    "periorbital",
    "head",
})

# The column names SCIN uses for body location across releases.
_BODY_PART_COLS = ("body_part", "anatom_site", "location", "site", "region", "body_location")


@dataclass(frozen=True)
class SCINSample:
    case_id: str
    image_path: Path | None            # None when loaded from HuggingFace
    label_vector: tuple[int, ...]      # 6-dim macro condition vector (0/1)
    raw_conditions: tuple[str, ...]    # original SCIN labels, kept for debugging
    fitzpatrick: Fitzpatrick | None
    body_part: str | None              # raw value from the CSV, useful for debugging
    image_bytes: bytes | None = None   # Non-None when loaded from HuggingFace

    def get_bytes(self) -> bytes:
        """Return raw image bytes regardless of whether we came from a file or HF."""
        if self.image_bytes is not None:
            return self.image_bytes
        if self.image_path is not None:
            return self.image_path.read_bytes()
        raise ValueError(f"sample {self.case_id!r} has neither image_path nor image_bytes")


def parse_scin_manifest(
    root: Path,
    cases_csv: str = "scin_cases.csv",
    labels_csv: str = "scin_labels.csv",
    image_dir: str = "images",
    min_confidence: float = 0.0,
    body_parts: frozenset[str] | None = FACE_BODY_PARTS,
) -> list[SCINSample]:
    """Read SCIN CSVs into SCINSample rows, filtered to face-region images.

    Args:
        root: directory containing the two CSVs and the image folder.
        min_confidence: drop dermatologist labels below this confidence (0..1).
        body_parts: keep only samples whose body-location column contains any
            of these strings (case-insensitive substring match). Pass None to
            disable the filter and accept all body parts (not recommended —
            produces a very high face-detection skip rate).
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

    # 2. Iterate cases, build SCINSamples.
    samples: list[SCINSample] = []
    total = 0
    skipped_body_part = 0
    skipped_image = 0

    with cases_path.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        body_col = _find_body_col(reader.fieldnames or [])
        if body_parts and body_col is None:
            log.warning(
                "body-part filter requested but no matching column found in %s "
                "(checked: %s) — will rely on face-detector to skip non-face images",
                cases_path.name, ", ".join(_BODY_PART_COLS),
            )

        for row in reader:
            total += 1
            case_id = row.get("case_id") or row.get("case") or row.get("id")
            if not case_id:
                continue

            raw_body_part = row.get(body_col, "") if body_col else ""
            if body_parts and body_col and not _is_face_region(raw_body_part, body_parts):
                skipped_body_part += 1
                continue

            image_path = _resolve_image(row, img_root, case_id)
            if image_path is None or not image_path.is_file():
                skipped_image += 1
                continue

            conditions = by_case.get(case_id, [])
            vec = scin_labels_to_vector(conditions)
            fp = fitzpatrick_from_str(
                row.get("fitzpatrick") or row.get("skin_type") or row.get("fst")
            )
            samples.append(
                SCINSample(
                    case_id=case_id,
                    image_path=image_path,
                    label_vector=tuple(vec),
                    raw_conditions=tuple(conditions),
                    fitzpatrick=fp,
                    body_part=raw_body_part or None,
                )
            )

    log.info(
        "SCIN parse: %d total rows → %d face-region samples kept "
        "(%d skipped by body-part, %d skipped missing image)",
        total, len(samples), skipped_body_part, skipped_image,
    )
    return samples


def body_part_distribution(samples: list[SCINSample]) -> dict[str, int]:
    """Count how many samples fall into each unique body-part value."""
    dist: dict[str, int] = {}
    for s in samples:
        key = s.body_part or "unknown"
        dist[key] = dist.get(key, 0) + 1
    return dict(sorted(dist.items(), key=lambda kv: -kv[1]))


def _find_body_col(fieldnames: list[str]) -> str | None:
    lower = {c.lower(): c for c in fieldnames}
    for candidate in _BODY_PART_COLS:
        if candidate in lower:
            return lower[candidate]
    return None


def _is_face_region(raw: str, accepted: frozenset[str]) -> bool:
    """True if raw body-part value contains any accepted term."""
    if not raw:
        return False
    lower = raw.lower()
    return any(term in lower for term in accepted)


def _resolve_image(row: dict, img_root: Path, case_id: str) -> Path | None:
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
