from fastapi import APIRouter

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.inference import run_skin_inference


router = APIRouter()


@router.post("", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    profile, mode = run_skin_inference(payload.image_base64)
    return AnalyzeResponse(profile=profile, inference_mode=mode)
