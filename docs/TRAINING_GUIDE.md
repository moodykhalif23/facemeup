# ML Model Training Guide

## Problem Identified

The current model returns low confidence predictions (11%) with default values because it was trained on `_generate_dummy_data()` which creates random noise images with random labels. This is not a code issue - the infrastructure works correctly, but the model needs real training data.

## Solution: Train with Real Data

### Option 1: Quick Training (Recommended for Testing)

Train with improved synthetic data that mimics skin characteristics:

**Windows PowerShell:**
```powershell
# Run automated quick training script
.\backend\ml\quick_train_docker.ps1
```

**Linux/Mac:**
```bash
# Start Docker containers
docker-compose up -d

# Train Phase 1 (20 epochs, ~30 minutes)
docker exec -it skincare-api python ml/train.py --phase 1

# Train Phase 2 (15 epochs, ~30 minutes)
docker exec -it skincare-api python ml/train.py --phase 2

# Export models
docker exec -it skincare-api python ml/export_savedmodel.py \
    --model ml/checkpoints/phase2_best_model.h5 \
    --output app/models_artifacts/saved_model

# Restart API to load new model
docker-compose restart api
```

### Option 2: Full Training with ISIC Dataset (Production Quality)

Train with real dermatology images from ISIC dataset:

**Windows PowerShell:**
```powershell
# Run automated full training script
.\backend\ml\train_in_docker.ps1
```

**Linux/Mac:**
```bash
# Make script executable
chmod +x backend/ml/train_in_docker.sh

# Run full training pipeline
./backend/ml/train_in_docker.sh
```

**Manual Steps (if scripts don't work):**
```bash
# Start Docker containers
docker-compose up -d

# Download ISIC dataset (30-60 minutes, several GB)
docker exec -it skincare-api python ml/scripts/download_isic.py

# Train Phase 1 (1-2 hours)
docker exec -it skincare-api python ml/train.py --phase 1

# Train Phase 2 (1-2 hours)
docker exec -it skincare-api python ml/train.py --phase 2

# Export models
docker exec -it skincare-api python ml/export_savedmodel.py \
    --model ml/checkpoints/phase2_best_model.h5 \
    --output app/models_artifacts/saved_model

docker exec -it skincare-api python ml/export_tflite.py \
    --model ml/checkpoints/phase2_best_model.h5 \
    --output app/models_artifacts/model.tflite \
    --quantize int8

# Restart API
docker-compose restart api
```

## What Changed

### 1. Deleted Dummy Model
- Removed `backend/app/models_artifacts/saved_model/` (trained on noise)
- Removed `backend/ml/checkpoints/quick_model.h5` (trained on noise)

### 2. Improved Data Loader
Updated `backend/ml/data_loader.py`:
- Now attempts to load real ISIC dataset from TensorFlow Datasets
- Falls back to local ISIC directory if available
- Improved synthetic data generation (skin-tone colors instead of random noise)
- Synthetic labels based on image characteristics (brightness, variance, redness)

### 3. Training Infrastructure
- All training runs inside Docker container
- Models automatically saved to `backend/app/models_artifacts/`
- Volume mounting ensures models persist after container restart

## Monitor Training

### View Training Progress

```bash
# View logs in real-time
docker logs -f skincare-api

# Check training metrics
docker exec -it skincare-api cat ml/checkpoints/phase1_training.csv
docker exec -it skincare-api cat ml/checkpoints/phase2_training.csv
```

### TensorBoard (Optional)

```bash
# Start TensorBoard
docker exec -d skincare-api tensorboard --logdir ml/logs --host 0.0.0.0 --port 6006

# Access at http://localhost:6006
```

## Expected Results

### With Improved Synthetic Data
- Confidence: 40-60%
- Predictions: More varied (not all "Normal")
- Training time: ~1 hour total

### With ISIC Dataset
- Confidence: 70-85%
- Predictions: Accurate skin type and condition detection
- Training time: 3-5 hours total

## Verify Model Works

```bash
# Test the analysis endpoint
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "BASE64_ENCODED_IMAGE",
    "landmarks": []
  }'
```

Expected response with trained model:
```json
{
  "skin_type": "Combination",
  "conditions": ["Dehydration", "Uneven tone"],
  "confidence": 0.78,
  "recommendations": [...]
}
```

## Troubleshooting

### Out of Memory
```yaml
# Reduce batch size in backend/ml/config.yaml
dataset:
  batch_size: 16  # Change from 32
```

### Training Too Slow
```yaml
# Reduce epochs for testing
training:
  phase1:
    epochs: 5  # Change from 20
  phase2:
    epochs: 3  # Change from 15
```

### ISIC Download Fails
The training will automatically use improved synthetic data. This is sufficient for testing but not production.

## Next Steps

1. Train the model using Option 1 or 2 above
2. Test predictions with real face images
3. If results are good, deploy to production
4. If results need improvement, consider:
   - Collecting more diverse training data
   - Adjusting model architecture
   - Fine-tuning hyperparameters
   - Adding more data augmentation
