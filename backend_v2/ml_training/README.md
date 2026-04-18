# ml_training

PyTorch training code for the skin analysis pipeline. Runs in Colab/Kaggle
(or any GPU box) — **not** deployed to production.

Outputs: ONNX artifacts copied into `../ml_service/models/`.

## Planned scripts (Phase 2–3)

| Path                          | Purpose                                                       |
|-------------------------------|---------------------------------------------------------------|
| `src/data/scin.py`            | SCIN dataset loader + Fitzpatrick labels                      |
| `src/data/augment.py`         | Torchvision v2 transforms (CLAHE via cv2, flips, color jitter)|
| `src/data/preprocess.py`      | Face detect → align → CLAHE → segment → patch extract         |
| `src/models/classifier.py`    | EfficientNet-B0 / MobileNetV3 multi-head (6 condition sigmoid)|
| `src/train/train.py`          | Multi-label BCE trainer with class-balanced sampling          |
| `src/train/distill.py`        | Knowledge distillation: EfficientNet → MobileNetV3            |
| `src/eval/fairness.py`        | Per-Fitzpatrick precision/recall/F1 audit                     |
| `src/eval/gradcam_viz.py`     | Sanity-check Grad-CAM overlays on validation set              |
| `src/export/to_onnx.py`       | Export + verify ONNX roundtrip (MobileNet, U-Net, RetinaFace) |
| `configs/base.yaml`           | Hyperparams, paths, Fitzpatrick stratification                |

## Data sources

- **SCIN** (Google, ~10k real phone photos, CC-BY-4.0) — primary
- **Small labeled bootstrap** (~500 internal Dr Rashel user photos with consent)

## Usage (Colab-ready)

```python
!pip install -e ".[train]"

from ml_training.src.train.train import train_multilabel
train_multilabel(config="configs/base.yaml")
```

Checkpoint → ONNX export → drop into `ml_service/models/` → rebuild sidecar.
