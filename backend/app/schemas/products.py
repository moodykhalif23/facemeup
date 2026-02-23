from pydantic import BaseModel


class Product(BaseModel):
    sku: str
    name: str
    ingredients: list[str]
    stock: int
