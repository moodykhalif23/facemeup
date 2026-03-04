# Clean progress view
docker exec skincare-api bash -c "grep -a 'STEP\|✓\|Epoch\|val_loss\|TRAINING COMPLETE' ml/training.log | tail -10"

# Raw download size
docker exec skincare-api bash -c "du -sh ml/data/ham10000/"
