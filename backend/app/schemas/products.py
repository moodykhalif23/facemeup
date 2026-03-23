from pydantic import BaseModel


class Product(BaseModel):
    id: str
    sku: str
    name: str
    price: float
    ingredients: list[str]
    stock: int
    image_url: str | None = None
    category: str | None = None
    suitable_for: str | None = None
    effects: list[str] = []
    wc_id: int | None = None


class ProductDetail(BaseModel):
    id: str
    sku: str
    name: str
    price: float
    category: str
    description: str
    benefits: list[str]
    ingredients: str
    usage: str
    stock: int
    image_url: str | None = None
    suitable_for: str | None = None
    effects: list[str] = []
    wc_id: int | None = None
