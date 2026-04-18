import numpy as np
import pytest

from app.config import get_settings
from app.onnx_runner import OnnxRegistry
from app.pipeline import SkinPipeline
from app.pipeline.decode import decode_base64_image
from app.pipeline.landmarks import from_mediapipe
from app.pipeline.normalize import clahe_on_luminance, grey_world_white_balance, normalize
from app.pipeline.patches import extract_patches
from app.pipeline.runner import NoFaceFoundError
from app.pipeline.segment import skin_mask_ycrcb


def test_decode_roundtrip(synthetic_face_b64: str) -> None:
    img = decode_base64_image(synthetic_face_b64)
    assert img.dtype == np.uint8
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.shape[0] > 100 and img.shape[1] > 100


def test_decode_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        decode_base64_image("not-a-valid-base64-payload!!!")


def test_from_mediapipe_requires_full_set() -> None:
    assert from_mediapipe([{"x": 0, "y": 0}], 100, 100) is None


def test_from_mediapipe_produces_5pt(fake_mediapipe_landmarks) -> None:
    lm = from_mediapipe(fake_mediapipe_landmarks, 512, 512)
    assert lm is not None
    arr = lm.as_array()
    assert arr.shape == (5, 2)
    # left eye is to the left of right eye; mouth below nose; nose below eyes
    assert arr[0, 0] < arr[1, 0]
    assert arr[3, 1] > arr[2, 1] > arr[0, 1]


def test_grey_world_is_idempotent_on_grey_image() -> None:
    grey = np.full((64, 64, 3), 128, dtype=np.uint8)
    out = grey_world_white_balance(grey)
    assert np.allclose(out, grey, atol=1)


def test_clahe_preserves_shape(synthetic_face_bgr) -> None:
    out = clahe_on_luminance(synthetic_face_bgr)
    assert out.shape == synthetic_face_bgr.shape
    assert out.dtype == np.uint8


def test_skin_mask_identifies_oval(synthetic_face_bgr) -> None:
    mask = skin_mask_ycrcb(synthetic_face_bgr)
    assert mask.shape == synthetic_face_bgr.shape[:2]
    ratio = float(np.count_nonzero(mask)) / mask.size
    assert 0.05 < ratio < 0.9, f"skin ratio {ratio} out of expected range"


def test_extract_patches_returns_5_regions(synthetic_face_bgr) -> None:
    # Treat the synthetic face as already aligned (it is square and frontal).
    normalized = normalize(synthetic_face_bgr)
    mask = skin_mask_ycrcb(normalized)
    patches = extract_patches(normalized, mask, patch_size=128)
    assert [p.region for p in patches] == [
        "forehead", "left_cheek", "right_cheek", "nose", "chin"
    ]
    for p in patches:
        assert p.image.shape == (128, 128, 3)
        assert 0.0 <= p.skin_ratio <= 1.0


def test_pipeline_with_client_landmarks(synthetic_face_b64, fake_mediapipe_landmarks) -> None:
    settings = get_settings()
    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    pipeline = SkinPipeline(settings, registry, aligned_size=256)

    result = pipeline.run(synthetic_face_b64, client_landmarks=fake_mediapipe_landmarks)

    assert result.detection.source == "client"
    assert result.aligned.shape == (256, 256, 3)
    assert result.skin_mask.shape == (256, 256)
    assert len(result.patches) == 5
    assert result.meta["patch_regions"] == [
        "forehead", "left_cheek", "right_cheek", "nose", "chin"
    ]

    tensor = pipeline.build_classifier_batch(result.patches)
    assert tensor.shape == (5, 3, settings.input_size, settings.input_size)
    assert tensor.dtype == np.float32


def test_pipeline_raises_when_no_face_and_no_landmarks(synthetic_face_b64) -> None:
    settings = get_settings()
    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    pipeline = SkinPipeline(settings, registry)

    # Synthetic oval doesn't look like a real face → Haar should miss it.
    with pytest.raises(NoFaceFoundError):
        pipeline.run(synthetic_face_b64, client_landmarks=None)
