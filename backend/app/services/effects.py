from __future__ import annotations

from typing import Iterable

# Canonical effects taxonomy with common synonyms.
EFFECT_TAXONOMY: dict[str, list[str]] = {
    "clean": ["clean", "cleansing", "clarify", "purify"],
    "oil control": ["oil control", "sebum control", "mattify", "mattifying"],
    "pore shrinkage": ["pore shrinkage", "pore tightening", "tightening pores", "pore care"],
    "replenishment": ["replenishment", "replenish", "rejuvenation"],
    "moisture": ["moisture", "moisturize", "moisturising", "hydration", "hydrate"],
    "lock water": ["lock water", "water lock", "water retention"],
    "skin whitening": ["skin whitening", "whitening", "brightening"],
    "light spot": ["light spot", "dark spot", "spots", "spot correct"],
    "sunscreen": ["sunscreen", "spf", "sun protection", "uv protection"],
    "oxygen injection": ["oxygen injection", "oxygen boost"],
    "compact": ["compact", "firming", "firm", "tighten"],
    "anti wrinkle": ["anti wrinkle", "anti-wrinkle", "wrinkle", "anti aging", "anti-aging"],
    "antifading": ["antifading", "fade", "fading"],
    "repair": ["repair", "restore", "barrier repair"],
    "soothe": ["soothe", "soothing", "calm", "calming"],
    "acne treatment": ["acne treatment", "anti acne", "acne care", "blemish"],
    "detoxification": ["detoxification", "detox", "purify"],
    "eye care": ["eye care", "eye area", "eye"],
    "antioxidant": ["antioxidant", "anti oxidant", "anti-oxidant"],
    "anti free radical": ["anti free radical", "free radical", "anti-radical"],
    "collagen": ["collagen", "collagen boost", "plumping"],
    "water oil balance": ["water oil balance", "water-oil balance", "oil-water balance"],
    "brighten skin color": ["brighten skin color", "brighten skin", "radiance"],
    "fade acne print": ["fade acne print", "acne print", "acne marks", "post acne"],
    "pouch": ["pouch", "under eye bag", "eye bag"],
    "eye lines": ["eye lines", "fine lines", "crow's feet"],
    "dark circles": ["dark circles", "eye dark circles"],
    "lymphatic detoxification": ["lymphatic detoxification", "lymph detox"],
}

CONDITION_EFFECT_MAP: dict[str, list[str]] = {
    "Acne": ["acne treatment", "clean", "oil control", "pore shrinkage"],
    "Hyperpigmentation": ["skin whitening", "light spot", "brighten skin color", "fade acne print"],
    "Uneven tone": ["skin whitening", "brighten skin color", "light spot"],
    "Dehydration": ["moisture", "lock water", "water oil balance"],
    "Wrinkles": ["anti wrinkle", "collagen", "eye lines"],
    "Fine lines": ["anti wrinkle", "collagen", "eye lines"],
    "Dark spots": ["light spot", "brighten skin color", "skin whitening"],
    "Redness": ["soothe", "repair"],
    "Sensitive": ["soothe", "repair"],
}


_EFFECT_LOOKUP: dict[str, str] = {}
for canon, synonyms in EFFECT_TAXONOMY.items():
    for value in synonyms + [canon]:
        _EFFECT_LOOKUP[value.lower()] = canon


def normalize_effect(value: str) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if not v:
        return None
    if v in _EFFECT_LOOKUP:
        return _EFFECT_LOOKUP[v]
    # Fuzzy contains match
    for key, canon in _EFFECT_LOOKUP.items():
        if key in v:
            return canon
    return None


def normalize_effects(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        canon = normalize_effect(value)
        if canon and canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


def split_effects_csv(csv_value: str | None) -> list[str]:
    if not csv_value:
        return []
    return normalize_effects([v for v in csv_value.split(",") if v.strip()])
