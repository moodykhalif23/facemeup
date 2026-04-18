"""Condition taxonomy and SCIN-to-macro label mapping.

The target label set is the 6-class taxonomy from spec §1:
    Acne, Dryness, Oiliness, Hyperpigmentation, Wrinkles, Redness

SCIN (Google, ~10k consumer photos) annotates ~93 fine-grained dermatologist
diagnoses plus Fitzpatrick I–VI skin tone. We map the fine labels into macro
categories so the classifier matches the spec and the frontend contract.

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
    HYPERPIGMENTATION = 3
    WRINKLES = 4
    REDNESS = 5


CONDITION_NAMES: tuple[str, ...] = tuple(c.name.title() for c in Condition)


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

    # Hyperpigmentation
    "melasma": (Condition.HYPERPIGMENTATION,),
    "post-inflammatory hyperpigmentation": (Condition.HYPERPIGMENTATION,),
    "pih": (Condition.HYPERPIGMENTATION,),
    "solar lentigo": (Condition.HYPERPIGMENTATION,),
    "lentigines": (Condition.HYPERPIGMENTATION,),
    "ephelides": (Condition.HYPERPIGMENTATION,),
    "freckles": (Condition.HYPERPIGMENTATION,),
    "cafe au lait": (Condition.HYPERPIGMENTATION,),

    # Wrinkles / aging
    "rhytides": (Condition.WRINKLES,),
    "actinic damage": (Condition.WRINKLES, Condition.HYPERPIGMENTATION),
    "photodamage": (Condition.WRINKLES, Condition.HYPERPIGMENTATION),
    "elastosis": (Condition.WRINKLES,),

    # Redness / vascular
    "rosacea": (Condition.REDNESS,),
    "telangiectasia": (Condition.REDNESS,),
    "erythema": (Condition.REDNESS,),
    "flushing": (Condition.REDNESS,),
}


def scin_labels_to_vector(scin_labels: list[str]) -> list[int]:
    """Convert a list of SCIN fine-grained labels to a 6-dim 0/1 macro vector.

    Case-insensitive substring match against SCIN_MACRO_MAP keys; any label that
    contains a mapped key contributes. Unknown labels contribute nothing.
    """
    vec = [0] * len(Condition)
    for raw in scin_labels:
        needle = raw.lower().strip()
        for key, macros in SCIN_MACRO_MAP.items():
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
