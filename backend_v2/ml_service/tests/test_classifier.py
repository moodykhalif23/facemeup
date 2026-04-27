"""ONNX classifier + heatmap tests.

Uses a tiny random-weights ONNX stub so we cover the full classifier + heatmap
code path without needing the real Phase 3 checkpoint.
"""

from __future__ import annotations

import numpy as np

from app.config import get_settings
from app.pipeline.classify import ONNXClassifier, placeholder_classify
from app.pipeline.heatmaps import generate_heatmaps


def test_stub_onnx_is_valid(stub_onnx_path) -> None:
    assert stub_onnx_path.is_file()
    assert stub_onnx_path.stat().st_size > 100


def test_onnx_classifier_basic_shapes(stub_onnx_session) -> None:
    settings = get_settings()
    clf = ONNXClassifier(stub_onnx_session, settings.conditions)

    # 5 patches (mirrors the pipeline output)
    tensor = np.random.default_rng(0).normal(size=(5, 3, 224, 224)).astype(np.float32)
    result = clf.classify(tensor, settings.skin_types, questionnaire={"oil_levels": "very_oily"})

    assert result.inference_mode == "onnx_mobilenet"
    assert set(result.condition_scores.keys()) == set(settings.conditions)
    assert all(0.0 <= p <= 1.0 for p in result.condition_scores.values())
    assert result.skin_type == "Oily"   # questionnaire hint
    assert set(result.skin_type_scores.keys()) == set(settings.skin_types)
    # skin-type distribution sums close to 1
    assert abs(sum(result.skin_type_scores.values()) - 1.0) < 0.01


def test_onnx_classifier_rejects_wrong_shape(stub_onnx_session) -> None:
    import pytest
    settings = get_settings()
    clf = ONNXClassifier(stub_onnx_session, settings.conditions)
    with pytest.raises(ValueError):
        clf.classify(np.zeros((0, 3, 224, 224), dtype=np.float32), settings.skin_types, {})
    with pytest.raises(ValueError):
        clf.classify(np.zeros((3, 224, 224), dtype=np.float32), settings.skin_types, {})


def test_heatmaps_skipped_when_below_threshold(stub_onnx_session) -> None:
    settings = get_settings()
    clf = ONNXClassifier(stub_onnx_session, settings.conditions)

    patches_imagenet = np.random.default_rng(1).normal(size=(5, 3, 224, 224)).astype(np.float32)
    patches_raw = [
        np.random.default_rng(2 + i).integers(0, 255, (224, 224, 3), dtype=np.uint8)
        for i in range(5)
    ]
    regions = ["forehead", "left_cheek", "right_cheek", "nose", "chin"]
    # Force all probabilities below threshold → no heatmaps emitted.
    baseline = np.full((5, len(settings.conditions)), 0.3, dtype=np.float32)

    hm = generate_heatmaps(
        session=stub_onnx_session,
        input_name=clf._input_name,
        output_name=clf._output_name,
        patches_imagenet=patches_imagenet,
        patches_raw=patches_raw,
        patch_regions=regions,
        condition_names=settings.conditions,
        baseline_probs=baseline,
        threshold=0.5,
    )
    assert hm == []


def test_heatmaps_generated_for_active_conditions(stub_onnx_session) -> None:
    settings = get_settings()
    clf = ONNXClassifier(stub_onnx_session, settings.conditions)

    patches_imagenet = np.random.default_rng(3).normal(size=(5, 3, 224, 224)).astype(np.float32)
    patches_raw = [
        np.random.default_rng(4 + i).integers(0, 255, (224, 224, 3), dtype=np.uint8)
        for i in range(5)
    ]
    regions = ["forehead", "left_cheek", "right_cheek", "nose", "chin"]
    # Force Acne (idx 0) high on forehead (patch 0), everything else low.
    baseline = np.full((5, len(settings.conditions)), 0.2, dtype=np.float32)
    baseline[0, 0] = 0.85

    hm = generate_heatmaps(
        session=stub_onnx_session,
        input_name=clf._input_name,
        output_name=clf._output_name,
        patches_imagenet=patches_imagenet,
        patches_raw=patches_raw,
        patch_regions=regions,
        condition_names=settings.conditions,
        baseline_probs=baseline,
        threshold=0.5,
        grid=4,   # smaller grid to keep the test fast
    )
    assert len(hm) == 1
    assert "Acne" in hm[0].label
    assert "forehead" in hm[0].label
    # base64 decodes cleanly to at least a 100-byte PNG
    import base64
    raw = base64.b64decode(hm[0].image_base64)
    assert raw.startswith(b"\x89PNG")
    assert len(raw) > 100


def test_placeholder_classifier_still_works() -> None:
    settings = get_settings()
    tensor = np.zeros((5, 3, 224, 224), dtype=np.float32)
    out = placeholder_classify(tensor, settings.skin_types, settings.conditions, {"oil_levels": "dry"})
    assert out.inference_mode == "placeholder_phase1"
    assert out.skin_type == "Dry"
    assert set(out.condition_scores.keys()) == set(settings.conditions)
