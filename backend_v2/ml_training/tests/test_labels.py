from skin_training.data.labels import (
    Condition,
    fitzpatrick_from_str,
    scin_labels_to_vector,
)


def test_condition_enum_has_6_members() -> None:
    assert len(Condition) == 7
    assert Condition.ACNE == 0
    assert Condition.REDNESS == 5
    assert Condition.DARK_CIRCLES == 6


def test_acne_maps_to_macro_acne() -> None:
    vec = scin_labels_to_vector(["Acne vulgaris"])
    assert vec[Condition.ACNE] == 1
    assert sum(vec) == 1


def test_seborrheic_dermatitis_triggers_oiliness_and_redness() -> None:
    vec = scin_labels_to_vector(["Seborrheic dermatitis"])
    assert vec[Condition.OILINESS] == 1
    assert vec[Condition.REDNESS] == 1


def test_melasma_is_hyperpigmentation() -> None:
    vec = scin_labels_to_vector(["Melasma"])
    assert vec[Condition.DARK_SPOTS] == 1
    assert sum(vec) == 1


def test_multiple_labels_aggregate() -> None:
    vec = scin_labels_to_vector(["Acne vulgaris", "Melasma", "Rosacea"])
    assert vec[Condition.ACNE] == 1
    assert vec[Condition.DARK_SPOTS] == 1
    assert vec[Condition.REDNESS] == 1


def test_unknown_label_is_noop() -> None:
    vec = scin_labels_to_vector(["Totally Unknown Condition"])
    assert sum(vec) == 0


def test_fitzpatrick_roman_parse() -> None:
    assert fitzpatrick_from_str("III") == 3
    assert fitzpatrick_from_str("vi") == 6


def test_fitzpatrick_numeric_parse() -> None:
    assert fitzpatrick_from_str(4) == 4
    assert fitzpatrick_from_str("2") == 2


def test_fitzpatrick_invalid_returns_none() -> None:
    assert fitzpatrick_from_str(None) is None
    assert fitzpatrick_from_str("garbage") is None
    assert fitzpatrick_from_str(7) is None
    assert fitzpatrick_from_str(0) is None
