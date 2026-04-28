"""Groq Llama-3.2-Vision inference provider.

Calls the Groq API with the raw (or aligned) face image and a structured prompt
that returns skin analysis in JSON. No face detection required — handles
close-up skin shots that Haar / RetinaFace miss.

Priority in app/main.py:
    1. Groq   (if GROQ_API_KEY set)
    2. ONNX   (if skin_classifier_mobilenet.onnx present)
    3. Placeholder (always available)

Why Groq:
    - 97.6% Haar skip rate on SCIN close-up images
    - 300 ms latency on Groq LPU vs 90+ s Ollama
    - No training data needed until custom ONNX checkpoint improves
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

_DISCLAIMER = (
    "This analysis is informational and does not replace professional dermatology advice."
)

_SKIN_ANALYSIS_PROMPT = """\
You are a professional dermatology AI assistant. Analyze the provided skin image and return ONLY a valid JSON object — no markdown, no explanation, just the JSON.

Assess these 7 facial skin concerns (score 0.0–1.0, where 1.0 = highly visible):
- Acne (pimples, papules, pustules, blackheads, clogged pores)
- Dryness (tight-looking skin, flakiness, rough texture, lack of moisture)
- Oiliness (shine, enlarged pores, sebum)
- Dark Spots (hyperpigmentation, melasma, post-acne marks, uneven tone)
- Wrinkles (fine lines, creases, loss of firmness)
- Redness (erythema, rosacea, irritation, visible capillaries)
- Dark Circles (under-eye darkness or puffiness)

Choose the dominant skin type:
- Oily, Dry, Combination, Normal, or Sensitive

Return this exact JSON structure:
{
  "skin_type": "Combination",
  "skin_type_scores": {
    "Oily": 0.2,
    "Dry": 0.1,
    "Combination": 0.6,
    "Normal": 0.08,
    "Sensitive": 0.02
  },
  "condition_scores": {
    "Acne": 0.0,
    "Dryness": 0.0,
    "Oiliness": 0.0,
    "Dark Spots": 0.0,
    "Wrinkles": 0.0,
    "Redness": 0.0,
    "Dark Circles": 0.0
  },
  "confidence": 0.75
}

Rules:
- skin_type_scores must sum to 1.0
- condition_scores between 0.0 and 1.0
- confidence 0.0–1.0 (your certainty about the overall assessment)
- If image quality is too low to assess, return confidence < 0.4
- Return ONLY the JSON, nothing else"""


class GroqProvider:
    """Calls Groq Llama-3.2-Vision for skin analysis."""

    def __init__(self, api_key: str, model: str, skin_types: tuple, conditions: tuple):
        from groq import Groq
        self._client = Groq(api_key=api_key)
        self._model = model
        self._skin_types = skin_types
        self._conditions = conditions
        log.info("Groq provider initialised: model=%s", model)

    def analyze(
        self,
        image_bgr: np.ndarray | None,
        image_b64_raw: str,
        questionnaire: dict,
    ) -> ClassifierResult:
        """Run Groq vision inference.

        Prefers `image_bgr` (aligned, CLAHE-normalised) if available;
        falls back to `image_b64_raw` (original upload) when face detection failed.
        """
        b64 = _prepare_b64(image_bgr, image_b64_raw)
        prompt = _build_prompt(questionnaire)

        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            log.error("Groq API error: %s", e)
            raise

        raw = resp.choices[0].message.content
        return self._parse(raw)

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
        # Normalise so they sum to 1.
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


def _prepare_b64(image_bgr: np.ndarray | None, fallback_b64: str) -> str:
    """Return a JPEG base64 string, resized to ≤512px to keep token count low."""
    import cv2

    if image_bgr is not None:
        h, w = image_bgr.shape[:2]
        if max(h, w) > 512:
            scale = 512 / max(h, w)
            image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        buf = BytesIO()
        Image.fromarray(rgb).save(buf, format="JPEG", quality=88)
        return base64.b64encode(buf.getvalue()).decode("ascii")

    # Fallback: use raw upload, strip data: prefix, re-encode at reduced size.
    raw = base64.b64decode(
        fallback_b64.split(",", 1)[1] if "," in fallback_b64 else fallback_b64
    )
    img = Image.open(BytesIO(raw)).convert("RGB")
    img.thumbnail((512, 512), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _build_prompt(questionnaire: dict) -> str:
    """Augment the base prompt with questionnaire context when available."""
    if not questionnaire:
        return _SKIN_ANALYSIS_PROMPT

    ctx_parts = []
    mappings = {
        "oil_levels":    "Self-reported oil level",
        "moisture_level":"Self-reported moisture",
        "skin_texture":  "Self-reported texture",
        "concerns":      "User's main concerns",
        "age":           "Age",
        "gender":        "Gender",
    }
    for key, label in mappings.items():
        val = questionnaire.get(key)
        if val:
            ctx_parts.append(f"- {label}: {val}")

    if not ctx_parts:
        return _SKIN_ANALYSIS_PROMPT

    extra = (
        "\n\nAdditional context from the user's self-assessment:\n"
        + "\n".join(ctx_parts)
        + "\nUse this as supporting context, but prioritise what you observe in the image."
    )
    return _SKIN_ANALYSIS_PROMPT + extra


def _fallback_result(skin_types: tuple, conditions: tuple) -> ClassifierResult:
    """Return a uniform-prior result when Groq response can't be parsed."""
    return ClassifierResult(
        skin_type=skin_types[0],
        skin_type_scores={t: round(1 / len(skin_types), 4) for t in skin_types},
        condition_scores={c: 0.3 for c in conditions},
        confidence=0.2,
        inference_mode="groq_parse_error",
    )
