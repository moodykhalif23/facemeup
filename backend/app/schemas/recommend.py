from pydantic import BaseModel


class RecommendRequest(BaseModel):
    skin_type: str
    conditions: list[str]


class ProductRecommendation(BaseModel):
    id: str
    sku: str
    name: str
    price: float
    score: float
    matched_ingredients: list[str]


class RecommendResponse(BaseModel):
    products: list[ProductRecommendation]
