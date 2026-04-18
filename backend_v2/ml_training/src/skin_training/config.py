"""YAML-backed configuration dataclasses.

Loads once at the start of training and is passed everywhere read-only. Using a
dataclass (vs. plain dict) catches typos at import time and gives IDE autocomplete.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DataConfig:
    aligned_dir: Path            # precomputed aligned faces + label tensors
    val_split: float = 0.1
    test_split: float = 0.1
    num_workers: int = 4
    pin_memory: bool = True
    image_size: int = 224


@dataclass(frozen=True)
class ModelConfig:
    backbone: str = "efficientnet_b0"   # timm model name; also "mobilenetv3_small_100"
    pretrained: bool = True
    dropout: float = 0.4
    embed_dim: int = 256
    n_conditions: int = 6
    n_skin_types: int = 5
    skin_type_head_enabled: bool = False   # enable once we collect skin-type labels


@dataclass(frozen=True)
class TrainConfig:
    epochs: int = 25
    batch_size: int = 32
    lr: float = 1e-3
    weight_decay: float = 1e-4
    lr_schedule: str = "cosine"            # "cosine" | "step" | "none"
    warmup_epochs: int = 2
    label_smoothing: float = 0.0
    grad_clip: float | None = 1.0
    mixed_precision: bool = True
    checkpoint_dir: Path = field(default_factory=lambda: Path("runs/exp"))
    log_every: int = 20
    save_every_epochs: int = 5
    early_stop_patience: int | None = 6
    seed: int = 42


@dataclass(frozen=True)
class LossConfig:
    pos_weight_cap: float = 5.0        # cap on per-class BCE positive weighting
    skin_type_weight: float = 0.3      # balance skin-type CE vs. condition BCE


@dataclass(frozen=True)
class Config:
    data: DataConfig
    model: ModelConfig
    train: TrainConfig
    loss: LossConfig

    @staticmethod
    def from_yaml(path: str | Path) -> Config:
        with open(path, encoding="utf8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)

        return Config(
            data=DataConfig(**_coerce_paths(raw.get("data", {}), ["aligned_dir"])),
            model=ModelConfig(**raw.get("model", {})),
            train=TrainConfig(**_coerce_paths(raw.get("train", {}), ["checkpoint_dir"])),
            loss=LossConfig(**raw.get("loss", {})),
        )


def _coerce_paths(d: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    out = dict(d)
    for k in keys:
        if k in out and not isinstance(out[k], Path):
            out[k] = Path(out[k])
    return out
