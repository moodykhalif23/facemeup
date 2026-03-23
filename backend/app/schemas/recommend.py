from pydantic import BaseModel


class RecommendRequest(BaseModel):
    skin_type: str
    conditions: list[str]
    gender: str | None = None
    age: int | None = None


class ProductRecommendation(BaseModel):
    id: str
    sku: str
    name: str
    price: float
    score: float
    matched_ingredients: list[str]
    image_url: str | None = None
    category: str | None = None
    effects: list[str] = []


class RecommendResponse(BaseModel):
    products: list[ProductRecommendation]
