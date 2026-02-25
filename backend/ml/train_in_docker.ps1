# Train skin analysis model inside Docker container (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ML Model Training in Docker" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if container is running
$containerRunning = docker ps --filter "name=skincare-api" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "Error: skincare-api container is not running" -ForegroundColor Red
    Write-Host "Please start the container first: docker-compose up -d"
    exit 1
}

Write-Host ""
Write-Host "Step 1: Download ISIC dataset (this may take 30-60 minutes)..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/scripts/download_isic.py

Write-Host ""
Write-Host "Step 2: Phase 1 Training - Feature Extraction (1-2 hours)..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/train.py --phase 1

Write-Host ""
Write-Host "Step 3: Phase 2 Training - Fine-Tuning (1-2 hours)..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/train.py --phase 2

Write-Host ""
Write-Host "Step 4: Export SavedModel for backend..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/export_savedmodel.py `
    --model ml/checkpoints/phase2_best_model.h5 `
    --output app/models_artifacts/saved_model

Write-Host ""
Write-Host "Step 5: Export TFLite for mobile..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/export_tflite.py `
    --model ml/checkpoints/phase2_best_model.h5 `
    --output app/models_artifacts/model.tflite `
    --quantize int8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Training Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Model artifacts saved to:"
Write-Host "  - backend/app/models_artifacts/saved_model/ (for backend)"
Write-Host "  - backend/app/models_artifacts/model.tflite (for mobile)"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart the API: docker-compose restart api"
Write-Host "  2. Test the analysis endpoint"
Write-Host "  3. Copy TFLite model to frontend/assets/"
