from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import cache_get_json, cache_set_json
from app.models.user import User
from app.schemas.recommend import RecommendRequest, RecommendResponse
from app.services.recommendation import recommend_products


router = APIRouter()


@router.post("", response_model=RecommendResponse)
def recommend(
    payload: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendResponse:
    key = f"recommend:{current_user.id}:{payload.skin_type}:{','.join(sorted(payload.conditions))}"
    cached = cache_get_json(key)
    if cached:
        return RecommendResponse(products=cached)

    products = recommend_products(payload.skin_type, payload.conditions, db)
    cache_set_json(key, [p.model_dump() for p in products], ttl=300)  # Cache for 5 minutes
    return RecommendResponse(products=products)
