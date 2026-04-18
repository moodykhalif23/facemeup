"""Export a trained checkpoint to ONNX and verify a numerical roundtrip.

After this runs successfully, copy the `.onnx` output into
`../ml_service/models/skin_classifier_mobilenet.onnx` and rebuild the sidecar.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from ..config import Config
from ..models.classifier import build_model

log = logging.getLogger("export")


def export(
    checkpoint: Path,
    output: Path,
    config_yaml: Path,
    image_size: int = 224,
    opset: int = 17,
    tolerance: float = 1e-3,
) -> None:
    cfg = Config.from_yaml(config_yaml)
    model = build_model(
        cfg.model.backbone, pretrained=False, embed_dim=cfg.model.embed_dim,
        dropout=cfg.model.dropout, n_conditions=cfg.model.n_conditions,
        n_skin_types=cfg.model.n_skin_types,
        skin_type_head_enabled=cfg.model.skin_type_head_enabled,
    )
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(payload["model"])
    model.eval()

    # The condition head is the production-critical one. To keep the exported
    # graph minimal for ONNX Runtime, we wrap the model so it returns a single
    # sigmoid tensor — matches what ml_service will consume.
    wrapper = _ConditionOnlyExport(model)
    wrapper.eval()

    dummy = torch.randn(1, 3, image_size, image_size)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Use dynamo-friendly dynamic_shapes (preferred in torch>=2.5).
    batch_dim = torch.export.Dim("batch", min=1, max=128)
    torch.onnx.export(
        wrapper,
        (dummy,),
        str(output),
        input_names=["image"],
        output_names=["condition_probs"],
        opset_version=opset,
        dynamic_shapes={"x": {0: batch_dim}},
    )
    log.info("wrote %s", output)

    # --- numerical roundtrip check --------------------------------------------
    sess = ort.InferenceSession(str(output), providers=["CPUExecutionProvider"])
    onnx_out = sess.run(None, {"image": dummy.numpy()})[0]
    with torch.no_grad():
        torch_out = wrapper(dummy).numpy()
    diff = float(np.abs(onnx_out - torch_out).max())
    log.info("onnx/torch max abs diff = %.2e (tol=%.2e)", diff, tolerance)
    if diff > tolerance:
        raise RuntimeError(f"ONNX export diverges from PyTorch by {diff:.2e}")


class _ConditionOnlyExport(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.model(x)
        return torch.sigmoid(out.logits_conditions)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export checkpoint → ONNX")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--opset", type=int, default=17)
    parser.add_argument("--tolerance", type=float, default=1e-3)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    export(args.checkpoint, args.output, args.config, args.image_size, args.opset, args.tolerance)


if __name__ == "__main__":
    main()
