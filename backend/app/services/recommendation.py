from app.schemas.recommend import ProductRecommendation

INGREDIENT_MAP: dict[str, list[str]] = {
    "Oily": ["Niacinamide", "Salicylic Acid"],
    "Dry": ["Hyaluronic Acid", "Ceramides"],
    "Combination": ["Niacinamide", "Hyaluronic Acid"],
    "Normal": ["Vitamin C", "Glycerin"],
    "Sensitive": ["Panthenol", "Ceramides"],
    "Acne": ["Salicylic Acid", "Tea Tree"],
    "Hyperpigmentation": ["Vitamin C", "Alpha Arbutin"],
    "Uneven tone": ["Niacinamide", "Vitamin C"],
    "Dehydration": ["Hyaluronic Acid", "Glycerin"],
}

CATALOG = [
    {
        "sku": "DRR-ACN-001",
        "name": "Dr Rashel Salicylic Clear Serum",
        "ingredients": ["Salicylic Acid", "Niacinamide", "Tea Tree"],
    },
    {
        "sku": "EST-HYD-010",
        "name": "Estelin Deep Hydration Cream",
        "ingredients": ["Hyaluronic Acid", "Ceramides", "Glycerin"],
    },
    {
        "sku": "DRR-BRT-022",
        "name": "Dr Rashel Bright Tone Essence",
        "ingredients": ["Vitamin C", "Alpha Arbutin", "Niacinamide"],
    },
]


def recommend_products(skin_type: str, conditions: list[str]) -> list[ProductRecommendation]:
    desired = set(INGREDIENT_MAP.get(skin_type, []))
    for condition in conditions:
        desired.update(INGREDIENT_MAP.get(condition, []))

    scored: list[ProductRecommendation] = []
    for item in CATALOG:
        matched = sorted(desired.intersection(set(item["ingredients"])))
        if not matched:
            continue
        score = len(matched) / max(len(desired), 1)
        scored.append(
            ProductRecommendation(
                sku=item["sku"],
                name=item["name"],
                score=round(score, 4),
                matched_ingredients=matched,
            )
        )

    return sorted(scored, key=lambda x: x.score, reverse=True)
