# ML Training Pipeline - Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- TensorFlow & Keras
- TensorFlow Datasets
- scikit-learn
- matplotlib & seaborn
- PyYAML

### 2. Verify Installation

```bash
python -c "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"
python -c "import keras; print(f'Keras {keras.__version__}')"
```

Expected output:
```
TensorFlow 2.16.x
Keras 3.x.x
```

### 3. Check GPU (Optional)

```bash
python -c "import tensorflow as tf; print(f'GPUs: {tf.config.list_physical_devices(\"GPU\")}')"
```

If no GPU, training will use CPU (slower but works fine for testing).

---

## Training (2-4 hours)

### Option A: Quick Test with Dummy Data (5 minutes)

```bash
cd backend

# Phase 1: Feature Extraction (will use dummy data)
python ml/train.py --phase 1

# Phase 2: Fine-Tuning
python ml/train.py --phase 2
```

This uses automatically generated dummy data for testing the pipeline.

### Option B: Full Training with ISIC Dataset (2-4 hours)

```bash
cd backend

# Step 1: Download ISIC dataset (may take 30-60 minutes)
python ml/scripts/download_isic.py

# Step 2: Phase 1 Training (1-2 hours)
python ml/train.py --phase 1

# Step 3: Phase 2 Training (1-2 hours)
python ml/train.py --phase 2
```

---

## Monitor Training

### TensorBoard

```bash
cd backend
tensorboard --logdir ml/logs
```

Open: http://localhost:6006

View:
- Training/validation loss
- Accuracy, precision, recall
- Learning rate changes
- Model graph

### Training Logs

```bash
# View Phase 1 logs
cat ml/checkpoints/phase1_training.csv

# View Phase 2 logs
cat ml/checkpoints/phase2_training.csv
```

---

## Evaluate Model

```bash
cd backend

# Evaluate Phase 2 model
python ml/evaluate.py --model ml/checkpoints/phase2_best_model.h5
```

Output:
- Overall metrics (accuracy, precision, recall, F1)
- Per-class metrics
- Confusion matrix
- Validation against targets

---

## Export Models

### 1. Export to TFLite (for mobile)

```bash
cd backend

# With INT8 quantization (recommended, <5MB)
python ml/export_tflite.py \
  --model ml/checkpoints/phase2_best_model.h5 \
  --output app/models_artifacts/model.tflite \
  --quantize int8
```

### 2. Export to SavedModel (for backend)

```bash
cd backend

python ml/export_savedmodel.py \
  --model ml/checkpoints/phase2_best_model.h5 \
  --output app/models_artifacts/saved_model
```

### 3. Copy TFLite to Frontend

```bash
# Windows
copy backend\app\models_artifacts\model.tflite frontend\assets\model.tflite

# Mac/Linux
cp backend/app/models_artifacts/model.tflite frontend/assets/model.tflite
```

## Troubleshooting

### Out of Memory

```bash
# Reduce batch size in config.yaml
dataset:
  batch_size: 16  # Change from 32 to 16
```

### Training Too Slow

```bash
# Reduce epochs for testing
training:
  phase1:
    epochs: 5  # Change from 20 to 5
  phase2:
    epochs: 3  # Change from 15 to 3
```

### ISIC Download Fails

The training script will automatically use dummy data if ISIC is not available. This is fine for testing the pipeline.

### Model Too Large

```bash
# Use INT8 quantization
python ml/export_tflite.py \
  --model ml/checkpoints/phase2_best_model.h5 \
  --quantize int8
```

---

## Configuration

Edit `ml/config.yaml` to customize:

### Model
- `input_size`: Image size (default: 224)
- `skin_types`: Output classes for skin types
- `conditions`: Output classes for conditions

### Training
- `epochs`: Number of training epochs
- `learning_rate`: Learning rate
- `batch_size`: Batch size

### Data Augmentation
- `random_flip`: Horizontal flip
- `random_rotation`: Rotation range
- `random_brightness`: Brightness adjustment
- `random_contrast`: Contrast adjustment

---

## Next Steps

After training and exporting:

1. ✅ **Test Backend Inference**
   ```bash
   # Start backend
   cd backend
   uvicorn app.main:app --reload
   
   # Test analysis endpoint
   curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"image_base64": "..."}'
   ```

2. ✅ **Integrate with Frontend**
   - Copy TFLite model to `frontend/assets/`
   - Implement camera screen
   - Add TFLite inference
   - Test on device

3. ✅ **Validate Performance**
   - Test on real skin images
   - Compare with Bitmoji analyzer
   - Run bias audit
   - Collect user feedback

---

## Support

**Issues?**
- Check `ml/logs/` for training logs
- Review `ml/checkpoints/*.csv` for metrics
- Run TensorBoard for visualization
- Consult `backend/ml/README.md` for details

---

**Ready to train?** Start with Option A (dummy data) to test the pipeline, then move to Option B (ISIC dataset) for production training.
