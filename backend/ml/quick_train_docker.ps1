# Quick training with improved synthetic data (PowerShell)
# This is faster than downloading ISIC dataset - good for testing

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Quick ML Training (Synthetic Data)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "This will train with improved synthetic skin-like data"
Write-Host "Training time: ~1 hour total"
Write-Host ""

# Check if container is running
$containerRunning = docker ps --filter "name=skincare-api" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "Error: skincare-api container is not running" -ForegroundColor Red
    Write-Host "Starting containers..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 10
}

Write-Host "Step 1/4: Phase 1 Training (~30 minutes)..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/train.py --phase 1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Phase 1 training failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2/4: Phase 2 Training (~30 minutes)..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/train.py --phase 2

if ($LASTEXITCODE -ne 0) {
    Write-Host "Phase 2 training failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3/4: Export SavedModel..." -ForegroundColor Yellow
docker exec -it skincare-api python ml/export_savedmodel.py `
    --model ml/checkpoints/phase2_best_model.h5 `
    --output app/models_artifacts/saved_model

Write-Host ""
Write-Host "Step 4/4: Restart API to load new model..." -ForegroundColor Yellow
docker-compose restart api

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Training Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The model is now trained and loaded."
Write-Host "You can test it by making requests to the /api/v1/analyze endpoint"
Write-Host ""
Write-Host "Note: This model uses synthetic data for quick testing."
Write-Host "For production, train with real ISIC dataset using train_in_docker.ps1"
