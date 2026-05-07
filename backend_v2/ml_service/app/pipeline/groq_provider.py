"""Groq Llama-Vision inference provider — calibrated for phone-captured close-ups.

Calls the Groq vision API with the aligned face plus per-region patches and a
prompt tuned to match the Bitmoji device's level → score semantics. The phone
camera is single-modality (visible light only), so we deliberately:

  - send patches at higher resolution (768 px) than the legacy 512 px,
  - send 3-5 region patches alongside the full face so the model can resolve
    pores / wrinkles / under-eye detail it would miss in a wide shot,
  - bias the prompt toward flagging mild conditions, since the consumer-facing
    score → "active" cutoff is now 0.30 (matches Bitmoji level > 2).

Provider priority (see app/main.py):
    1. Groq vision  (this file)         — current production path
    2. ONNX         (skin_classifier.onnx, when trained)
    3. Placeholder  (always available)
"""

from __future__ import annotations

import base64
import json
import logging
from io import BytesIO

import numpy as np
from PIL import Image

from ..pipeline.classify import ClassifierResult

log = logging.getLogger(__name__)

# Maximum side length used when re-encoding before sending. 768 keeps the
# token cost modest while preserving enough detail for visible pore / fine-
# wrinkle cues. Bumping past 1024 has not measurably improved agreement with
# the Bitmoji device in our tests.
_MAX_SIDE = 768
_PATCH_MAX_SIDE = 384
# Groq's vision API accepts at most 5 images per request. With the full face
# counted, that leaves room for 4 region crops. The pipeline selects the most
# skin-rich crops first, so dropping the tail loses the least signal.
_MAX_REGION_CROPS = 4

_DISCLAIMER = (
    "This analysis is informational and does not replace professional dermatology advice."
)

_SKIN_ANALYSIS_PROMPT = """\
You are a dermatology AI grading a phone-captured close-up of a single person's face. Return ONLY a valid JSON object — no markdown, no explanation.

Inputs you will receive (in order):
  1. The full aligned face (always present).
  2. Up to 5 region crops at higher zoom: forehead, left_cheek, right_cheek, nose, chin.
     Use these to resolve fine-grained signs (pores, fine wrinkles, sebum sheen,
     under-eye darkness, hyperpigmentation) that wash out in a wide shot.

Score these 7 concerns on 0.00–1.00 with this calibration:

  0.00–0.15  not present / clearly clear
  0.15–0.30  trace / barely visible
  0.30–0.55  mild but evident — the user would notice
  0.55–0.80  moderate, clearly visible to a casual observer
  0.80–1.00  severe / dominant

The downstream UI flags anything ≥ 0.30 as an active condition, so do not be
falsely conservative — if a sign is mildly but genuinely visible, score ≥ 0.30.
Equivalently, anything you would call "level 2 of 5" or higher → score ≥ 0.30.

Concerns and where to look:
  - Acne          → forehead, cheeks, chin (papules, pustules, blackheads, clogged pores)
  - Dryness       → cheeks, around mouth (tightness, flaking, dull rough texture)
  - Oiliness      → forehead, nose (T-zone), cheeks (specular shine, sebum sheen)
  - Dark Spots    → cheeks, forehead (post-acne marks, melasma, sun spots, uneven tone)
  - Wrinkles      → forehead lines, crow's feet around eyes, nasolabial folds, lip lines
  - Redness       → cheeks, nose, around nostrils (erythema, visible capillaries, irritation)
  - Dark Circles  → under-eye area (darkness, hollowness, puffiness)

Skin type — choose ONE that best fits the dominant pattern:
  Oily, Dry, Combination, Normal, Sensitive

Return EXACTLY this JSON shape (numbers as decimals, no trailing comments):
{
  "skin_type": "Combination",
  "skin_type_scores": {
    "Oily": 0.20, "Dry": 0.10, "Combination": 0.60, "Normal": 0.08, "Sensitive": 0.02
  },
  "condition_scores": {
    "Acne": 0.0, "Dryness": 0.0, "Oiliness": 0.0,
    "Dark Spots": 0.0, "Wrinkles": 0.0, "Redness": 0.0, "Dark Circles": 0.0
  },
  "regions": {
    "forehead":    {"oiliness": 0.0, "wrinkles": 0.0, "acne": 0.0},
    "left_cheek":  {"acne": 0.0, "dark_spots": 0.0, "redness": 0.0, "pores": 0.0},
    "right_cheek": {"acne": 0.0, "dark_spots": 0.0, "redness": 0.0, "pores": 0.0},
    "nose":        {"oiliness": 0.0, "blackheads": 0.0, "redness": 0.0},
    "chin":        {"acne": 0.0, "dryness": 0.0}
  },
  "confidence": 0.75
}

Rules:
- skin_type_scores must sum to 1.0 (±0.02).
- All scores between 0.0 and 1.0.
- "regions" object: only include keys for crops you actually received; omit the rest.
- If image quality is too low to assess (severe blur, occlusion, no face visible),
  return "confidence" < 0.40 and keep all condition_scores low.
- Return ONLY the JSON, nothing else."""


class GroqProvider:
    """Calls Groq's vision endpoint with full face + region crops."""

    def __init__(self, api_key: str, model: str, skin_types: tuple, conditions: tuple):
        from groq import Groq
        self._client = Groq(api_key=api_key)
        self._model = model
        self._skin_types = skin_types
        self._conditions = conditions
        log.info("Groq provider initialised: model=%s max_side=%d patch_side=%d",
                 model, _MAX_SIDE, _PATCH_MAX_SIDE)

    def analyze(
        self,
        image_bgr: np.ndarray | None,
        image_b64_raw: str,
        questionnaire: dict,
        region_patches: list[tuple[str, np.ndarray]] | None = None,
    ) -> ClassifierResult:
        """Run Groq vision inference.

        Inputs:
            image_bgr: aligned + CLAHE-normalised face from the preprocess
                pipeline. May be None if face detection failed.
            image_b64_raw: original upload, used as fallback when image_bgr
                is None.
            questionnaire: user self-assessment context (oil level, age, etc.).
            region_patches: optional list of (region_name, BGR-image) tuples.
                When supplied, each is re-encoded and sent alongside the full
                face so the model can resolve fine-grained signs.
        """
        full_b64 = _prepare_b64(image_bgr, image_b64_raw, max_side=_MAX_SIDE)

        content: list[dict] = [
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{full_b64}"}},
        ]
        attached_regions: list[str] = []
        # Groq's vision endpoint caps at 5 images per request, so with the full
        # face counted we have room for at most 4 region crops. We prefer the
        # informationally-richest regions in this priority order; the caller
        # can pre-filter for skin_ratio and we'll keep the head of the list.
        if region_patches:
            for region, patch_bgr in region_patches[: _MAX_REGION_CROPS]:
                if patch_bgr is None or patch_bgr.size == 0:
                    continue
                patch_b64 = _encode_bgr_jpeg(patch_bgr, max_side=_PATCH_MAX_SIDE)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{patch_b64}"},
                })
                attached_regions.append(region)

        prompt = _build_prompt(questionnaire, attached_regions)
        content.append({"type": "text", "text": prompt})

        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": content}],
                temperature=0.1,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            log.error("Groq API error: %s", e)
            raise

        raw = resp.choices[0].message.content
        result = self._parse(raw)
        log.info("groq inference: regions=%s skin_type=%s confidence=%s",
                 attached_regions or "none", result.skin_type, result.confidence)
        return result

    def _parse(self, raw: str) -> ClassifierResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            log.warning("Groq returned non-JSON: %s … raw=%s", e, raw[:200])
            return _fallback_result(self._skin_types, self._conditions)

        skin_type = str(data.get("skin_type", self._skin_types[0]))
        if skin_type not in self._skin_types:
            skin_type = self._skin_types[0]

        raw_st_scores = data.get("skin_type_scores", {})
        skin_type_scores = {
            t: float(raw_st_scores.get(t, 1.0 / len(self._skin_types)))
            for t in self._skin_types
        }
        total = sum(skin_type_scores.values()) or 1.0
        skin_type_scores = {k: round(v / total, 4) for k, v in skin_type_scores.items()}
        skin_type = max(skin_type_scores, key=skin_type_scores.get)

        raw_cond = data.get("condition_scores", {})
        condition_scores = {
            c: float(max(0.0, min(1.0, raw_cond.get(c, 0.0))))
            for c in self._conditions
        }

        confidence = float(max(0.0, min(1.0, data.get("confidence", 0.6))))

        return ClassifierResult(
            skin_type=skin_type,
            skin_type_scores=skin_type_scores,
            condition_scores=condition_scores,
            confidence=round(confidence, 4),
            inference_mode="groq_llama_vision",
        )


def _prepare_b64(image_bgr: np.ndarray | None, fallback_b64: str, max_side: int) -> str:
    """Return JPEG base64 of the aligned image (preferred) or original upload."""
    if image_bgr is not None and image_bgr.size > 0:
        return _encode_bgr_jpeg(image_bgr, max_side=max_side)

    raw = base64.b64decode(
        fallback_b64.split(",", 1)[1] if "," in fallback_b64 else fallback_b64
    )
    img = Image.open(BytesIO(raw)).convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _encode_bgr_jpeg(image_bgr: np.ndarray, max_side: int) -> str:
    import cv2
    h, w = image_bgr.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)),
                               interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    buf = BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _build_prompt(questionnaire: dict, attached_regions: list[str]) -> str:
    """Augment the base prompt with questionnaire + region-attached context."""
    parts = [_SKIN_ANALYSIS_PROMPT]

    if attached_regions:
        parts.append(
            "\n\nThe attached crops (in order, after the full face) are: "
            + ", ".join(attached_regions) + "."
        )
    else:
        parts.append(
            "\n\nNo region crops were attached — assess from the full face only "
            "and omit the \"regions\" object from your response."
        )

    if questionnaire:
        ctx_parts = []
        mappings = {
            "oil_levels":     "Self-reported oil level",
            "moisture_level": "Self-reported moisture",
            "skin_texture":   "Self-reported texture",
            "concerns":       "User's main concerns",
            "age":            "Age",
            "gender":         "Gender",
        }
        for key, label in mappings.items():
            val = questionnaire.get(key)
            if val:
                ctx_parts.append(f"- {label}: {val}")
        if ctx_parts:
            parts.append(
                "\n\nAdditional context from the user's self-assessment:\n"
                + "\n".join(ctx_parts)
                + "\nUse this as supporting context, but prioritise what you observe in the image."
            )

    return "".join(parts)


def _fallback_result(skin_types: tuple, conditions: tuple) -> ClassifierResult:
    """Uniform-prior result when Groq's response can't be parsed."""
    return ClassifierResult(
        skin_type=skin_types[0],
        skin_type_scores={t: round(1 / len(skin_types), 4) for t in skin_types},
        condition_scores={c: 0.3 for c in conditions},
        confidence=0.2,
        inference_mode="groq_parse_error",
    )
