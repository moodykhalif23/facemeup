import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .onnx_runner import OnnxRegistry
from .pipeline import SkinPipeline
from .pipeline.classify import ONNXClassifier, placeholder_classify
from .pipeline.heatmaps import generate_heatmaps
from .pipeline.runner import NoFaceFoundError
from .schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, HeatmapPayload

log = logging.getLogger("ml_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("ml_service starting env=%s providers=%s", settings.env, settings.onnx_providers)

    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    app.state.registry = registry
    app.state.pipeline = SkinPipeline(settings, registry)

    # Eagerly attempt classifier load so we log once at startup whether heatmaps are available.
    classifier_session = registry.get(settings.classifier_model)
    if classifier_session is not None:
        app.state.classifier = ONNXClassifier(classifier_session, settings.conditions)
        log.info("classifier ONNX loaded: %s", settings.classifier_model)
    else:
        app.state.classifier = None
        log.warning("no classifier ONNX — falling back to placeholder, heatmaps disabled")

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
    classifier: ONNXClassifier | None = app.state.classifier

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

    heatmaps: list[HeatmapPayload] = []
    if classifier is not None and tensor.size > 0:
        try:
            clf = classifier.classify(tensor, settings.skin_types, req.questionnaire)
            raw_probs = _raw_probs_for_heatmap(classifier, tensor)
            hm_results = generate_heatmaps(
                session=classifier._session,
                input_name=classifier._input_name,
                output_name=classifier._output_name,
                patches_imagenet=tensor,
                patches_raw=[p.image for p in result.patches],
                patch_regions=[p.region for p in result.patches],
                condition_names=settings.conditions,
                baseline_probs=raw_probs,
            )
            heatmaps = [HeatmapPayload(label=h.label, image_base64=h.image_base64) for h in hm_results]
        except Exception as e:
            # Fail heatmaps soft — better to ship the analysis without them than 500.
            log.exception("heatmap generation failed: %s", e)
            clf = classifier.classify(tensor, settings.skin_types, req.questionnaire)
    else:
        clf = placeholder_classify(tensor, settings.skin_types, settings.conditions, req.questionnaire)

    active = [label for label, prob in clf.condition_scores.items() if prob >= 0.5]

    return AnalyzeResponse(
        skin_type=clf.skin_type,
        skin_type_scores=clf.skin_type_scores,
        conditions=active,
        condition_scores=clf.condition_scores,
        confidence=clf.confidence,
        inference_mode=clf.inference_mode,
        heatmaps=heatmaps,
    )


def _raw_probs_for_heatmap(classifier: ONNXClassifier, tensor):
    """Run the classifier once more to get per-patch probabilities for heatmap targeting.

    Kept separate so we don't pollute `ONNXClassifier.classify()`'s return type.
    """
    return classifier._session.run(
        [classifier._output_name], {classifier._input_name: tensor}
    )[0]
