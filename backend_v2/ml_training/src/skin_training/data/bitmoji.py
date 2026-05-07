"""Bitmoji-device dataset adapter.

The `scrappy/` collector pulls per-record JSON files alongside each face
image. Each JSON carries the device's 15-metric analysis at full granularity
(0–100 score, 1–5 level). This module turns those records into samples shaped
exactly like `SCINSample` so the existing trainer can consume them without
changes — and additionally exposes the raw 0–100 scores so a future
regression head (closer to the device's continuous output) can be trained
without re-parsing.

Why we use this dataset:
    - Real consumer photos taken on the device's camera (close-up, controlled
      light) — the closest analogue to phone selfies we have at scale.
    - Labels are device-derived rather than dermatologist-confirmed, so treat
      with care: the `derived_conditions` flags are calibrated for the
      device's own UV / cross-polarised optics, and visible-light-only models
      cannot match parity on UV-only categories. Filter accordingly.

Public surface mirrors `scin.parse_scin_manifest` so the call site can swap.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .labels import Condition, Fitzpatrick

log = logging.getLogger(__name__)


# Bitmoji raw-condition (the "raw_conditions" list in each *.json) → our 7-dim
# macro taxonomy. Mirrors backend_v2/internal mapping but kept independent so
# the dataset definition is self-contained.
_BITMOJI_TO_MACRO: dict[str, tuple[Condition, ...]] = {
    "blackhead":    (Condition.ACNE, Condition.OILINESS),
    "uv_acne":      (Condition.ACNE,),
    "pimples":      (Condition.ACNE,),
    "pores":        (Condition.ACNE, Condition.OILINESS),
    "spots":        (Condition.DARK_SPOTS,),
    "uv_spots":     (Condition.DARK_SPOTS,),
    "pigmentation": (Condition.DARK_SPOTS,),
    "wrinkles":     (Condition.WRINKLES,),
    "moisture":     (Condition.DRYNESS,),    # flagged when score is low
    "sensitivity":  (Condition.REDNESS,),
    "dark_circles": (Condition.DARK_CIRCLES,),
    "sebum":        (Condition.OILINESS,),    # flagged when score is low
}

# Per-condition continuous score derived from the raw 0–100 device metrics.
# The device's score scale is "higher = healthier" for most metrics, so we
# invert (100 − score) → 0–1 severity. The exceptions below are inverted in
# the opposite direction — we keep them aligned with the macro semantics.
_INVERT_FOR_SEVERITY = True


@dataclass(frozen=True)
class BitmojiSample:
    """SCIN-compatible (the shared trainer code only touches these fields)
    plus a `raw_scores` dict that exposes the device's 15 continuous metrics.
    """
    case_id: str
    image_path: Path | None
    label_vector: tuple[int, ...]            # 7-dim 0/1 macro vector
    raw_conditions: tuple[str, ...]          # original Bitmoji flags
    fitzpatrick: Fitzpatrick | None          # not provided by the device
    body_part: str | None = "face"
    image_bytes: bytes | None = None

    # Bitmoji-specific extras (a future regression head can train on these):
    raw_scores: dict[str, dict] = field(default_factory=dict)
    severity_vector: tuple[float, ...] = field(default_factory=tuple)
    derived_skin_type: str | None = None
    age_estimate: int | None = None
    ita: float | None = None

    def get_bytes(self) -> bytes:
        if self.image_bytes is not None:
            return self.image_bytes
        if self.image_path is not None:
            return self.image_path.read_bytes()
        raise ValueError(f"sample {self.case_id!r} has neither image_path nor image_bytes")


def parse_bitmoji_dataset(
    images_dir: Path,
    *,
    require_image: bool = True,
    min_face_score: float | None = None,
) -> list[BitmojiSample]:
    """Walk `images_dir` for matched (.jpg, .json) pairs and return samples.

    Args:
        images_dir: directory produced by `scrappy/collector.js` — expects
            `<result_id>.jpg` next to `<result_id>.json`.
        require_image: drop records whose image file is missing.
        min_face_score: optionally drop records with a low device-reported
            face_score (0–100) — useful for filtering out partial / occluded
            shots.

    Returns:
        List of BitmojiSample. The trainer's existing pipeline only reads
        the SCIN-shared fields; the extras are available for downstream
        regression training.
    """
    images_dir = Path(images_dir)
    if not images_dir.is_dir():
        raise FileNotFoundError(images_dir)

    metas = sorted(images_dir.glob("*.json"))
    samples: list[BitmojiSample] = []
    skipped_no_image = 0
    skipped_face_score = 0
    skipped_parse = 0

    for meta_path in metas:
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            log.warning("skip %s: %s", meta_path.name, e)
            skipped_parse += 1
            continue

        result_id = data.get("result_id") or meta_path.stem
        image_file = data.get("image_file") or f"{result_id}.jpg"
        image_path = images_dir / image_file

        if require_image and not image_path.is_file():
            # collector saves either .jpg/.jpeg/.png — try them all.
            alt = next((p for p in (
                images_dir / f"{result_id}.jpg",
                images_dir / f"{result_id}.jpeg",
                images_dir / f"{result_id}.png",
            ) if p.is_file()), None)
            if alt is None:
                skipped_no_image += 1
                continue
            image_path = alt

        scores = data.get("scores", {}) or {}
        face_score = scores.get("face_score")
        if (
            min_face_score is not None
            and isinstance(face_score, (int, float))
            and face_score < min_face_score
        ):
            skipped_face_score += 1
            continue

        raw_conditions = tuple(data.get("raw_conditions") or [])
        label_vector = _bitmoji_to_label_vector(raw_conditions)
        severity = _bitmoji_to_severity_vector(scores)

        sample = BitmojiSample(
            case_id=result_id,
            image_path=image_path,
            label_vector=tuple(label_vector),
            raw_conditions=raw_conditions,
            fitzpatrick=None,
            raw_scores=scores,
            severity_vector=severity,
            derived_skin_type=data.get("skin_type"),
            age_estimate=scores.get("age_estimate"),
            ita=(scores.get("skin_tone") or {}).get("ita"),
        )
        samples.append(sample)

    log.info(
        "Bitmoji parse: %d JSON files → %d samples kept "
        "(%d missing image, %d under min_face_score, %d unparseable)",
        len(metas), len(samples), skipped_no_image, skipped_face_score, skipped_parse,
    )
    return samples


def _bitmoji_to_label_vector(raw_conditions: tuple[str, ...]) -> list[int]:
    """Project the device's flag list onto our 7-dim 0/1 macro vector."""
    vec = [0] * len(Condition)
    for raw in raw_conditions:
        macros = _BITMOJI_TO_MACRO.get(raw)
        if macros is None:
            continue
        for c in macros:
            vec[int(c)] = 1
    return vec


def _bitmoji_to_severity_vector(scores: dict) -> tuple[float, ...]:
    """Continuous 7-dim severity in [0, 1] from the device's raw metrics.

    The device uses "score higher = healthier". We invert (100 − score) so
    larger values mean *more severe*. Per-macro aggregation takes the max
    across contributing metrics — matches the inference-time max-pool used
    by the multi-instance classifier.
    """
    contribs: dict[Condition, list[float]] = defaultdict(list)
    for key, macros in _BITMOJI_TO_MACRO.items():
        m = scores.get(key)
        if not isinstance(m, dict):
            continue
        s = m.get("score")
        if not isinstance(s, (int, float)):
            continue
        severity = max(0.0, min(1.0, (100.0 - float(s)) / 100.0)) if _INVERT_FOR_SEVERITY \
            else max(0.0, min(1.0, float(s) / 100.0))
        for macro in macros:
            contribs[macro].append(severity)

    vec = [0.0] * len(Condition)
    for c in Condition:
        vals = contribs.get(c)
        if vals:
            vec[int(c)] = round(max(vals), 4)
    return tuple(vec)
