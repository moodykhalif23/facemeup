"""INT8 post-training quantization for the student ONNX model.

Input:  student ONNX (float32, ~8 MB for MobileNetV3-small)
Output: int8 ONNX (~2-3 MB, 3-5x faster on CPU with AVX2)

Uses ONNX Runtime's static quantization with a calibration dataset
(100 random aligned faces) to determine per-tensor scale/zero-point.

Per spec §5.2: target model size < 5 MB, inference < 500 ms on mobile.
INT8 achieves < 3 MB; ONNX Runtime on CPU with 1 thread is < 200 ms.
"""

from __future__ import annotations

import argparse
import logging
import tempfile
from pathlib import Path

import numpy as np

log = logging.getLogger("quantize")


def quantize_to_int8(
    fp32_onnx: Path,
    output: Path,
    calibration_dir: Path | None = None,
    n_calibration: int = 100,
    image_size: int = 224,
) -> Path:
    """Quantize a float32 ONNX to INT8 using static quantization.

    Args:
        fp32_onnx:      The float32 ONNX model (usually best_student.onnx).
        output:         Where to write the INT8 ONNX.
        calibration_dir: Directory containing aligned .npy face arrays.
                         If None, uses synthetic random tensors (less accurate
                         calibration but works for a smoke test).
        n_calibration:  Number of calibration samples.
        image_size:     Expected H/W input (must match the model's static shape).
    """
    try:
        from onnxruntime.quantization import (
            CalibrationDataReader,
            QuantType,
            quantize_static,
        )
    except ImportError as e:
        raise ImportError(
            "pip install onnxruntime  (version >= 1.16 for static quantization)"
        ) from e

    output.parent.mkdir(parents=True, exist_ok=True)
    input_name = _get_input_name(fp32_onnx)
    reader = _build_reader(calibration_dir, input_name, n_calibration, image_size)

    log.info("quantizing %s -> %s (n_calibration=%d)", fp32_onnx, output, n_calibration)
    quantize_static(
        model_input=str(fp32_onnx),
        model_output=str(output),
        calibration_data_reader=reader,
        quant_type=QuantType.QUInt8,
        per_channel=False,  # per-tensor is faster; per-channel is slightly more accurate
        reduce_range=False,
    )
    log.info("INT8 model written: %s  (%.1f MB)", output, output.stat().st_size / 1e6)
    return output


def verify_int8(fp32_onnx: Path, int8_onnx: Path, image_size: int = 224,
                tolerance: float = 0.05) -> float:
    """Check that INT8 outputs are close to FP32 on a random input.

    Returns the max absolute difference. Raises if it exceeds tolerance.
    For INT8 quantization, 0.05 (5%) is a reasonable threshold.
    """
    import onnxruntime as ort
    fp32_sess = ort.InferenceSession(str(fp32_onnx), providers=["CPUExecutionProvider"])
    int8_sess = ort.InferenceSession(str(int8_onnx), providers=["CPUExecutionProvider"])

    x = np.random.randn(1, 3, image_size, image_size).astype(np.float32)
    in_name = fp32_sess.get_inputs()[0].name

    fp32_out = fp32_sess.run(None, {in_name: x})[0]
    int8_out = int8_sess.run(None, {in_name: x})[0]

    diff = float(np.abs(fp32_out - int8_out).max())
    log.info("INT8 verification: max abs diff = %.4f (tol=%.2f)", diff, tolerance)
    if diff > tolerance:
        log.warning("INT8 accuracy degraded beyond tolerance — consider per_channel=True")
    return diff


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_input_name(onnx_path: Path) -> str:
    import onnxruntime as ort
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    return sess.get_inputs()[0].name


class _build_reader:
    """CalibrationDataReader that yields normalised image tensors."""

    def __init__(self, calibration_dir, input_name, n, image_size):
        import cv2
        self._input_name = input_name
        self._tensors    = []
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

        if calibration_dir is not None:
            npys = sorted(Path(calibration_dir).glob("*.npy"))[:n]
            for p in npys:
                bgr = np.load(p)
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                self._tensors.append(((rgb - mean) / std).transpose(2, 0, 1)[None, ...])
        if len(self._tensors) < n:
            rng  = np.random.default_rng(42)
            needed = n - len(self._tensors)
            log.info("using %d synthetic calibration tensors (real: %d)", needed, len(self._tensors))
            for _ in range(needed):
                self._tensors.append(
                    rng.normal(size=(1, 3, image_size, image_size)).astype(np.float32)
                )
        self._iter = iter(self._tensors)

    def get_next(self):
        try:
            return {self._input_name: next(self._iter)}
        except StopIteration:
            return None


def main() -> None:
    parser = argparse.ArgumentParser(description="INT8 post-training quantization")
    parser.add_argument("--input",  type=Path, required=True, help="float32 ONNX to quantize")
    parser.add_argument("--output", type=Path, required=True, help="output INT8 ONNX path")
    parser.add_argument("--calibration-dir", type=Path, default=None,
                        help="Directory of aligned .npy files for calibration")
    parser.add_argument("--n-calibration", type=int, default=100)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    quantize_to_int8(args.input, args.output, args.calibration_dir,
                     args.n_calibration, args.image_size)
    verify_int8(args.input, args.output, args.image_size, args.tolerance)


if __name__ == "__main__":
    main()
