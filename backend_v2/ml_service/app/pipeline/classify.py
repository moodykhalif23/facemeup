"""Condition classifier.

Two implementations behind one interface:

- `ONNXClassifier` — production path. Loads the ONNX artefact exported by
  `ml_training` (shape: input image [N,3,H,W] float32, output condition_probs
  [N, n_conditions] sigmoid-applied).
- `placeholder_classify` — used when no ONNX model is installed. Returns
  uniform probabilities with a questionnaire-derived skin-type hint so the
  pipeline stays usable during development / Phase 3 training.
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


# ---------------------------------------------------------------------------
# ONNX-backed classifier
# ---------------------------------------------------------------------------


class ONNXClassifier:
    def __init__(self, session, conditions: tuple[str, ...]):
        self._session = session
        self._conditions = conditions
        inputs = session.get_inputs()
        outputs = session.get_outputs()
        if len(inputs) != 1:
            raise ValueError(f"classifier ONNX expects 1 input, got {len(inputs)}")
        self._input_name = inputs[0].name
        self._output_name = outputs[0].name

    def classify(
        self,
        patch_tensor: np.ndarray,
        skin_types: tuple[str, ...],
        questionnaire: dict,
    ) -> ClassifierResult:
        """patch_tensor: (N, 3, H, W) imagenet-normalised float32."""
        if patch_tensor.ndim != 4 or patch_tensor.shape[0] == 0:
            raise ValueError(f"expected (N,3,H,W) non-empty batch; got {patch_tensor.shape}")

        probs = self._session.run([self._output_name], {self._input_name: patch_tensor})[0]
        if probs.ndim != 2 or probs.shape[1] != len(self._conditions):
            raise ValueError(
                f"classifier produced shape {probs.shape}; expected (N, {len(self._conditions)})"
            )

        # Multi-instance learning: max-pool each condition across patches.
        per_condition = probs.max(axis=0)
        condition_scores = {
            name: float(per_condition[i]) for i, name in enumerate(self._conditions)
        }

        # Skin type stays questionnaire-derived until the head is trained.
        skin_type_scores, skin_type = _skin_type_from_questionnaire(
            skin_types, questionnaire
        )
        confidence = float(np.mean(np.abs(per_condition - 0.5) * 2.0))

        return ClassifierResult(
            skin_type=skin_type,
            skin_type_scores=skin_type_scores,
            condition_scores=condition_scores,
            confidence=round(confidence, 4),
            inference_mode="onnx_mobilenet",
        )


# ---------------------------------------------------------------------------
# Placeholder classifier (used when no ONNX model is present)
# ---------------------------------------------------------------------------


def placeholder_classify(
    patch_tensor: np.ndarray,
    skin_types: tuple[str, ...],
    conditions: tuple[str, ...],
    questionnaire: dict,
) -> ClassifierResult:
    """Returns uniform-prior output. Call site matches ONNXClassifier.classify."""
    _ = patch_tensor
    skin_type_scores, skin_type = _skin_type_from_questionnaire(skin_types, questionnaire)
    condition_scores = {label: 0.5 for label in conditions}
    return ClassifierResult(
        skin_type=skin_type,
        skin_type_scores=skin_type_scores,
        condition_scores=condition_scores,
        confidence=0.3,
        inference_mode="placeholder_phase1",
    )


# ---------------------------------------------------------------------------
# Shared questionnaire → skin-type logic
# ---------------------------------------------------------------------------


_SKIN_FEEL_HINTS = {
    "very_oily": "Oily",
    "slightly_oily": "Combination",
    "mixed": "Combination",
    "balanced": "Normal",
    "dry": "Dry",
    "hydrated": "Normal",
}


def _skin_type_from_questionnaire(
    skin_types: tuple[str, ...], questionnaire: dict
) -> tuple[dict[str, float], str]:
    """Return (per-type score dict, argmax label)."""
    hint = None
    for key in ("oil_levels", "moisture_level", "skin_feel"):
        val = questionnaire.get(key)
        if isinstance(val, str) and val in _SKIN_FEEL_HINTS:
            hint = _SKIN_FEEL_HINTS[val]
            break

    if hint and hint in skin_types:
        scores = {label: 0.15 for label in skin_types}
        scores[hint] = round(1.0 - 0.15 * (len(skin_types) - 1), 4)
        return scores, hint

    uniform = round(1.0 / len(skin_types), 4)
    scores = {label: uniform for label in skin_types}
    return scores, skin_types[0]
