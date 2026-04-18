"""PyTorch Dataset over precomputed aligned faces.

The precompute step freezes geometry (alignment, CLAHE); training augmentations
are pixel-level only — applying RandomCrop/Rotate after alignment would defeat
the purpose of the canonical template.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision.transforms import v2 as T

from .labels import Fitzpatrick


@dataclass(frozen=True)
class AlignedSample:
    case_id: str
    path: Path
    label_vector: np.ndarray        # shape (n_conditions,) float32 in {0,1}
    fitzpatrick: int                # 0 = unknown, 1..6


class AlignedFaceDataset(Dataset):
    def __init__(
        self,
        aligned_root: Path,
        samples: list[AlignedSample],
        image_size: int,
        train: bool,
    ):
        self._root = aligned_root
        self._samples = samples
        self._image_size = image_size
        self._train = train
        self._transform = _build_transforms(image_size, train)

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int):
        s = self._samples[idx]
        bgr = np.load(s.path)  # (H, W, 3) uint8 BGR
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb).permute(2, 0, 1)  # (3, H, W) uint8
        tensor = self._transform(tensor)
        return {
            "image": tensor,
            "labels": torch.from_numpy(s.label_vector).float(),
            "fitzpatrick": torch.tensor(s.fitzpatrick, dtype=torch.long),
        }


def _build_transforms(image_size: int, train: bool):
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std = [0.229, 0.224, 0.225]

    if train:
        # Pixel-level only; geometry is frozen by alignment.
        return T.Compose([
            T.RandomHorizontalFlip(p=0.5),
            T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10, hue=0.02),
            T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
            T.RandomResizedCrop(image_size, scale=(0.9, 1.0), ratio=(0.95, 1.05), antialias=True),
            T.ToDtype(torch.float32, scale=True),
            T.Normalize(mean=imagenet_mean, std=imagenet_std),
            T.RandomErasing(p=0.15, scale=(0.02, 0.10)),
        ])
    return T.Compose([
        T.Resize(image_size, antialias=True),
        T.CenterCrop(image_size),
        T.ToDtype(torch.float32, scale=True),
        T.Normalize(mean=imagenet_mean, std=imagenet_std),
    ])


def load_samples(labels_csv: Path, aligned_dir: Path) -> list[AlignedSample]:
    """Read labels.csv produced by precompute.py into AlignedSample rows."""
    samples: list[AlignedSample] = []
    with labels_csv.open(encoding="utf8") as f:
        reader = csv.DictReader(f)
        cond_cols = [c for c in reader.fieldnames or [] if c.startswith("c")]
        for row in reader:
            case_id = row["case_id"]
            path = aligned_dir / f"{case_id}.npy"
            if not path.is_file():
                continue
            try:
                fp = int(row.get("fitzpatrick", "0") or 0)
            except ValueError:
                fp = 0
            vec = np.array([int(row[c]) for c in cond_cols], dtype=np.float32)
            samples.append(AlignedSample(case_id=case_id, path=path, label_vector=vec, fitzpatrick=fp))
    return samples


def stratified_split(
    samples: list[AlignedSample],
    val_split: float,
    test_split: float,
    seed: int = 42,
) -> tuple[list[AlignedSample], list[AlignedSample], list[AlignedSample]]:
    """Split stratified by Fitzpatrick bucket so every bucket appears in train/val/test.

    For samples with unknown Fitzpatrick (bucket 0) we use random split.
    """
    rng = np.random.default_rng(seed)
    by_bucket: dict[int, list[AlignedSample]] = {}
    for s in samples:
        by_bucket.setdefault(s.fitzpatrick, []).append(s)

    train, val, test = [], [], []
    for bucket, items in by_bucket.items():
        idx = np.arange(len(items))
        rng.shuffle(idx)
        n_test = max(1, int(round(len(items) * test_split))) if len(items) > 1 else 0
        n_val = max(1, int(round(len(items) * val_split))) if len(items) > 1 else 0
        test.extend(items[i] for i in idx[:n_test])
        val.extend(items[i] for i in idx[n_test:n_test + n_val])
        train.extend(items[i] for i in idx[n_test + n_val:])
    return train, val, test


__all__ = ["AlignedFaceDataset", "AlignedSample", "load_samples", "stratified_split"]
_ = Fitzpatrick  # silence unused-import check; re-exported by data package
