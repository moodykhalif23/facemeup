"""Skin inference — Ollama-backed with rule-based questionnaire fallback."""
import logging
from typing import Optional

from app.schemas.analyze import SkinProfile
from app.services.ollama_service import CONDITIONS, SKIN_TYPES, ollama_service

logger = logging.getLogger(__name__)

# ── Questionnaire fallback (no Ollama dependency) ─────────────────────────────

_SKIN_FEEL_MAP = {
    "oily": "Oily", "dry": "Dry", "combination": "Combination",
    "normal": "Normal", "sensitive": "Sensitive",
}
_CONCERN_MAP = {
    "acne": "Acne", "dark_spots": "Hyperpigmentation", "wrinkles": "Wrinkles",
    "redness": "Redness", "dryness": "Dehydration", "oiliness": "Acne",
    "sensitivity": "Redness", "dark_circles": "Hyperpigmentation",
    "blackheads": "Acne", "pigmentation": "Hyperpigmentation", "pores": "Acne",
}


def _questionnaire_profile(questionnaire: Optional[dict]) -> SkinProfile:
    q = questionnaire or {}
    skin_feel = (q.get("skin_feel") or "").lower()
    skin_type = _SKIN_FEEL_MAP.get(skin_feel) or _derive_skin_type(q)

    raw_concerns = q.get("concerns") or []
    conditions = list({_CONCERN_MAP[c] for c in raw_concerns if c in _CONCERN_MAP}) or ["None detected"]

    filled = sum(1 for k in ("skin_feel", "skin_texture", "moisture_level", "oil_levels") if q.get(k))
    confidence = round(min(0.65, 0.35 + filled * 0.075), 4)

    other_st = round((1.0 - confidence) / (len(SKIN_TYPES) - 1), 4)
    skin_type_scores = {s: (confidence if s == skin_type else other_st) for s in SKIN_TYPES}

    detected = set(conditions) - {"None detected"}
    other_cs = round((1.0 - 0.65 * len(detected)) / max(1, len(CONDITIONS) - len(detected)), 4)
    condition_scores = {c: (0.65 if c in detected else other_cs) for c in CONDITIONS}
    if "None detected" in conditions:
        condition_scores["None detected"] = confidence

    return SkinProfile(
        skin_type=skin_type,
        conditions=conditions,
        confidence=confidence,
        skin_type_scores=skin_type_scores,
        condition_scores=condition_scores,
    )


def _derive_skin_type(q: dict) -> str:
    scores = {s: 0 for s in SKIN_TYPES}
    oil = (q.get("oil_levels") or "").lower()
    moisture = (q.get("moisture_level") or "").lower()
    texture = (q.get("skin_texture") or "").lower()

    if oil == "very_oily":       scores["Oily"] += 2
    elif oil == "slightly_oily": scores["Oily"] += 1; scores["Combination"] += 1
    elif oil == "mixed":         scores["Combination"] += 2

    if moisture == "dry":        scores["Dry"] += 2
    elif moisture in ("hydrated", "balanced"): scores["Normal"] += 1

    if texture == "rough":       scores["Dry"] += 1; scores["Sensitive"] += 1
    elif texture == "smooth":    scores["Normal"] += 1
    elif texture == "mixed":     scores["Combination"] += 1

    concerns = set(q.get("concerns") or [])
    if "sensitivity" in concerns or "redness" in concerns:
        scores["Sensitive"] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "Normal"


# ── Main entry point (same signature as before) ───────────────────────────────

def run_skin_inference(
    image_base64: str,
    landmarks: Optional[list] = None,
    questionnaire: Optional[dict] = None,
) -> tuple[SkinProfile, str]:
    """
    Analyse skin using Ollama.
    Priority: vision (LLaVA) → questionnaire (Llama) → rule-based fallback.
    Signature is identical to the previous TensorFlow implementation.
    """
    # 1. Image analysis via LLaVA
    if image_base64:
        result = ollama_service.analyze_image(image_base64, questionnaire)
        if result:
            return result

    # 2. Questionnaire analysis via Llama
    if questionnaire:
        result = ollama_service.analyze_questionnaire(questionnaire)
        if result:
            return result

    # 3. Rule-based fallback (no Ollama required)
    logger.warning("Ollama unavailable — using rule-based questionnaire fallback")
    return _questionnaire_profile(questionnaire), "questionnaire_fallback"
