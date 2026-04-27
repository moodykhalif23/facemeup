"""Condition taxonomy and source-to-macro label mapping.

The target label set is a 7-class cosmetic taxonomy aligned to the face-only
GlowMix/Kaggle concern vocabulary:
    Acne, Dryness, Oiliness, Dark Spots, Wrinkles, Redness, Dark Circles

SCIN (Google, ~10k consumer photos) annotates ~93 fine-grained dermatologist
diagnoses plus Fitzpatrick I–VI skin tone. We map the fine labels into macro
categories so the classifier matches the cosmetics-oriented frontend contract.

The mapping is deliberately conservative — we only map conditions where the
spec category is clearly a superset. Anything ambiguous (e.g. "drug rash") is
left as negative across all macro labels.
"""

from __future__ import annotations

from enum import IntEnum


class Condition(IntEnum):
    ACNE = 0
    DRYNESS = 1
    OILINESS = 2
    DARK_SPOTS = 3
    WRINKLES = 4
    REDNESS = 5
    DARK_CIRCLES = 6


CONDITION_NAMES: tuple[str, ...] = (
    "Acne",
    "Dryness",
    "Oiliness",
    "Dark Spots",
    "Wrinkles",
    "Redness",
    "Dark Circles",
)


# SCIN condition-name → list of macro Conditions it implies.
# Case-insensitive substring match. Keep conservative; we err toward unlabelled.
SCIN_MACRO_MAP: dict[str, tuple[Condition, ...]] = {
    # Acne family
    "acne": (Condition.ACNE,),
    "acne vulgaris": (Condition.ACNE,),
    "acne rosacea": (Condition.ACNE, Condition.REDNESS),
    "folliculitis": (Condition.ACNE,),
    "perioral dermatitis": (Condition.ACNE, Condition.REDNESS),
    "hidradenitis": (Condition.ACNE,),
    "comedonal": (Condition.ACNE,),

    # Dryness / barrier damage
    "xerosis": (Condition.DRYNESS,),
    "eczema": (Condition.DRYNESS, Condition.REDNESS),
    "atopic dermatitis": (Condition.DRYNESS, Condition.REDNESS),
    "ichthyosis": (Condition.DRYNESS,),
    "asteatotic": (Condition.DRYNESS,),

    # Oiliness
    "seborrheic dermatitis": (Condition.OILINESS, Condition.REDNESS),
    "seborrhoeic dermatitis": (Condition.OILINESS, Condition.REDNESS),
    "seborrhea": (Condition.OILINESS,),

    # Dark spots / pigmentation
    "melasma": (Condition.DARK_SPOTS,),
    "post-inflammatory hyperpigmentation": (Condition.DARK_SPOTS,),
    "pih": (Condition.DARK_SPOTS,),
    "solar lentigo": (Condition.DARK_SPOTS,),
    "lentigines": (Condition.DARK_SPOTS,),
    "ephelides": (Condition.DARK_SPOTS,),
    "freckles": (Condition.DARK_SPOTS,),
    "cafe au lait": (Condition.DARK_SPOTS,),

    # Wrinkles / aging
    "rhytides": (Condition.WRINKLES,),
    "actinic damage": (Condition.WRINKLES, Condition.DARK_SPOTS),
    "photodamage": (Condition.WRINKLES, Condition.DARK_SPOTS),
    "elastosis": (Condition.WRINKLES,),

    # Redness / vascular
    "rosacea": (Condition.REDNESS,),
    "telangiectasia": (Condition.REDNESS,),
    "erythema": (Condition.REDNESS,),
    "flushing": (Condition.REDNESS,),
}


COSMETIC_MACRO_MAP: dict[str, tuple[Condition, ...]] = {
    # Acne / blemishes
    "acne": (Condition.ACNE,),
    "pimple": (Condition.ACNE,),
    "blemish": (Condition.ACNE,),
    "breakout": (Condition.ACNE,),
    "comedone": (Condition.ACNE,),
    "blackhead": (Condition.ACNE, Condition.OILINESS),

    # Dryness / texture
    "dry": (Condition.DRYNESS,),
    "dryness": (Condition.DRYNESS,),
    "dehydrat": (Condition.DRYNESS,),
    "flaky": (Condition.DRYNESS,),
    "rough": (Condition.DRYNESS,),
    "texture": (Condition.DRYNESS,),

    # Oiliness / pores / shine
    "oily": (Condition.OILINESS,),
    "oiliness": (Condition.OILINESS,),
    "sebum": (Condition.OILINESS,),
    "shine": (Condition.OILINESS,),
    "pore": (Condition.OILINESS,),

    # Pigmentation / dark spots
    "pigment": (Condition.DARK_SPOTS,),
    "dark spot": (Condition.DARK_SPOTS,),
    "spot": (Condition.DARK_SPOTS,),
    "hyperpig": (Condition.DARK_SPOTS,),
    "uneven tone": (Condition.DARK_SPOTS,),
    "discolor": (Condition.DARK_SPOTS,),
    "melasma": (Condition.DARK_SPOTS,),

    # Wrinkles / fine lines
    "wrinkle": (Condition.WRINKLES,),
    "fine line": (Condition.WRINKLES,),
    "aging": (Condition.WRINKLES,),
    "ageing": (Condition.WRINKLES,),

    # Redness / irritation / sensitivity
    "redness": (Condition.REDNESS,),
    "red": (Condition.REDNESS,),
    "irritat": (Condition.REDNESS,),
    "sensitive": (Condition.REDNESS,),
    "sensitivity": (Condition.REDNESS,),
    "rosacea": (Condition.REDNESS,),

    # Dark circles
    "dark circle": (Condition.DARK_CIRCLES,),
    "under eye": (Condition.DARK_CIRCLES,),
    "undereye": (Condition.DARK_CIRCLES,),
    "eye bag": (Condition.DARK_CIRCLES,),
}


def scin_labels_to_vector(scin_labels: list[str]) -> list[int]:
    """Convert SCIN fine-grained labels to the 7-dim cosmetics target vector."""
    return _labels_to_vector(scin_labels, SCIN_MACRO_MAP)


def cosmetic_labels_to_vector(raw_labels: list[str]) -> list[int]:
    """Convert Kaggle/GlowMix-style cosmetic concern labels to the target vector."""
    return _labels_to_vector(raw_labels, COSMETIC_MACRO_MAP)


def _labels_to_vector(
    raw_labels: list[str],
    mapping: dict[str, tuple[Condition, ...]],
) -> list[int]:
    vec = [0] * len(Condition)
    for raw in raw_labels:
        needle = raw.lower().strip()
        for key, macros in mapping.items():
            if key in needle:
                for c in macros:
                    vec[int(c)] = 1
    return vec


class Fitzpatrick(IntEnum):
    I = 1
    II = 2
    III = 3
    IV = 4
    V = 5
    VI = 6


def fitzpatrick_from_str(raw: str | int | None) -> Fitzpatrick | None:
    """Parse a Fitzpatrick value from SCIN (strings like 'II', numbers, or None)."""
    if raw is None:
        return None
    if isinstance(raw, int):
        return Fitzpatrick(raw) if 1 <= raw <= 6 else None
    s = str(raw).strip().upper()
    roman = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
    if s in roman:
        return Fitzpatrick(roman[s])
    try:
        n = int(s)
        if 1 <= n <= 6:
            return Fitzpatrick(n)
    except ValueError:
        pass
    return None
