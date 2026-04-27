"""Tests for the SCIN body-part filter and schema helpers."""

from skin_training.data.scin import (
    FACE_BODY_PARTS,
    _find_body_col,
    _is_face_region,
    body_part_distribution,
)


def test_face_terms_match_expected_regions():
    assert "face" in FACE_BODY_PARTS
    assert "neck" in FACE_BODY_PARTS
    assert "scalp" in FACE_BODY_PARTS
    assert "cheek" in FACE_BODY_PARTS


def test_is_face_region_accepts_face_values():
    assert _is_face_region("face", FACE_BODY_PARTS)
    assert _is_face_region("Face/Cheek", FACE_BODY_PARTS)
    assert _is_face_region("perioral region", FACE_BODY_PARTS)
    assert _is_face_region("scalp", FACE_BODY_PARTS)
    assert _is_face_region("Neck", FACE_BODY_PARTS)


def test_is_face_region_rejects_non_face():
    assert not _is_face_region("arm", FACE_BODY_PARTS)
    assert not _is_face_region("leg", FACE_BODY_PARTS)
    assert not _is_face_region("torso", FACE_BODY_PARTS)
    assert not _is_face_region("hand", FACE_BODY_PARTS)
    assert not _is_face_region("back", FACE_BODY_PARTS)
    assert not _is_face_region("", FACE_BODY_PARTS)


def test_find_body_col_detects_known_names():
    assert _find_body_col(["case_id", "body_part", "condition"]) == "body_part"
    assert _find_body_col(["id", "anatom_site", "fst"]) == "anatom_site"
    assert _find_body_col(["case_id", "location"]) == "location"
    assert _find_body_col(["case_id", "unrelated_col"]) is None


def test_body_part_distribution_counts_correctly():
    from dataclasses import dataclass
    from pathlib import Path
    from skin_training.data.scin import SCINSample

    def make(bp: str) -> SCINSample:
        return SCINSample(
            case_id="x", image_path=Path("/x.jpg"),
            label_vector=(0,)*6, raw_conditions=(),
            fitzpatrick=None, body_part=bp
        )

    samples = [make("face"), make("face"), make("arm"), make(None)]
    dist = body_part_distribution(samples)
    assert dist["face"] == 2
    assert dist["arm"] == 1
    assert dist["unknown"] == 1
