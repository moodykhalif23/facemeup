# ml_service

Python FastAPI sidecar that owns the heavy ML pipeline. The Go API calls this
service over HTTP (compose network, localhost) for `/v1/analyze`.

## Pipeline (Phase 1)

```
POST /v1/analyze
  ├─ decode base64 (EXIF-aware)
  ├─ face detection
  │     1. client-supplied MediaPipe FaceMesh landmarks (preferred)
  │     2. RetinaFace ONNX (Phase 4 — placeholder stub)
  │     3. OpenCV Haar cascade (last resort)
  ├─ 5-point similarity alignment → canonical 256×256 crop
  ├─ illumination normalization: grey-world WB + CLAHE on L channel
  ├─ skin segmentation
  │     • BiSeNet face-parsing ONNX (when model present)
  │     • YCrCb thresholding (fallback)
  ├─ patch extraction: forehead · L cheek · R cheek · nose · chin
  └─ classifier
        • Phase 1: placeholder (uniform sigmoid, biased by questionnaire hint)
        • Phase 4: MobileNetV3 multi-head ONNX (6-condition BCE sigmoid + 5-type softmax)
```

## Layout

```
ml_service/
├── app/
│   ├── main.py           # FastAPI app, /healthz, /v1/analyze
│   ├── config.py         # pydantic-settings (ML_* env vars)
│   ├── schemas.py        # request/response models
│   ├── onnx_runner.py    # lazy ONNX session registry
│   └── pipeline/
│       ├── decode.py     # base64 → ndarray + EXIF
│       ├── landmarks.py  # FiveePoint dataclass + MediaPipe/RetinaFace adapters
│       ├── detect.py     # face detection priority chain
│       ├── align.py      # ArcFace similarity warp
│       ├── normalize.py  # grey-world WB + CLAHE(L)
│       ├── segment.py    # BiSeNet + YCrCb fallback
│       ├── patches.py    # 5 canonical skin regions
│       ├── classify.py   # placeholder classifier
│       └── runner.py     # orchestrator
├── tests/                # pytest + synthetic face fixture
├── models/               # .onnx artefacts (gitignored)
├── scripts/download_models.py
└── Dockerfile
```

## Running locally (no Docker)

```bash
cd ml_service
python -m venv .venv
.venv\Scripts\activate     # or `source .venv/bin/activate`
pip install -e ".[dev]"

# Optional: pretrained ONNX artefacts (pipeline runs without them using fallbacks)
python scripts/download_models.py

uvicorn app.main:app --reload --port 8013
```

## Running tests

```bash
pytest                         # all tests
pytest tests/test_pipeline.py  # pipeline only
```

Tests use a synthetic face image (skin-toned oval) and client-supplied landmarks,
so they don't depend on any ONNX model being present on disk.

## Environment variables

All prefixed with `ML_`.

| Variable                | Default                              | Purpose                         |
|-------------------------|--------------------------------------|---------------------------------|
| `ML_ENV`                | `development`                        | Environment tag for logs        |
| `ML_PORT`               | `8000`                               | Uvicorn port                    |
| `ML_MODELS_DIR`         | `/app/models`                        | Where ONNX files live           |
| `ML_FACE_DETECTOR_MODEL`| `retinaface_mnet.onnx`               | RetinaFace filename             |
| `ML_SEGMENTER_MODEL`    | `face_parsing_bisenet.onnx`          | BiSeNet filename                |
| `ML_CLASSIFIER_MODEL`   | `skin_classifier_mobilenet.onnx`     | MobileNet classifier (Phase 4)  |
| `ML_INPUT_SIZE`         | `224`                                | Patch resolution                |
| `ML_ONNX_PROVIDERS`     | `("CPUExecutionProvider",)`          | ORT execution providers         |

## Phase 1 status

- ✅ Preprocessing pipeline end-to-end (decode → detect → align → normalize → segment → patches)
- ✅ `/v1/analyze` returns real patches + placeholder classifier output
- ✅ Disclaimer included per spec §12
- ✅ Unit tests with synthetic face pass without any model files
- ⏳ Real classifier — Phase 4
- ⏳ Grad-CAM heatmaps — Phase 4
