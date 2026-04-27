"""Smoke test: distillation + INT8 quantization on synthetic tensors.

Verifies the full Phase 6 pipeline end-to-end without requiring a real
teacher checkpoint or real data.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from skin_training.models.classifier import build_model
from skin_training.train.losses import compute_pos_weight


# ── tiny model fixtures ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tiny_teacher():
    return build_model("mobilenetv3_small_100", pretrained=False,
                       embed_dim=32, dropout=0.0, n_conditions=6,
                       n_skin_types=5, skin_type_head_enabled=False).eval()


@pytest.fixture(scope="module")
def tiny_student():
    return build_model("mobilenetv3_small_100", pretrained=False,
                       embed_dim=32, dropout=0.0, n_conditions=6,
                       n_skin_types=5, skin_type_head_enabled=False)


# ── distillation loss smoke ───────────────────────────────────────────────────

def test_distillation_loss_backward(tiny_teacher, tiny_student):
    """One distillation step: teacher soft targets + student hard loss."""
    import torch.nn.functional as F
    from skin_training.train.losses import MultiHeadLoss

    label_matrix = np.random.randint(0, 2, size=(16, 6)).astype(np.int32)
    pos_weight   = compute_pos_weight(label_matrix)
    hard_fn      = MultiHeadLoss(pos_weight=pos_weight)

    x = torch.randn(4, 3, 112, 112)
    y = torch.randint(0, 2, (4, 6)).float()

    temperature = 4.0
    alpha = 0.5

    tiny_teacher.eval()
    tiny_student.train()

    with torch.no_grad():
        t_out = tiny_teacher(x)
        soft_targets = torch.sigmoid(t_out.logits_conditions / temperature)

    s_out        = tiny_student(x)
    hard         = hard_fn(s_out.logits_conditions, y).total
    soft_student = torch.sigmoid(s_out.logits_conditions / temperature)
    soft         = F.mse_loss(soft_student, soft_targets) * (temperature ** 2)
    loss         = alpha * hard + (1.0 - alpha) * soft

    assert loss.item() > 0
    assert not torch.isnan(loss)
    loss.backward()
    # Verify gradients flow through the student
    for p in tiny_student.parameters():
        if p.grad is not None:
            assert not torch.isnan(p.grad).any()


# ── INT8 quantization smoke ────────────────────────────────────────────────────

def test_int8_quantization_roundtrip(tiny_student):
    """Export student to FP32 ONNX, quantize to INT8, verify outputs close."""
    try:
        from onnxruntime.quantization import QuantType, quantize_static
    except ImportError:
        pytest.skip("onnxruntime quantization not available")

    from skin_training.export.to_onnx import _ConditionOnlyExport
    from skin_training.export.quantize import _build_reader, _get_input_name, verify_int8

    tiny_student.eval()
    wrapper = _ConditionOnlyExport(tiny_student).eval()
    x = torch.randn(1, 3, 112, 112)

    with tempfile.TemporaryDirectory() as td:
        fp32_path = Path(td) / "student_fp32.onnx"
        int8_path = Path(td) / "student_int8.onnx"

        batch_dim = torch.export.Dim("batch", min=1, max=32)
        torch.onnx.export(
            wrapper, (x,), str(fp32_path),
            input_names=["image"], output_names=["condition_probs"],
            opset_version=17, dynamic_shapes={"x": {0: batch_dim}},
        )
        assert fp32_path.is_file()

        input_name = _get_input_name(fp32_path)
        reader = _build_reader(None, input_name, n=10, image_size=112)
        quantize_static(str(fp32_path), str(int8_path),
                        calibration_data_reader=reader, quant_type=QuantType.QUInt8)

        assert int8_path.is_file()
        # Size should be noticeably smaller
        ratio = int8_path.stat().st_size / fp32_path.stat().st_size
        assert ratio < 0.95, f"INT8 not smaller than FP32: ratio={ratio:.2f}"

        diff = verify_int8(fp32_path, int8_path, image_size=112, tolerance=0.15)
        assert diff < 0.15, f"INT8 accuracy too degraded: diff={diff:.4f}"
