import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .onnx_runner import OnnxRegistry
from .pipeline import SkinPipeline
from .pipeline.classify import ONNXClassifier, placeholder_classify
from .pipeline.groq_provider import GroqProvider
from .pipeline.heatmaps import generate_heatmaps
from .pipeline.quality import assess_all, has_blocking
from .pipeline.runner import NoFaceFoundError
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    HeatmapPayload,
    QualityWarning,
)

log = logging.getLogger("ml_service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# ---------------------------------------------------------------------------
# Inference provider priority:
#   1. Groq Llama-Vision  (if ML_GROQ_API_KEY is set)
#   2. ONNX classifier    (if skin_classifier_mobilenet.onnx exists)
#   3. Placeholder        (always available)
#
# Active threshold is 0.30 — anything ≥ 0.30 is reported as an active condition.
# This was 0.50 before; the change calibrates Groq's score scale to the Bitmoji
# device's "level > 2 of 5 = concerning" cut. See pipeline/groq_provider.py.
# ---------------------------------------------------------------------------

ACTIVE_CONDITION_THRESHOLD = 0.30


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


app = FastAPI(title="Skincare ML Service", version="0.2.0", lifespan=lifespan)


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
    region_patches: list[tuple] = []
    quality_issues: list = []
    try:
        pipeline_result = pipeline.run(
            req.image_base64,
            client_landmarks=[lm.model_dump() for lm in req.landmarks] if req.landmarks else None,
        )
        aligned_bgr = pipeline_result.normalized
        # Region patches feed Groq's multi-image call. Skin-mask coverage is
        # used as a cheap signal that the crop is mostly skin (not hair / eye).
        # Sorted by skin_ratio so the cap inside groq_provider keeps the most
        # informative crops if it has to drop any.
        region_patches = sorted(
            ((p.region, p.image, p.skin_ratio)
             for p in pipeline_result.patches
             if p.skin_ratio >= 0.25),
            key=lambda t: -t[2],
        )
        region_patches = [(name, img) for name, img, _ in region_patches]

        # Quality gates run on the aligned face so the checks are framing-
        # invariant (the alignment normalises pose / scale).
        bbox = pipeline_result.detection.bbox if pipeline_result.detection else None
        quality_issues = assess_all(aligned_bgr, face_bbox=bbox)
        if has_blocking(quality_issues):
            blocking_msgs = "; ".join(i.message for i in quality_issues if i.severity == "block")
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "image_quality_too_low",
                    "message": blocking_msgs,
                    "warnings": [
                        {"code": i.code, "severity": i.severity, "message": i.message}
                        for i in quality_issues
                    ],
                },
            )

    except NoFaceFoundError:
        # Groq handles this — it doesn't strictly need a detected face — but
        # we add a soft warning so the user knows we couldn't crop regions.
        if groq is None and classifier is None:
            raise HTTPException(
                status_code=422,
                detail="No face detected and no AI provider configured. "
                       "Set ML_GROQ_API_KEY to enable cloud inference.",
            )
        log.info("face detection failed — Groq will infer from original image, no region patches")
        from .pipeline.quality import QualityIssue
        quality_issues = [QualityIssue(
            code="face_not_detected",
            severity="warn",
            message=("Couldn't lock onto a face — results may be less accurate. "
                     "For best results, retake with your face centred and well-lit."),
        )]
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.exception("preprocessing pipeline error")
        raise HTTPException(status_code=500, detail=f"pipeline error: {e}") from e

    # --- Inference -----------------------------------------------------------
    heatmaps: list[HeatmapPayload] = []

    if groq is not None:
        try:
            clf = groq.analyze(
                aligned_bgr,
                req.image_base64,
                req.questionnaire,
                region_patches=region_patches or None,
            )
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

    active = [
        label for label, prob in clf.condition_scores.items()
        if prob >= ACTIVE_CONDITION_THRESHOLD
    ]

    quality_payload = [
        QualityWarning(code=i.code, severity=i.severity, message=i.message)
        for i in quality_issues
    ]

    return AnalyzeResponse(
        skin_type=clf.skin_type,
        skin_type_scores=clf.skin_type_scores,
        conditions=active,
        condition_scores=clf.condition_scores,
        confidence=clf.confidence,
        inference_mode=clf.inference_mode,
        heatmaps=heatmaps,
        quality_warnings=quality_payload,
    )
