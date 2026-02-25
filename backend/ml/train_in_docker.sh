#!/bin/bash
# Train skin analysis model inside Docker container

echo "=========================================="
echo "ML Model Training in Docker"
echo "=========================================="

# Check if container is running
if ! docker ps | grep -q skincare-api; then
    echo "Error: skincare-api container is not running"
    echo "Please start the container first: docker-compose up -d"
    exit 1
fi

echo ""
echo "Step 1: Download ISIC dataset (this may take 30-60 minutes)..."
docker exec -it skincare-api python ml/scripts/download_isic.py

echo ""
echo "Step 2: Phase 1 Training - Feature Extraction (1-2 hours)..."
docker exec -it skincare-api python ml/train.py --phase 1

echo ""
echo "Step 3: Phase 2 Training - Fine-Tuning (1-2 hours)..."
docker exec -it skincare-api python ml/train.py --phase 2

echo ""
echo "Step 4: Export SavedModel for backend..."
docker exec -it skincare-api python ml/export_savedmodel.py \
    --model ml/checkpoints/phase2_best_model.h5 \
    --output app/models_artifacts/saved_model

echo ""
echo "Step 5: Export TFLite for mobile..."
docker exec -it skincare-api python ml/export_tflite.py \
    --model ml/checkpoints/phase2_best_model.h5 \
    --output app/models_artifacts/model.tflite \
    --quantize int8

echo ""
echo "=========================================="
echo "Training Complete!"
echo "=========================================="
echo ""
echo "Model artifacts saved to:"
echo "  - backend/app/models_artifacts/saved_model/ (for backend)"
echo "  - backend/app/models_artifacts/model.tflite (for mobile)"
echo ""
echo "Next steps:"
echo "  1. Restart the API: docker-compose restart api"
echo "  2. Test the analysis endpoint"
echo "  3. Copy TFLite model to frontend/assets/"
