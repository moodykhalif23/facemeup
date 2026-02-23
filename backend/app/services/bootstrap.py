from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import ProductCatalog

DEFAULT_PRODUCTS = [
    ProductCatalog(
        sku="DRR-ACN-001",
        name="Dr Rashel Salicylic Clear Serum",
        ingredients_csv="Salicylic Acid,Niacinamide,Tea Tree",
        stock=24,
    ),
    ProductCatalog(
        sku="EST-HYD-010",
        name="Estelin Deep Hydration Cream",
        ingredients_csv="Hyaluronic Acid,Ceramides,Glycerin",
        stock=18,
    ),
]


def seed_products(db: Session) -> None:
    existing = db.execute(select(ProductCatalog.sku)).first()
    if existing:
        return
    db.add_all(DEFAULT_PRODUCTS)
    db.commit()
