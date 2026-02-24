from fastapi import APIRouter

from app.api.v1.endpoints import (
    analyze,
    auth,
    loyalty,
    orders,
    products,
    profile,
    proxy,
    recommend,
    sync,
)


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
api_router.include_router(recommend.router, prefix="/recommend", tags=["recommend"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(loyalty.router, prefix="/loyalty", tags=["loyalty"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
