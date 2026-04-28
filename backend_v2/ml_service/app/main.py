import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .onnx_runner import OnnxRegistry
from .pipeline import SkinPipeline
from .pipeline.classify import ONNXClassifier, placeholder_classify
from .pipeline.groq_provider import GroqProvider
from .pipeline.heatmaps import generate_heatmaps
from .pipeline.runner import NoFaceFoundError
from .schemas import AnalyzeRequest, AnalyzeResponse, HealthResponse, HeatmapPayload

log = logging.getLogger("ml_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# ---------------------------------------------------------------------------
# Inference provider priority:
#   1. Groq Llama-3.2-Vision   (if ML_GROQ_API_KEY is set)
#   2. ONNX classifier          (if skin_classifier_mobilenet.onnx exists)
#   3. Placeholder              (always available)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("ml_service starting env=%s", settings.env)

    # Preprocessing pipeline (face detect → align → CLAHE → patches)
    registry = OnnxRegistry(settings.models_dir, settings.onnx_providers)
    app.state.registry = registry
    app.state.pipeline = SkinPipeline(settings, registry)

    # Provider 1 — Groq
    if settings.groq_api_key:
        try:
            app.state.groq = GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                skin_types=settings.skin_types,
                conditions=settings.conditions,
            )
            log.info("Groq provider active: model=%s", settings.groq_model)
        except Exception as e:
            log.error("Groq provider init failed: %s — falling back", e)
            app.state.groq = None
    else:
        app.state.groq = None
        log.info("GROQ_API_KEY not set — Groq disabled")

    # Provider 2 — ONNX
    classifier_session = registry.get(settings.classifier_model)
    if classifier_session is not None:
        app.state.classifier = ONNXClassifier(classifier_session, settings.conditions)
        log.info("ONNX classifier loaded: %s", settings.classifier_model)
    else:
        app.state.classifier = None
        if app.state.groq is None:
            log.warning("no Groq key and no ONNX model — using placeholder")

    yield
    log.info("ml_service stopping")


app = FastAPI(title="Skincare ML Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    settings = get_settings()
    registry: OnnxRegistry = app.state.registry
    groq: GroqProvider | None = getattr(app.state, "groq", None)
    providers = []
    if groq:
        providers.append(f"groq:{settings.groq_model}")
    if app.state.classifier:
        providers.append("onnx")
    if not providers:
        providers.append("placeholder")
    return HealthResponse(
        status="ok",
        models_loaded=bool(groq or app.state.classifier),
        providers=providers,
    )


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    settings = get_settings()
    pipeline: SkinPipeline = app.state.pipeline
    groq: GroqProvider | None = getattr(app.state, "groq", None)
    classifier: ONNXClassifier | None = app.state.classifier

    # --- Try preprocessing pipeline (face detect → align → patches) ----------
    pipeline_result = None
    aligned_bgr = None
    try:
        pipeline_result = pipeline.run(
            req.image_base64,
            client_landmarks=[lm.model_dump() for lm in req.landmarks] if req.landmarks else None,
        )
        aligned_bgr = pipeline_result.normalized   # CLAHE-normalised aligned face
    except NoFaceFoundError:
        # Groq handles this — it doesn't need a detected face.
        if groq is None and classifier is None:
            raise HTTPException(
                status_code=422,
                detail="No face detected and no AI provider configured. "
                       "Set ML_GROQ_API_KEY to enable cloud inference.",
            )
        log.info("face detection failed — Groq/placeholder will infer from original image")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.exception("preprocessing pipeline error")
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}") from e

    # --- Inference -----------------------------------------------------------
    heatmaps: list[HeatmapPayload] = []

    if groq is not None:
        # Groq works on aligned face (if available) OR original image.
        try:
            clf = groq.analyze(aligned_bgr, req.image_base64, req.questionnaire)
        except Exception as e:
            log.error("Groq inference failed: %s — falling through to ONNX/placeholder", e)
            clf = None
    else:
        clf = None

    if clf is None and classifier is not None and pipeline_result is not None:
        tensor = pipeline.build_classifier_batch(pipeline_result.patches)
        if tensor.size > 0:
            try:
                clf = classifier.classify(tensor, settings.skin_types, req.questionnaire)
                raw_probs = classifier._session.run(
                    [classifier._output_name], {classifier._input_name: tensor}
                )[0]
                hm_results = generate_heatmaps(
                    session=classifier._session,
                    input_name=classifier._input_name,
                    output_name=classifier._output_name,
                    patches_imagenet=tensor,
                    patches_raw=[p.image for p in pipeline_result.patches],
                    patch_regions=[p.region for p in pipeline_result.patches],
                    condition_names=settings.conditions,
                    baseline_probs=raw_probs,
                )
                heatmaps = [HeatmapPayload(label=h.label, image_base64=h.image_base64)
                            for h in hm_results]
            except Exception as e:
                log.exception("ONNX inference/heatmap error: %s", e)
                clf = classifier.classify(tensor, settings.skin_types, req.questionnaire)

    if clf is None:
        tensor = (pipeline.build_classifier_batch(pipeline_result.patches)
                  if pipeline_result else __import__("numpy").empty((0, 3, 1, 1), dtype="float32"))
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
