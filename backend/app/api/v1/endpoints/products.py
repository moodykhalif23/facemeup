from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.core.redis_client import cache_get_json, cache_set_json
from app.models.product import ProductCatalog
from app.models.user import User
from app.schemas.products import Product, ProductDetail


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
            id=row.sku,
            sku=row.sku,
            name=row.name,
            price=row.price,
            ingredients=[v for v in row.ingredients_csv.split(",") if v],
            stock=row.stock,
            image_url=row.image_url,
            category=row.category
        )
        for row in rows
    ]
    cache_set_json(cache_key, [p.model_dump() for p in products])
    return products


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: str, db: Session = Depends(get_db)) -> ProductDetail:
    """Get detailed product information by ID (SKU)"""
    cache_key = f"products:detail:{product_id}"
    cached = cache_get_json(cache_key)
    if cached:
        return ProductDetail(**cached)
    
    row = db.execute(
        select(ProductCatalog).where(ProductCatalog.sku == product_id)
    ).scalar_one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Derive benefits from ingredients in the product
    ingredient_benefits = {
        "Salicylic Acid": "Unclogs pores and reduces acne",
        "Niacinamide": "Minimizes pores and controls oil",
        "Hyaluronic Acid": "Deeply hydrates and plumps skin",
        "Retinol": "Reduces fine lines and firms skin",
        "Vitamin C": "Brightens skin and fades dark spots",
        "Ceramides": "Restores and strengthens skin barrier",
        "Glycolic Acid": "Exfoliates and improves texture",
        "Tea Tree": "Targets blemishes and bacteria",
        "Peptides": "Boosts collagen and firms skin",
        "Alpha Arbutin": "Fades dark spots and evens tone",
        "Kojic Acid": "Lightens hyperpigmentation",
        "Centella": "Soothes and calms irritated skin",
        "Shea Butter": "Deeply nourishes and moisturizes",
        "Zinc": "Controls sebum and reduces inflammation",
        "Aloe Vera": "Soothes and hydrates sensitive skin",
    }
    ingredients_list = [v.strip() for v in row.ingredients_csv.split(",") if v.strip()]
    benefits = [ingredient_benefits[i] for i in ingredients_list if i in ingredient_benefits][:4]
    if not benefits:
        benefits = [f"Formulated with {ingredients_list[0]}" if ingredients_list else "Premium skincare formula"]

    product = ProductDetail(
        id=row.sku,
        sku=row.sku,
        name=row.name,
        price=row.price,
        category=row.category or "Skincare",
        description=row.description or f"Premium skincare product: {row.name}",
        benefits=benefits,
        ingredients=", ".join(ingredients_list),
        usage="Apply twice daily to clean, dry skin. Gently massage until fully absorbed.",
        stock=row.stock,
        image_url=row.image_url
    )
    
    cache_set_json(cache_key, product.model_dump())
    return product


@router.post("/admin/seed", response_model=dict[str, int])
def reseed_catalog(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict[str, int]:
    from sqlalchemy import delete
    from app.services.bootstrap import DEFAULT_PRODUCTS
    from app.core.redis_client import get_redis_client

    db.execute(delete(ProductCatalog))
    db.commit()
    try:
        get_redis_client().delete("products:catalog")
    except Exception:
        pass

    db.add_all(DEFAULT_PRODUCTS)
    db.commit()

    count = db.execute(select(ProductCatalog)).scalars().all()
    return {"products": len(count)}
