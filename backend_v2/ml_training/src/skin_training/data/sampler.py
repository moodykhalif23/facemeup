"""Class-balanced sampler for multi-label training.

Skin conditions are heavily long-tailed in SCIN (acne and rosacea dwarf
wrinkles). Uniform sampling under-represents rare classes. We sample with
weights inversely proportional to each sample's max class frequency — a
pragmatic middle ground between full class-balancing and uniform.
"""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import WeightedRandomSampler

from .dataset import AlignedSample


def class_balanced_sampler(
    samples: list[AlignedSample],
    num_samples: int | None = None,
    smoothing: float = 1.0,
) -> WeightedRandomSampler:
    """Return a WeightedRandomSampler with per-sample weights.

    `smoothing` shifts class frequencies away from 0 (smoothing=0 is unsafe for
    zero-count classes, which would produce div-by-zero weights).
    """
    n_classes = len(samples[0].label_vector)
    counts = np.full(n_classes, smoothing, dtype=np.float64)
    for s in samples:
        counts += s.label_vector

    # Per-class weight = 1 / frequency
    class_weights = counts.sum() / (counts * n_classes)

    per_sample = np.zeros(len(samples), dtype=np.float64)
    for i, s in enumerate(samples):
        active = s.label_vector.astype(bool)
        if not active.any():
            per_sample[i] = 1.0  # "no condition" samples still get baseline weight
            continue
        per_sample[i] = float(class_weights[active].max())

    per_sample = per_sample / per_sample.sum()
    return WeightedRandomSampler(
        weights=torch.as_tensor(per_sample, dtype=torch.double),
        num_samples=num_samples or len(samples),
        replacement=True,
    )
