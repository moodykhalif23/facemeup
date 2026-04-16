"""Ollama-backed inference: replaces TensorFlow SavedModel for skin analysis and recommendations."""
import json
import logging

import httpx

from app.core.config import settings
from app.schemas.analyze import SkinProfile

logger = logging.getLogger(__name__)

SKIN_TYPES = ["Oily", "Dry", "Combination", "Normal", "Sensitive"]
CONDITIONS = ["Acne", "Hyperpigmentation", "Uneven tone", "Redness", "Dehydration", "Wrinkles", "None detected"]


class OllamaService:
    def __init__(self) -> None:
        self._base = settings.ollama_url.rstrip("/")
        self._vision = settings.ollama_vision_model
        self._text = settings.ollama_text_model

    # ── internal ──────────────────────────────────────────────────────────────

    def _call(self, model: str, prompt: str, image_b64: str | None = None) -> dict | None:
        payload: dict = {"model": model, "prompt": prompt, "stream": False, "format": "json"}
        if image_b64:
            payload["images"] = [image_b64]
        # Vision model needs more time for image processing; text model is fast
        timeout = 150.0 if image_b64 else 45.0
        try:
            r = httpx.post(f"{self._base}/api/generate", json=payload, timeout=timeout)
            r.raise_for_status()
            return json.loads(r.json()["response"])
        except Exception as exc:
            logger.warning("Ollama (%s) failed: %s", model, exc)
            return None

    def _build_profile(self, data: dict) -> SkinProfile:
        skin_type = data.get("skin_type", "Normal")
        if skin_type not in SKIN_TYPES:
            skin_type = "Normal"

        conditions = [c for c in (data.get("conditions") or []) if c in CONDITIONS]
        if not conditions:
            conditions = ["None detected"]

        confidence = round(min(max(float(data.get("confidence", 0.5)), 0.0), 1.0), 4)

        raw_st = data.get("skin_type_scores") or {}
        skin_type_scores = {s: round(float(raw_st.get(s, 0.0)), 4) for s in SKIN_TYPES}
        if not any(skin_type_scores.values()):
            other = round((1.0 - confidence) / (len(SKIN_TYPES) - 1), 4)
            skin_type_scores = {s: (confidence if s == skin_type else other) for s in SKIN_TYPES}

        raw_cs = data.get("condition_scores") or {}
        condition_scores = {c: round(float(raw_cs.get(c, 0.0)), 4) for c in CONDITIONS}
        if not any(condition_scores.values()):
            for c in conditions:
                if c != "None detected":
                    condition_scores[c] = confidence

        return SkinProfile(
            skin_type=skin_type,
            conditions=conditions,
            confidence=confidence,
            skin_type_scores=skin_type_scores,
            condition_scores=condition_scores,
        )

    # ── public API ────────────────────────────────────────────────────────────

    def analyze_image(self, image_b64: str, questionnaire: dict | None = None) -> tuple[SkinProfile, str] | None:
        """Analyze a face photo with LLaVA. Returns (SkinProfile, mode) or None if Ollama unavailable."""
        extra = ""
        if questionnaire:
            extra = (
                f"\nUser also reported: oil_levels={questionnaire.get('oil_levels')}, "
                f"moisture={questionnaire.get('moisture_level')}, concerns={questionnaire.get('concerns')}."
            )

        prompt = (
            f"Analyze this face photo for skin type and conditions.{extra}\n"
            f"Skin types: {SKIN_TYPES}\n"
            f"Conditions: {CONDITIONS}\n"
            "Return JSON with keys: skin_type (string), conditions (array), confidence (float 0-1), "
            "skin_type_scores (object, all types), condition_scores (object, all conditions)."
        )

        data = self._call(self._vision, prompt, image_b64)
        if not data or "skin_type" not in data:
            return None
        return self._build_profile(data), "ollama_vision"

    def analyze_questionnaire(self, questionnaire: dict) -> tuple[SkinProfile, str] | None:
        """Analyze questionnaire answers with Llama. Returns (SkinProfile, mode) or None if unavailable."""
        prompt = (
            f"Analyze this skin questionnaire and determine skin type and conditions.\n"
            f"Answers: {json.dumps(questionnaire)}\n"
            f"Skin types: {SKIN_TYPES}\n"
            f"Conditions: {CONDITIONS}\n"
            "Return JSON: skin_type (string), conditions (array), confidence (float 0-0.65 max for questionnaire), "
            "skin_type_scores (object), condition_scores (object)."
        )

        data = self._call(self._text, prompt)
        if not data or "skin_type" not in data:
            return None
        return self._build_profile(data), "ollama_questionnaire"

    def rank_products(self, skin_type: str, conditions: list[str], candidates: list[dict]) -> list[str]:
        """Re-rank candidate products by relevance. Returns ordered SKU list; falls back to original order."""
        if not candidates:
            return []

        lines = "\n".join(
            f"SKU:{p['sku']} | {p['name']} | ingredients:{p['ingredients']} | effects:{p['effects']}"
            for p in candidates
        )
        prompt = (
            f"Rank these skincare products for skin type '{skin_type}' with conditions {conditions}.\n"
            f"Products:\n{lines}\n"
            'Return JSON: {"ranked_skus": ["sku1", "sku2", ...]} — all SKUs, best match first.'
        )

        data = self._call(self._text, prompt)
        ranked = (data or {}).get("ranked_skus")
        if not ranked or not isinstance(ranked, list):
            return [p["sku"] for p in candidates]

        # Preserve any candidates not returned by the model (append at end)
        seen = set(ranked)
        tail = [p["sku"] for p in candidates if p["sku"] not in seen]
        return ranked + tail


ollama_service = OllamaService()
