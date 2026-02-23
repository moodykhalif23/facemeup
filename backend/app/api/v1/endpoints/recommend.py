from fastapi import APIRouter

from app.schemas.recommend import RecommendRequest, RecommendResponse
from app.services.recommendation import recommend_products


router = APIRouter()


@router.post("", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    products = recommend_products(payload.skin_type, payload.conditions)
    return RecommendResponse(products=products)
