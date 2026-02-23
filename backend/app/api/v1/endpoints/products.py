from fastapi import APIRouter

from app.schemas.products import Product


router = APIRouter()


@router.get("", response_model=list[Product])
def list_products() -> list[Product]:
    return [
        Product(
            sku="DRR-ACN-001",
            name="Dr Rashel Salicylic Clear Serum",
            ingredients=["Salicylic Acid", "Niacinamide", "Tea Tree"],
            stock=24,
        ),
        Product(
            sku="EST-HYD-010",
            name="Estelin Deep Hydration Cream",
            ingredients=["Hyaluronic Acid", "Ceramides", "Glycerin"],
            stock=18,
        ),
    ]
