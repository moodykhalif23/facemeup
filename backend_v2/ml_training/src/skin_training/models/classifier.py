"""Multi-head skin classifier.

- Backbone: any timm model (default EfficientNet-B0 per spec §5.1).
- Head A: 6-way sigmoid for conditions (multi-label — spec §6).
- Head B: 5-way softmax for skin type (optional; disabled until skin-type labels exist).

Both heads share a small dense bottleneck so they regularise each other.
"""

from __future__ import annotations

from dataclasses import dataclass

import timm
import torch
import torch.nn as nn


@dataclass(frozen=True)
class ClassifierOutputs:
    logits_conditions: torch.Tensor           # (B, n_conditions) raw logits (pre-sigmoid)
    logits_skin_type: torch.Tensor | None     # (B, n_skin_types) raw logits (pre-softmax), or None


class MultiHeadClassifier(nn.Module):
    def __init__(
        self,
        backbone: str = "efficientnet_b0",
        pretrained: bool = True,
        embed_dim: int = 256,
        dropout: float = 0.4,
        n_conditions: int = 6,
        n_skin_types: int = 5,
        skin_type_head_enabled: bool = False,
    ):
        super().__init__()
        # Feature extractor: timm with num_classes=0 returns pooled features.
        self.backbone = timm.create_model(backbone, pretrained=pretrained, num_classes=0, global_pool="avg")
        feat_dim = _probe_output_dim(self.backbone)

        self.bottleneck = nn.Sequential(
            nn.BatchNorm1d(feat_dim),
            nn.Linear(feat_dim, embed_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
        )
        self.head_conditions = nn.Linear(embed_dim, n_conditions)
        self.head_skin_type = nn.Linear(embed_dim, n_skin_types) if skin_type_head_enabled else None

    def forward(self, x: torch.Tensor) -> ClassifierOutputs:
        feats = self.backbone(x)
        z = self.bottleneck(feats)
        logits_c = self.head_conditions(z)
        logits_s = self.head_skin_type(z) if self.head_skin_type is not None else None
        return ClassifierOutputs(logits_conditions=logits_c, logits_skin_type=logits_s)

    @torch.no_grad()
    def predict_probs(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        out = self.forward(x)
        result = {"conditions": torch.sigmoid(out.logits_conditions)}
        if out.logits_skin_type is not None:
            result["skin_type"] = torch.softmax(out.logits_skin_type, dim=-1)
        return result


def _probe_output_dim(backbone: nn.Module) -> int:
    """Return the pooled feature dimension of a timm backbone.

    `backbone.num_features` is unreliable for models with a post-pool conv_head
    (notably MobileNetV3: reports 576, actually outputs 1024). A 1-sample dummy
    forward always gives the truth.
    """
    was_training = backbone.training
    backbone.eval()
    try:
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224)
            out = backbone(dummy)
    finally:
        backbone.train(was_training)
    if out.ndim != 2:
        raise RuntimeError(f"expected (B, C) features from backbone; got shape {tuple(out.shape)}")
    return int(out.shape[1])


def build_model(
    backbone: str,
    pretrained: bool,
    embed_dim: int,
    dropout: float,
    n_conditions: int,
    n_skin_types: int,
    skin_type_head_enabled: bool,
) -> MultiHeadClassifier:
    return MultiHeadClassifier(
        backbone=backbone,
        pretrained=pretrained,
        embed_dim=embed_dim,
        dropout=dropout,
        n_conditions=n_conditions,
        n_skin_types=n_skin_types,
        skin_type_head_enabled=skin_type_head_enabled,
    )
