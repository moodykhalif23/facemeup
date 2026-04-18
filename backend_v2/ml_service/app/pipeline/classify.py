"""Placeholder classifier for Phase 1.

Returns uniform sigmoid probabilities with low confidence so callers can
wire the full end-to-end response shape without a trained model. Replaced in
Phase 4 by the real MobileNet multi-head ONNX.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ClassifierResult:
    skin_type: str
    skin_type_scores: dict[str, float]
    condition_scores: dict[str, float]
    confidence: float
    inference_mode: str


def placeholder_classify(
    patch_tensor: np.ndarray,
    skin_types: tuple[str, ...],
    conditions: tuple[str, ...],
    questionnaire: dict,
) -> ClassifierResult:
    """Uniform-prior output marked as a placeholder.

    `patch_tensor` is accepted so the call site matches the real classifier's
    signature — keeps the refactor in Phase 4 to a single-file swap.
    """
    _ = patch_tensor
    skin_type_scores = {label: round(1.0 / len(skin_types), 4) for label in skin_types}
    condition_scores = {label: 0.5 for label in conditions}

    # If the questionnaire carries a clear hint, bias the skin-type distribution
    # a bit so the placeholder isn't completely useless in demos.
    hint = _questionnaire_skin_type_hint(questionnaire)
    if hint and hint in skin_type_scores:
        skin_type_scores = {label: 0.15 for label in skin_types}
        skin_type_scores[hint] = round(1.0 - 0.15 * (len(skin_types) - 1), 4)

    skin_type = max(skin_type_scores, key=skin_type_scores.get)
    return ClassifierResult(
        skin_type=skin_type,
        skin_type_scores=skin_type_scores,
        condition_scores=condition_scores,
        confidence=0.3,
        inference_mode="placeholder_phase1",
    )


_SKIN_FEEL_HINTS = {
    "very_oily": "Oily",
    "slightly_oily": "Combination",
    "mixed": "Combination",
    "balanced": "Normal",
    "dry": "Dry",
    "hydrated": "Normal",
}


def _questionnaire_skin_type_hint(questionnaire: dict) -> str | None:
    for key in ("oil_levels", "moisture_level", "skin_feel"):
        val = questionnaire.get(key)
        if isinstance(val, str) and val in _SKIN_FEEL_HINTS:
            return _SKIN_FEEL_HINTS[val]
    return None
