from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import ProductCatalog
from app.schemas.recommend import ProductRecommendation
from app.services.effects import CONDITION_EFFECT_MAP, split_effects_csv

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

# Keywords to match in product names/descriptions for each skin type/condition
KEYWORD_MAP: dict[str, list[str]] = {
    # Skin Types
    "Oily": ["oil control", "mattifying", "pore", "salicylic", "clay", "charcoal", "niacinamide"],
    "Dry": ["hydrat", "moistur", "nourish", "hyaluronic", "ceramide", "shea butter", "dry skin"],
    "Combination": ["balance", "hydrat", "niacinamide", "vitamin c"],
    "Normal": ["vitamin c", "glow", "radiance", "maintain"],
    "Sensitive": ["gentle", "soothing", "calm", "sensitive", "aloe", "centella"],
    
    # Conditions
    "Acne": ["acne", "blemish", "clear", "salicylic", "tea tree", "pimple"],
    "Hyperpigmentation": ["bright", "whitening", "pigment", "dark spot", "vitamin c", "arbutin"],
    "Uneven tone": ["bright", "even", "tone", "radiance", "vitamin c", "niacinamide"],
    "Dehydration": ["hydrat", "moistur", "hyaluronic", "water", "plump"],
    "Fine lines": ["anti-aging", "retinol", "wrinkle", "firm", "peptide"],
    "Wrinkles": ["anti-aging", "retinol", "wrinkle", "firm", "collagen"],
    "Dark spots": ["bright", "whitening", "dark spot", "pigment", "vitamin c"],
    "Redness": ["soothing", "calm", "redness", "sensitive", "centella"],
}

def recommend_products(
    skin_type: str,
    conditions: list[str],
    gender: str | None = None,
    age: int | None = None,
    db: Session = None,
) -> list[ProductRecommendation]:
    """
    Recommend products from database based on skin type and conditions
    Uses both ingredient matching and keyword matching in product names/descriptions
    
    Args:
        skin_type: User's skin type
        conditions: List of skin conditions
        db: Database session (optional, will create if not provided)
        
    Returns:
        List of recommended products sorted by relevance score
    """
    # Get desired ingredients and keywords
    desired_ingredients = set(INGREDIENT_MAP.get(skin_type, []))
    desired_keywords = set(KEYWORD_MAP.get(skin_type, []))
    
    for condition in conditions:
        if condition != "None detected":
            desired_ingredients.update(INGREDIENT_MAP.get(condition, []))
            desired_keywords.update(KEYWORD_MAP.get(condition, []))
    
    desired_effects: set[str] = set()
    for condition in conditions:
        if condition != "None detected":
            desired_effects.update(CONDITION_EFFECT_MAP.get(condition, []))
    
    # If no specific criteria, use general skincare
    if not desired_ingredients and not desired_keywords:
        desired_ingredients = {"Hyaluronic Acid", "Vitamin C", "Niacinamide", "Glycerin"}
        desired_keywords = {"hydrat", "moistur", "vitamin", "serum"}
    
    # Get database session if not provided
    if db is None:
        db = next(get_db())
    
    # Fetch all products from database
    products = db.execute(select(ProductCatalog)).scalars().all()
    
    if not products:
        return []
    
    scored: list[ProductRecommendation] = []
    
    for product in products:
        # Filter by suitable_for if provided
        if gender and gender.lower() in ("male", "female"):
            product_gender = (product.suitable_for or "all").lower()
            if product_gender not in ("all", gender.lower()):
                continue

        # Parse ingredients from CSV
        product_ingredients = [ing.strip() for ing in product.ingredients_csv.split(",") if ing.strip()]
        product_effects = split_effects_csv(product.effects_csv)
        
        # Combine product name, category, and description for keyword matching
        searchable_text = f"{product.name} {product.category or ''} {product.description or ''}".lower()
        
        # Find matching ingredients (case-insensitive)
        matched_ingredients = []
        for desired_ing in desired_ingredients:
            for product_ing in product_ingredients:
                if desired_ing.lower() in product_ing.lower():
                    matched_ingredients.append(desired_ing)
                    break
        
        # Find matching keywords in product name/description
        matched_keywords = []
        for keyword in desired_keywords:
            if keyword.lower() in searchable_text:
                matched_keywords.append(keyword)

        # Match effects to conditions
        matched_effects = []
        for desired_eff in desired_effects:
            if desired_eff in product_effects:
                matched_effects.append(desired_eff)
        
        # Calculate score based on ingredient, keyword, and effects matches
        ingredient_score = len(matched_ingredients) / max(len(desired_ingredients), 1) if desired_ingredients else 0
        keyword_score = len(matched_keywords) / max(len(desired_keywords), 1) if desired_keywords else 0
        effect_score = len(matched_effects) / max(len(desired_effects), 1) if desired_effects else 0
        
        # Weighted average: keywords are more reliable for our data
        total_score = (keyword_score * 0.6) + (ingredient_score * 0.25) + (effect_score * 0.15)

        # Small age-based boost for anti-aging effects
        if age is not None and product_effects:
            if age >= 30 and any(eff in product_effects for eff in ["anti wrinkle", "antifading", "collagen", "eye lines"]):
                total_score += 0.05
            if age < 20 and any(eff in product_effects for eff in ["anti wrinkle", "antifading", "collagen"]):
                total_score -= 0.03
        
        # Only include products with some relevance
        if total_score > 0.1:
            scored.append(
                ProductRecommendation(
                    id=product.sku,
                    sku=product.sku,
                    name=product.name,
                    price=product.price or 0,
                    score=round(total_score, 4),
                    matched_ingredients=sorted(set(matched_ingredients + matched_keywords + matched_effects))[:5],
                    image_url=product.image_url,
                    category=product.category,
                    effects=product_effects,
                )
            )
    
    # Sort by score (highest first) and return top recommendations
    return sorted(scored, key=lambda x: x.score, reverse=True)[:20]
