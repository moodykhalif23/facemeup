# ML Training Guide for Skincare AI

## Current Status

✅ **Quick Model Trained** - A basic model with dummy data is working
✅ **Inference Pipeline** - Backend can now process images and return predictions
✅ **SavedModel Exported** - Model is deployed and ready to use

## For Production: Train with Real Data

### Option 1: Quick Production Model (Recommended - 30 minutes)

Use the improved quick training with more realistic synthetic data:

```bash
# Train with better synthetic data (500 samples, 10 epochs)
docker exec skincare-api python ml/quick_train.py

# Restart backend
docker-compose restart api
```

This gives you a working model immediately for testing and demo purposes.

### Option 2: HAM10000 Dataset (2-3 hours)

Real dermatoscopic images from Harvard Dataverse:

```bash
# Download HAM10000 dataset (~2GB, 10,000 images)
docker exec skincare-api python ml/scripts/download_skin_dataset.py

# Train Phase 1 (1-2 hours)
docker exec skincare-api python ml/train.py --phase 1

# Train Phase 2 (1 hour)
docker exec skincare-api python ml/train.py --phase 2 --model ml/checkpoints/phase1_best_model.h5

# Export to SavedModel
docker exec skincare-api python ml/export_savedmodel.py \
  --model ml/checkpoints/phase2_best_model.h5 \
  --output app/models_artifacts/saved_model

# Restart backend
docker-compose restart api
```

### Option 3: Custom Dataset

If you have your own skin images:

1. **Organize your data:**
```
ml/data/custom/
├── train/
│   ├── oily/
│   ├── dry/
│   ├── combination/
│   ├── normal/
│   └── sensitive/
├── val/
└── test/
```

2. **Update data_loader.py** to load from your custom directory

3. **Train:**
```bash
docker exec skincare-api python ml/train.py --phase 1
docker exec skincare-api python ml/train.py --phase 2
```

## Model Performance Targets

| Metric | Current (Dummy) | Target (Real Data) |
|--------|----------------|-------------------|
| Accuracy | ~10% | >75% |
| Precision | N/A | >70% |
| Recall | N/A | >70% |
| F1 Score | N/A | >70% |
| Inference Time | <500ms | <500ms |

## Monitoring Training

### TensorBoard:
```bash
docker exec -d skincare-api tensorboard --logdir ml/logs --host 0.0.0.0 --port 6006
```
Access at: http://localhost:6006

### Check Logs:
```bash
# Training logs
docker exec skincare-api cat ml/checkpoints/phase1_training.csv

# Model checkpoints
docker exec skincare-api ls -lh ml/checkpoints/
```

## Testing the Model

### Test Analysis Endpoint:
```bash
# Take a photo and analyze
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "BASE64_ENCODED_IMAGE",
    "questionnaire": {}
  }'
```

### Expected Response:
```json
{
  "profile": {
    "skin_type": "Combination",
    "conditions": ["Acne", "Dehydration"],
    "confidence": 0.85
  },
  "inference_mode": "server_savedmodel"
}
```

## Troubleshooting

### Model Not Loading:
```bash
# Check if model exists
docker exec skincare-api ls -la app/models_artifacts/saved_model/

# Check backend logs
docker logs skincare-api --tail 50
```

### Low Accuracy:
- Train with more epochs
- Use real dataset (HAM10000)
- Increase model complexity
- Add more data augmentation

### Out of Memory:
- Reduce batch size in config.yaml
- Use smaller model (MobileNetV2)
- Train on machine with more RAM

## Next Steps

1. ✅ **Current**: Basic model working with dummy data
2. ✅ **Complete**: MediaPipe Face Mesh integration for real-time capture (see MEDIAPIPE_INTEGRATION.md)
3. 🔄 **Recommended**: Train with HAM10000 for better accuracy
4. 🔄 **Future**: Collect real user data for fine-tuning
5. 🔄 **Future**: A/B test different model architectures

## Resources

- **MediaPipe Integration Guide**: See `docs/MEDIAPIPE_INTEGRATION.md` for complete documentation
- **HAM10000 Dataset**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/DBW86T
- **TensorFlow Lite**: https://www.tensorflow.org/lite
- **EfficientNet Paper**: https://arxiv.org/abs/1905.11946

---

**Current Status**: ✅ Model is trained and working. MediaPipe Face Mesh integration complete. Recommendations are being generated from real Dr. Rashel products!

For production deployment, train with HAM10000 dataset for better accuracy.
