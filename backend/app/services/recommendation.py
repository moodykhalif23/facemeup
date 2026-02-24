from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import ProductCatalog
from app.schemas.recommend import ProductRecommendation

# Ingredient mapping for skin types and conditions
INGREDIENT_MAP: dict[str, list[str]] = {
    # Skin Types
    "Oily": ["Niacinamide", "Salicylic Acid", "Tea Tree", "Zinc", "Clay", "Charcoal"],
    "Dry": ["Hyaluronic Acid", "Ceramides", "Glycerin", "Shea Butter", "Squalane", "Vitamin E"],
    "Combination": ["Niacinamide", "Hyaluronic Acid", "Glycerin", "Vitamin C"],
    "Normal": ["Vitamin C", "Glycerin", "Hyaluronic Acid", "Niacinamide"],
    "Sensitive": ["Panthenol", "Ceramides", "Aloe Vera", "Centella", "Chamomile", "Oat"],
    
    # Conditions
    "Acne": ["Salicylic Acid", "Tea Tree", "Niacinamide", "Benzoyl Peroxide", "Zinc"],
    "Hyperpigmentation": ["Vitamin C", "Alpha Arbutin", "Niacinamide", "Kojic Acid", "Licorice"],
    "Uneven tone": ["Niacinamide", "Vitamin C", "Alpha Arbutin", "Glycolic Acid"],
    "Dehydration": ["Hyaluronic Acid", "Glycerin", "Ceramides", "Squalane"],
    "Fine lines": ["Retinol", "Peptides", "Vitamin C", "Hyaluronic Acid"],
    "Wrinkles": ["Retinol", "Peptides", "Vitamin C", "Collagen"],
    "Dark spots": ["Vitamin C", "Alpha Arbutin", "Kojic Acid", "Niacinamide"],
    "Redness": ["Centella", "Niacinamide", "Aloe Vera", "Green Tea"],
}


def recommend_products(skin_type: str, conditions: list[str], db: Session = None) -> list[ProductRecommendation]:
    """
    Recommend products from database based on skin type and conditions
    
    Args:
        skin_type: User's skin type
        conditions: List of skin conditions
        db: Database session (optional, will create if not provided)
        
    Returns:
        List of recommended products sorted by relevance score
    """
    # Get desired ingredients based on skin type and conditions
    desired = set(INGREDIENT_MAP.get(skin_type, []))
    for condition in conditions:
        if condition != "None detected":
            desired.update(INGREDIENT_MAP.get(condition, []))
    
    # If no specific ingredients needed, use general skincare ingredients
    if not desired:
        desired = {"Hyaluronic Acid", "Vitamin C", "Niacinamide", "Glycerin"}
    
    # Get database session if not provided
    if db is None:
        db = next(get_db())
    
    # Fetch all products from database
    products = db.execute(select(ProductCatalog)).scalars().all()
    
    if not products:
        # Return empty list if no products in database
        return []
    
    scored: list[ProductRecommendation] = []
    
    for product in products:
        # Parse ingredients from CSV
        product_ingredients = [ing.strip() for ing in product.ingredients_csv.split(",") if ing.strip()]
        
        # Find matching ingredients (case-insensitive)
        matched = []
        for desired_ing in desired:
            for product_ing in product_ingredients:
                if desired_ing.lower() in product_ing.lower():
                    matched.append(desired_ing)
                    break
        
        # Skip products with no matching ingredients
        if not matched:
            continue
        
        # Calculate relevance score
        score = len(matched) / max(len(desired), 1)
        
        scored.append(
            ProductRecommendation(
                id=product.sku,
                sku=product.sku,
                name=product.name,
                price=product.price or 29.99,
                score=round(score, 4),
                matched_ingredients=sorted(set(matched)),
            )
        )
    
    # Sort by score (highest first) and return top recommendations
    return sorted(scored, key=lambda x: x.score, reverse=True)[:20]
