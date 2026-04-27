"""Generate a random-weights ONNX classifier stub for integration testing.

Lets us exercise the full `/v1/analyze` path (ONNX load, inference, Grad-CAM)
without waiting for the real Phase 3 training run.

The stub is a tiny 2-layer CNN with output shape (N, 7) after sigmoid — same
contract as the production model trained by ml_training/.

Usage:
    python scripts/build_stub_classifier.py
    # → writes models/skin_classifier_mobilenet.onnx (replace with real model later)

Requires onnx + numpy only (no PyTorch) so it runs in the runtime container.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

try:
    import onnx
    from onnx import TensorProto, helper, numpy_helper
except ImportError:
    print("ERROR: this script needs `pip install onnx`.", file=sys.stderr)
    sys.exit(1)


def build_stub(
    out_path: Path,
    n_conditions: int = 7,
    input_size: int = 224,
    seed: int = 0,
) -> Path:
    rng = np.random.default_rng(seed)

    # Conv1: 3 → 8, 3×3
    w1 = rng.normal(0, 0.1, size=(8, 3, 3, 3)).astype(np.float32)
    b1 = np.zeros(8, dtype=np.float32)
    # Conv2: 8 → 16, 3×3
    w2 = rng.normal(0, 0.1, size=(16, 8, 3, 3)).astype(np.float32)
    b2 = np.zeros(16, dtype=np.float32)
    # FC: 16 → n_conditions
    w_fc = rng.normal(0, 0.1, size=(n_conditions, 16)).astype(np.float32)
    b_fc = np.zeros(n_conditions, dtype=np.float32)

    image = helper.make_tensor_value_info("image", TensorProto.FLOAT, [None, 3, input_size, input_size])
    probs = helper.make_tensor_value_info("condition_probs", TensorProto.FLOAT, [None, n_conditions])

    inits = [
        numpy_helper.from_array(w1, "w1"),
        numpy_helper.from_array(b1, "b1"),
        numpy_helper.from_array(w2, "w2"),
        numpy_helper.from_array(b2, "b2"),
        numpy_helper.from_array(w_fc, "w_fc"),
        numpy_helper.from_array(b_fc, "b_fc"),
    ]

    nodes = [
        helper.make_node("Conv", ["image", "w1", "b1"], ["c1"], kernel_shape=[3, 3], pads=[1, 1, 1, 1]),
        helper.make_node("Relu", ["c1"], ["r1"]),
        helper.make_node("MaxPool", ["r1"], ["p1"], kernel_shape=[2, 2], strides=[2, 2]),
        helper.make_node("Conv", ["p1", "w2", "b2"], ["c2"], kernel_shape=[3, 3], pads=[1, 1, 1, 1]),
        helper.make_node("Relu", ["c2"], ["r2"]),
        helper.make_node("GlobalAveragePool", ["r2"], ["gap"]),
        helper.make_node("Flatten", ["gap"], ["flat"], axis=1),
        helper.make_node("Gemm", ["flat", "w_fc", "b_fc"], ["logits"], transB=1),
        helper.make_node("Sigmoid", ["logits"], ["condition_probs"]),
    ]

    graph = helper.make_graph(nodes, "stub_classifier", [image], [probs], initializer=inits)
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.checker.check_model(model)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a random-weights ONNX classifier stub")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent.parent / "models" / "skin_classifier_mobilenet.onnx")
    parser.add_argument("--input-size", type=int, default=224)
    parser.add_argument("--n-conditions", type=int, default=7)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    path = build_stub(args.output, args.n_conditions, args.input_size, args.seed)
    print(f"wrote stub classifier → {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
