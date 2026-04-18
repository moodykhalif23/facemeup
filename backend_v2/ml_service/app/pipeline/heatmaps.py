"""Grad-CAM-style heatmaps for ONNX classifiers (spec §7).

True Grad-CAM needs gradients, which ONNX Runtime doesn't expose. We use a
**score-map approximation**: occlude regions of each patch and measure the
drop in per-condition probability. The result is the same visual intent
(heat where the model is looking) without requiring PyTorch at runtime.

For the small 224×224 patches and 6-class head, a 14×14 occlusion grid costs
~196 extra forward passes per heatmap — fast on CPU (<100ms total for a
mobilenet) and embarrassingly batched.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


@dataclass
class HeatmapResult:
    label: str
    image_base64: str


def generate_heatmaps(
    session,
    input_name: str,
    output_name: str,
    patches_imagenet: np.ndarray,     # (N, 3, H, W) normalised for the model
    patches_raw: list[np.ndarray],     # (N,) list of BGR uint8 for overlay
    patch_regions: list[str],
    condition_names: tuple[str, ...],
    baseline_probs: np.ndarray,        # (N, C) already-computed probs to save a call
    threshold: float = 0.5,
    grid: int = 14,
    blur_sigma: float = 4.0,
) -> list[HeatmapResult]:
    """Produce one overlay per (condition present above threshold, patch).

    Only conditions with at least one patch probability >= threshold are drawn —
    keeps the payload small and avoids confusing heatmaps of conditions the
    model didn't detect.
    """
    if patches_imagenet.ndim != 4:
        raise ValueError(f"expected 4-D batch, got {patches_imagenet.shape}")
    N, C, H, W = patches_imagenet.shape

    out: list[HeatmapResult] = []
    active_conditions = np.where(baseline_probs.max(axis=0) >= threshold)[0]
    if active_conditions.size == 0:
        return out

    for cond_idx in active_conditions:
        # Find the patch with the strongest signal for this condition
        best_patch = int(np.argmax(baseline_probs[:, cond_idx]))
        patch_imagenet = patches_imagenet[best_patch]
        patch_raw = patches_raw[best_patch]
        base_score = float(baseline_probs[best_patch, cond_idx])

        saliency = _occlusion_saliency(
            session, input_name, output_name,
            patch_imagenet, cond_idx, base_score, grid,
        )
        if blur_sigma > 0:
            ksize = max(3, int(blur_sigma * 2) | 1)
            saliency = cv2.GaussianBlur(saliency, (ksize, ksize), blur_sigma)
        saliency = _normalize_01(saliency)

        overlay = _render_overlay(patch_raw, saliency)
        label = f"{condition_names[cond_idx]} @ {patch_regions[best_patch]}"
        out.append(HeatmapResult(label=label, image_base64=_png_b64(overlay)))
    return out


def _occlusion_saliency(
    session,
    input_name: str,
    output_name: str,
    patch_imagenet: np.ndarray,   # (3, H, W) normalised
    cond_idx: int,
    base_score: float,
    grid: int,
) -> np.ndarray:
    """Measure probability drop when occluding grid×grid cells, one at a time.

    Batched: run all grid² masked variants in a single ONNX call.
    """
    C, H, W = patch_imagenet.shape
    cell_h = max(1, H // grid)
    cell_w = max(1, W // grid)

    variants = []
    coords = []
    for gy in range(grid):
        for gx in range(grid):
            y0 = gy * cell_h
            y1 = H if gy == grid - 1 else min(H, y0 + cell_h)
            x0 = gx * cell_w
            x1 = W if gx == grid - 1 else min(W, x0 + cell_w)
            v = patch_imagenet.copy()
            v[:, y0:y1, x0:x1] = 0.0   # ImageNet-normalised "grey" = channel mean
            variants.append(v)
            coords.append((y0, y1, x0, x1))

    batch = np.stack(variants, axis=0).astype(np.float32)
    probs = session.run([output_name], {input_name: batch})[0]  # (grid², n_conditions)
    drops = base_score - probs[:, cond_idx]  # positive where occlusion hurt the prediction

    saliency = np.zeros((H, W), dtype=np.float32)
    for (y0, y1, x0, x1), drop in zip(coords, drops):
        saliency[y0:y1, x0:x1] = max(saliency[y0:y1, x0:x1].max(), float(drop))
    return saliency


def _normalize_01(a: np.ndarray) -> np.ndarray:
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-6:
        return np.zeros_like(a, dtype=np.float32)
    return ((a - lo) / (hi - lo)).astype(np.float32)


def _render_overlay(patch_bgr: np.ndarray, saliency_01: np.ndarray) -> np.ndarray:
    """Return a BGR uint8 overlay: heatmap alpha-blended onto the patch."""
    h, w = patch_bgr.shape[:2]
    if saliency_01.shape != (h, w):
        saliency_01 = cv2.resize(saliency_01, (w, h), interpolation=cv2.INTER_LINEAR)
    heatmap = cv2.applyColorMap((saliency_01 * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return cv2.addWeighted(patch_bgr, 0.55, heatmap, 0.45, 0)


def _png_b64(bgr: np.ndarray) -> str:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    buf = BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")
