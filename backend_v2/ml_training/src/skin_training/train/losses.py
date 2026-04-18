"""Combined loss for multi-head classification.

- Conditions: BCEWithLogitsLoss with per-class positive weights (handles class
  imbalance at the loss level in addition to the sampler).
- Skin type: CrossEntropyLoss with optional label smoothing. Only applied if
  the head and labels are both present.

The BCE pos_weight is clamped to avoid extreme values for classes that appear
only once — otherwise a single positive example can dominate the gradient.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class LossBreakdown:
    total: torch.Tensor
    conditions: torch.Tensor
    skin_type: torch.Tensor | None


class MultiHeadLoss(nn.Module):
    def __init__(
        self,
        pos_weight: torch.Tensor,            # (n_conditions,)
        skin_type_weight: float = 0.3,
        label_smoothing: float = 0.0,
    ):
        super().__init__()
        self.register_buffer("pos_weight", pos_weight)
        self.skin_type_weight = skin_type_weight
        self.label_smoothing = label_smoothing

    def forward(
        self,
        logits_conditions: torch.Tensor,
        target_conditions: torch.Tensor,
        logits_skin_type: torch.Tensor | None = None,
        target_skin_type: torch.Tensor | None = None,
    ) -> LossBreakdown:
        loss_c = F.binary_cross_entropy_with_logits(
            logits_conditions, target_conditions, pos_weight=self.pos_weight
        )

        loss_s: torch.Tensor | None = None
        if logits_skin_type is not None and target_skin_type is not None:
            loss_s = F.cross_entropy(
                logits_skin_type, target_skin_type, label_smoothing=self.label_smoothing
            )

        total = loss_c + (self.skin_type_weight * loss_s if loss_s is not None else 0.0)
        return LossBreakdown(total=total, conditions=loss_c, skin_type=loss_s)


def compute_pos_weight(label_matrix: np.ndarray, cap: float = 5.0) -> torch.Tensor:
    """Per-class BCE positive weight = (#neg / #pos), capped.

    `label_matrix` shape: (N, n_conditions), values 0/1.
    """
    positives = label_matrix.sum(axis=0).astype(np.float64)
    negatives = label_matrix.shape[0] - positives
    weight = np.where(positives > 0, negatives / np.maximum(positives, 1e-6), 1.0)
    weight = np.clip(weight, 0.5, cap)
    return torch.tensor(weight, dtype=torch.float32)
