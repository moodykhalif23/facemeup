# ML Training Pipeline
## Keras EfficientNetB0 Fine-Tuning for Skin Analysis

This directory contains the machine learning training pipeline for the skin analysis model.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Prepare Dataset

```bash
# Download ISIC dataset
python ml/scripts/download_isic.py

# Export Bitmoji data (with consent)
python ml/scripts/export_bitmoji.py

# Prepare training data
python ml/data_loader.py --prepare
```

### 3. Train Model

```bash
# Phase 1: Feature Extraction (20 epochs)
python ml/train.py --config ml/config.yaml --phase 1

# Phase 2: Fine-Tuning (15 epochs)
python ml/train.py --config ml/config.yaml --phase 2
```

### 4. Evaluate Model

```bash
python ml/evaluate.py --model ml/models/best_model.h5
```

### 5. Export Models

```bash
# Export TFLite (quantized)
python ml/export_tflite.py --model ml/models/best_model.h5

# Export SavedModel
python ml/export_savedmodel.py --model ml/models/best_model.h5
```

## Directory Structure

```
ml/
├── config.yaml              # Training configuration
├── data_loader.py           # Dataset loading & preprocessing
├── model_builder.py         # EfficientNetB0 architecture
├── train.py                 # Main training script
├── evaluate.py              # Model evaluation
├── export_tflite.py         # TFLite conversion
├── export_savedmodel.py     # SavedModel export
├── bias_audit.py            # Fitzpatrick scale bias audit
├── data/                    # Training data
│   ├── isic/                # ISIC dataset
│   ├── bitmoji/             # Bitmoji exports
│   └── processed/           # Preprocessed data
├── models/                  # Trained models
│   ├── best_model.h5
│   └── checkpoints/
├── logs/                    # TensorBoard logs
└── scripts/                 # Utility scripts
    ├── download_isic.py
    ├── export_bitmoji.py
    └── visualize_data.py
```

## Training Strategy

### Phase 1: Feature Extraction (Weeks 1-2)
- Freeze all EfficientNetB0 base layers
- Train only custom classification head
- 20 epochs, learning rate 1e-3
- Early stopping patience: 5 epochs

### Phase 2: Fine-Tuning (Weeks 3-4)
- Unfreeze top 30 layers of EfficientNetB0
- Continue training with reduced learning rate
- 15 epochs, learning rate 1e-5
- Early stopping patience: 5 epochs

## Data Augmentation

- Random horizontal flip
- Random rotation (±20%)
- Random brightness adjustment (±20%)
- Random contrast adjustment (±20%)
- Random zoom (±10%)

## Model Architecture

```
Input (224x224x3)
    ↓
EfficientNetB0 (pre-trained on ImageNet)
    ↓
GlobalAveragePooling2D
    ↓
BatchNormalization
    ↓
Dense(256, relu)
    ↓
Dropout(0.4)
    ↓
Dense(10, softmax)  # 5 skin types + 5 conditions
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Accuracy | >75% |
| Precision | >70% |
| Recall | >70% |
| F1 Score | >70% |
| Model Size (TFLite) | <5MB |
| Inference Time (mobile) | <500ms |

## Bias Audit

The model is evaluated across Fitzpatrick skin tone scale (I-VI) to ensure fairness:

```bash
python ml/bias_audit.py --model ml/models/best_model.h5
```

## Benchmark vs Bitmoji

Compare model predictions against in-store Bitmoji analyzer:

```bash
python ml/benchmark_bitmoji.py --model ml/models/best_model.h5
```

Target: Cohen's Kappa > 0.7 (substantial agreement)

## TensorBoard

Monitor training progress:

```bash
tensorboard --logdir ml/logs
```

## Export Formats

### 1. TFLite (Mobile)
- Quantized to INT8
- Size: ~5MB
- Location: `app/models_artifacts/model.tflite`

### 2. SavedModel (Backend)
- Full precision
- Size: ~20MB
- Location: `app/models_artifacts/saved_model/`

### 3. ONNX (Optional)
- Cross-platform compatibility
- Location: `app/models_artifacts/model.onnx`

## Troubleshooting

### Out of Memory
- Reduce batch size in `config.yaml`
- Use mixed precision training
- Enable gradient checkpointing

### Low Accuracy
- Increase training epochs
- Adjust learning rate
- Add more data augmentation
- Check data quality

### Model Too Large
- Use INT8 quantization
- Prune unnecessary layers
- Use smaller base model (MobileNetV2)

## Next Steps

1. ✅ Train model (Weeks 1-4)
2. ✅ Export TFLite (<5MB)
3. ✅ Deploy to backend
4. ✅ Integrate with React Native
5. ✅ Validate on real users

## References

- EfficientNet: https://arxiv.org/abs/1905.11946
- TensorFlow Lite: https://www.tensorflow.org/lite
- ISIC Archive: https://www.isic-archive.com/
- Fitzpatrick Scale: https://en.wikipedia.org/wiki/Fitzpatrick_scale
