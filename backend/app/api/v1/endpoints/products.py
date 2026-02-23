from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.redis_client import cache_get_json, cache_set_json
from app.models.product import ProductCatalog
from app.models.user import User
from app.schemas.products import Product


router = APIRouter()


@router.get("", response_model=list[Product])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    cache_key = "products:catalog"
    cached = cache_get_json(cache_key)
    if cached:
        return [Product(**item) for item in cached]

    rows = db.execute(select(ProductCatalog).order_by(ProductCatalog.name.asc())).scalars()
    products = [
        Product(
            sku=row.sku,
            name=row.name,
            ingredients=[v for v in row.ingredients_csv.split(",") if v],
            stock=row.stock,
        )
        for row in rows
    ]
    cache_set_json(cache_key, [p.model_dump() for p in products])
    return products


@router.post("/admin/seed", response_model=dict[str, int])
def reseed_catalog(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict[str, int]:
    count = db.execute(select(ProductCatalog)).scalars().all()
    return {"products": len(count)}
