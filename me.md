Proposed new architecture (PyTorch)
Stack:

API: FastAPI (keep — it's fine) + Pydantic v2
ML runtime: PyTorch 2.x + torchvision, ONNX Runtime for production inference
Face pipeline: insightface (RetinaFace + 5-point landmarks, battle-tested, CPU-capable at ~30ms)
Skin segmentation: Lightweight U-Net (MobileNetV3 encoder) — trainable from BiSeNet face-parsing weights
Classifier: EfficientNet-B0 (train) → MobileNetV3 (distill for deployment) — 6-head sigmoid
Explainability: pytorch-grad-cam library (maintained, supports all CNNs)
Serving: Export to ONNX, serve via ONNX Runtime with CUDA/CPU fallback — 10-50x faster than PyTorch eager on CPU
Preprocessing: OpenCV (CLAHE, LAB, white balance) — already C++ fast
DB: Keep PostgreSQL + existing Alembic migrations (don't break history)
Queue: Keep Redis, add Celery/Arq for async inference if needed
Storage: MinIO/S3-compatible for image retention (not base64 blobs in DB)

Phased plan
Phase	Scope	Deliverable	Est.
0	Scaffold new backend repo structure, keep old running in parallel	backend_v2/ alongside current, shared DB	0.5d
1	Preprocessing pipeline: face detect → align → CLAHE → segment → patches. Unit tested.	skin_pipeline/preprocess.py + tests	2d
2	Training infra: data loader (HAM10000/ISIC/SCIN), augmentations, trainer, logger	skin_pipeline/train.py — trainable but untrained	2d
3	Baseline model: EfficientNet-B0 multi-head on HAM10000 + fairness audit	Checkpoint + eval report	3d (training time)
4	ONNX export + Grad-CAM + inference service	POST /api/v1/analyze live with real model, <2s p95	2d
5	Port remaining 35 endpoints (auth, products, orders, loyalty, admin, sync) — these are CRUD, mechanical	Full contract parity	3d
6	Knowledge distillation → MobileNetV3 + INT8 quant	5MB model, <500ms CPU	2d
7	Cutover: shadow traffic → dual-run → switch	Old backend archived	1d