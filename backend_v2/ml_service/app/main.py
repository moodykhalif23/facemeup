import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .onnx_runner import OnnxRegistry
from .pipeline import SkinPipeline
from .pipeline.classify import placeholder_classify
from .pipeline.runner import NoFaceFoundError
from .schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse

log = logging.getLogger("ml_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("ml_service starting env=%s providers=%s", settings.env, settings.onnx_providers)

    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    app.state.registry = registry
    app.state.pipeline = SkinPipeline(settings, registry)
    log.info("pipeline ready (models load lazily on first /v1/analyze)")
    yield
    log.info("ml_service stopping")


app = FastAPI(title="Skincare ML Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    settings = get_settings()
    registry: OnnxRegistry = app.state.registry
    return HealthResponse(
        status="ok",
        models_loaded=any(registry.loaded().values()),
        providers=list(settings.onnx_providers),
    )


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    settings = get_settings()
    pipeline: SkinPipeline = app.state.pipeline

    try:
        result = pipeline.run(
            req.image_base64,
            client_landmarks=[lm.model_dump() for lm in req.landmarks] if req.landmarks else None,
        )
    except NoFaceFoundError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.exception("pipeline failure")
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}") from e

    tensor = pipeline.build_classifier_batch(result.patches)
    clf = placeholder_classify(
        tensor, settings.skin_types, settings.conditions, req.questionnaire
    )

    active = [
        label for label, prob in clf.condition_scores.items() if prob >= 0.5
    ]

    return AnalyzeResponse(
        skin_type=clf.skin_type,
        skin_type_scores=clf.skin_type_scores,
        conditions=active,
        condition_scores=clf.condition_scores,
        confidence=clf.confidence,
        inference_mode=clf.inference_mode,
        heatmaps=[],
    )
