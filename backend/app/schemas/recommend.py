from pydantic import BaseModel


class RecommendRequest(BaseModel):
    skin_type: str
    conditions: list[str]


class ProductRecommendation(BaseModel):
    sku: str
    name: str
    score: float
    matched_ingredients: list[str]


class RecommendResponse(BaseModel):
    products: list[ProductRecommendation]
