# ml_training

PyTorch training pipeline for the skincare multi-label skin-condition classifier.
Runs in Colab / Kaggle / any GPU box — **not** deployed to production. Output is
an ONNX file that drops into [`../ml_service/models/`](../ml_service/models/).

## Layout

```
ml_training/
├── pyproject.toml
├── configs/base.yaml                 # default hyperparameters
├── src/skin_training/
│   ├── config.py                     # typed YAML config loader
│   ├── data/
│   │   ├── labels.py                 # Condition enum + SCIN → 6-class mapping
│   │   ├── scin.py                   # SCIN CSV parser
│   │   ├── precompute.py             # runs ml_service pipeline → aligned .npy
│   │   ├── dataset.py                # PyTorch Dataset + pixel augmentations
│   │   └── sampler.py                # class-balanced multi-label sampler
│   ├── models/classifier.py          # EfficientNet-B0 / MobileNetV3 dual-head
│   ├── train/
│   │   ├── losses.py                 # weighted BCE + CE
│   │   └── loop.py                   # full training loop (AMP + TB + early stop)
│   ├── eval/metrics.py               # per-condition + Fitzpatrick stratified
│   └── export/to_onnx.py             # checkpoint → ONNX + numerical roundtrip
├── scripts/colab_quickstart.py       # Colab one-liner entry point
└── tests/                            # smoke tests
```

## Pipeline at a glance

```
SCIN (CSV + images)          ← download manually (DUA required)
      │
      ▼
skin-precompute              ← runs ml_service preprocessing
      │   — face detect + align + CLAHE + WB
      │   — saves aligned .npy + labels.csv
      ▼
skin-train                   ← EfficientNet-B0 + 6-way sigmoid head
      │   — BCE with pos_weight
      │   — class-balanced sampler
      │   — Fitzpatrick-stratified validation split
      │   — cosine LR, mixed precision, early stop
      ▼
skin-export                  ← ONNX opset-17 + roundtrip diff check
      │
      ▼
ml_service/models/skin_classifier_mobilenet.onnx
```

## Install

### Locally (inference dev only — no GPU)

```bash
cd backend_v2/ml_training
pip install -e "../ml_service"    # pipeline preprocessing
pip install -e ".[dev]"           # torch, timm, etc.
pytest -v                         # smoke tests
```

### Colab

```python
!git clone https://github.com/<your-org>/skincare.git
%cd skincare/backend_v2
!pip install -e ml_service
!pip install -e ml_training
!python ml_training/scripts/colab_quickstart.py \
    --scin-root /content/scin \
    --work-dir /content/work
```

## Data sources

- **SCIN** (Google, 10k+ consumer photos, Fitzpatrick I–VI, CC-BY-4.0 / DUA) —
  primary. Download from github.com/google-research-datasets/scin.
- **Small labeled bootstrap** — ~500 Dr Rashel user photos with consent.
  Match SCIN's schema (see `data/scin.py`) and point `--scin-root` at the
  merged folder.

## Label taxonomy

Spec §1 six macro conditions, used throughout frontend + API:

| idx | name                | SCIN mapping examples                                  |
|-----|---------------------|--------------------------------------------------------|
| 0   | Acne                | acne vulgaris, folliculitis, perioral dermatitis       |
| 1   | Dryness             | eczema, xerosis, atopic dermatitis, ichthyosis         |
| 2   | Oiliness            | seborrheic dermatitis, seborrhea                       |
| 3   | Hyperpigmentation   | melasma, PIH, solar lentigo, lentigines                |
| 4   | Wrinkles            | rhytides, photodamage, elastosis                       |
| 5   | Redness             | rosacea, telangiectasia, erythema                      |

Multi-label sigmoid (spec §6) — a single face can carry multiple labels.

## Training targets (spec §11)

| Metric             | Target  |
|--------------------|---------|
| Macro F1           | ≥ 0.70  |
| Per-condition AUC  | ≥ 0.75  |
| Fitzpatrick V/VI F1 within 0.10 of I/II F1 (fairness — spec §12)     |

## Phase 2 status

- ✅ Package scaffolded, installable, CLI entry points registered
- ✅ SCIN parser + 6-class mapping with Fitzpatrick stratification
- ✅ Precompute reuses ml_service preprocessing (single source of truth)
- ✅ Dual-head classifier (conditions always, skin-type gated by config)
- ✅ Weighted BCE + class-balanced sampler + per-condition + stratified metrics
- ✅ Full training loop (AMP, cosine LR, early stop, TensorBoard, resume)
- ✅ ONNX export with numerical roundtrip check
- ⏳ Phase 3: actual training run on SCIN in Colab → first checkpoint
- ⏳ Phase 4: wire that ONNX into ml_service `/v1/analyze`
