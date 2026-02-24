from pydantic import BaseModel


class Product(BaseModel):
    sku: str
    name: str
    ingredients: list[str]
    stock: int


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
