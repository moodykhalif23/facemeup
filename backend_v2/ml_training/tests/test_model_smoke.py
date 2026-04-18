"""Smoke tests — model forward/backward, loss, ONNX export on synthetic tensors.

No real dataset required. Covers the training infrastructure end-to-end.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from skin_training.data.sampler import class_balanced_sampler
from skin_training.eval.metrics import evaluate
from skin_training.models.classifier import build_model
from skin_training.train.losses import MultiHeadLoss, compute_pos_weight


@pytest.fixture(scope="module")
def tiny_model():
    # mobilenetv3_small_100 is ~2M params — much faster than efficientnet_b0 for tests.
    return build_model(
        backbone="mobilenetv3_small_100",
        pretrained=False,
        embed_dim=64,
        dropout=0.1,
        n_conditions=6,
        n_skin_types=5,
        skin_type_head_enabled=False,
    ).eval()


def test_model_forward_shape(tiny_model) -> None:
    x = torch.randn(2, 3, 112, 112)
    out = tiny_model(x)
    assert out.logits_conditions.shape == (2, 6)
    assert out.logits_skin_type is None


def test_model_training_step_reduces_loss(tiny_model) -> None:
    tiny_model.train()
    torch.manual_seed(0)
    optimizer = torch.optim.AdamW(tiny_model.parameters(), lr=1e-3)
    loss_fn = MultiHeadLoss(pos_weight=torch.ones(6), skin_type_weight=0.0)

    # Small but deterministic batch; 3 steps should reduce loss.
    x = torch.randn(4, 3, 112, 112)
    y = torch.tensor([
        [1, 0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0, 1],
        [1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0],
    ], dtype=torch.float32)

    losses = []
    for _ in range(3):
        out = tiny_model(x)
        loss = loss_fn(out.logits_conditions, y).total
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss))
    assert losses[-1] < losses[0], f"loss did not decrease: {losses}"


def test_pos_weight_cap_applied() -> None:
    # class 0 present once in 100 samples → naive pos_weight ~99. Cap should clamp.
    labels = np.zeros((100, 6), dtype=np.int32)
    labels[0, 0] = 1
    labels[:, 1] = 1  # class 1 always present → weight < 1, but clamped to 0.5 floor
    w = compute_pos_weight(labels, cap=5.0)
    assert w.shape == (6,)
    assert 0.5 <= float(w[0]) <= 5.0
    assert 0.5 <= float(w[1]) <= 5.0


def test_class_balanced_sampler_weights_rare_class_higher() -> None:
    from skin_training.data.dataset import AlignedSample

    def mk(idx: int, vec: list[int]) -> AlignedSample:
        return AlignedSample(
            case_id=str(idx),
            path=Path(f"/tmp/{idx}.npy"),
            label_vector=np.array(vec, dtype=np.float32),
            fitzpatrick=0,
        )

    # 99 samples of class 0, 1 sample of class 1. The rare sample should get much
    # higher weight than the common ones.
    samples = [mk(i, [1, 0]) for i in range(99)] + [mk(99, [0, 1])]
    sampler = class_balanced_sampler(samples)
    weights = sampler.weights.numpy()
    assert weights[99] > weights[0] * 5, f"rare sample weight {weights[99]} vs common {weights[0]}"


def test_evaluate_perfect_predictions() -> None:
    rng = np.random.default_rng(0)
    targets = rng.integers(0, 2, size=(50, 6)).astype(np.int32)
    # Probs slightly above 0.5 where target=1, slightly below where target=0
    probs = targets.astype(np.float32) * 0.8 + (1 - targets) * 0.2
    fp = rng.integers(1, 7, size=50)
    report = evaluate(probs, targets, fp)
    assert report.n_samples == 50
    assert len(report.overall) == 6
    # Every class perfectly separable
    for m in report.overall:
        if m.support > 0:
            assert m.precision == 1.0
            assert m.recall == 1.0
            assert m.f1 == 1.0


def test_onnx_export_roundtrip(tiny_model) -> None:
    import onnxruntime as ort

    tiny_model.eval()
    from skin_training.export.to_onnx import _ConditionOnlyExport

    wrapper = _ConditionOnlyExport(tiny_model).eval()
    x = torch.randn(1, 3, 112, 112)

    with tempfile.TemporaryDirectory() as td:
        onnx_path = Path(td) / "tiny.onnx"
        torch.onnx.export(
            wrapper, x, str(onnx_path),
            input_names=["image"], output_names=["probs"],
            opset_version=17,
            dynamic_axes={"image": {0: "batch"}, "probs": {0: "batch"}},
        )
        assert onnx_path.is_file()

        sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        onnx_out = sess.run(None, {"image": x.numpy()})[0]
        with torch.no_grad():
            torch_out = wrapper(x).numpy()
        assert np.allclose(onnx_out, torch_out, atol=1e-3), (
            f"max diff {abs(onnx_out - torch_out).max():.2e}"
        )
