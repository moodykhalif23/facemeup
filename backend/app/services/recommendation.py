"""Product recommendation: keyword/ingredient first-pass → Ollama re-ranking."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import ProductCatalog
from app.schemas.recommend import ProductRecommendation
from app.services.effects import CONDITION_EFFECT_MAP, split_effects_csv
from app.services.ollama_service import ollama_service

# Desired ingredients per skin type / condition
_INGREDIENT_MAP: dict[str, list[str]] = {
    "Oily":              ["Niacinamide", "Salicylic Acid", "Tea Tree", "Zinc", "Clay"],
    "Dry":               ["Hyaluronic Acid", "Ceramides", "Glycerin", "Shea Butter", "Squalane"],
    "Combination":       ["Niacinamide", "Hyaluronic Acid", "Glycerin", "Vitamin C"],
    "Normal":            ["Vitamin C", "Glycerin", "Hyaluronic Acid", "Niacinamide"],
    "Sensitive":         ["Panthenol", "Ceramides", "Aloe Vera", "Centella"],
    "Acne":              ["Salicylic Acid", "Tea Tree", "Niacinamide", "Benzoyl Peroxide", "Zinc"],
    "Hyperpigmentation": ["Vitamin C", "Alpha Arbutin", "Niacinamide", "Kojic Acid"],
    "Uneven tone":       ["Niacinamide", "Vitamin C", "Alpha Arbutin", "Glycolic Acid"],
    "Dehydration":       ["Hyaluronic Acid", "Glycerin", "Ceramides", "Squalane"],
    "Wrinkles":          ["Retinol", "Peptides", "Vitamin C", "Collagen"],
    "Redness":           ["Centella", "Niacinamide", "Aloe Vera", "Panthenol"],
}

_KEYWORD_MAP: dict[str, list[str]] = {
    "Oily":              ["oil control", "mattifying", "pore", "salicylic", "clay", "niacinamide"],
    "Dry":               ["hydrat", "moistur", "nourish", "hyaluronic", "ceramide", "dry skin"],
    "Combination":       ["balance", "hydrat", "niacinamide", "vitamin c"],
    "Normal":            ["vitamin c", "glow", "radiance"],
    "Sensitive":         ["gentle", "soothing", "calm", "sensitive", "centella"],
    "Acne":              ["acne", "blemish", "clear", "salicylic", "tea tree"],
    "Hyperpigmentation": ["bright", "whitening", "dark spot", "vitamin c", "arbutin"],
    "Uneven tone":       ["bright", "even tone", "radiance", "vitamin c"],
    "Dehydration":       ["hydrat", "moistur", "hyaluronic", "plump"],
    "Wrinkles":          ["anti-aging", "retinol", "wrinkle", "firm", "collagen"],
    "Redness":           ["soothing", "calm", "redness", "centella", "aloe"],
}


def recommend_products(
    skin_type: str,
    conditions: list[str],
    gender: str | None = None,
    age: int | None = None,
    db: Session = None,
) -> list[ProductRecommendation]:
    if db is None:
        db = next(get_db())

    products = db.execute(select(ProductCatalog)).scalars().all()
    if not products:
        return []

    # Build desired sets from skin type + conditions
    desired_ingredients: set[str] = set(_INGREDIENT_MAP.get(skin_type, []))
    desired_keywords: set[str] = set(_KEYWORD_MAP.get(skin_type, []))
    desired_effects: set[str] = set()
    for cond in conditions:
        if cond != "None detected":
            desired_ingredients.update(_INGREDIENT_MAP.get(cond, []))
            desired_keywords.update(_KEYWORD_MAP.get(cond, []))
            desired_effects.update(CONDITION_EFFECT_MAP.get(cond, []))

    # ── First pass: score all products, keep top 30 candidates ────────────────
    candidates: list[tuple[float, ProductCatalog]] = []
    for p in products:
        if gender and gender.lower() in ("male", "female"):
            if (p.suitable_for or "all").lower() not in ("all", gender.lower()):
                continue

        p_ingredients = [i.strip() for i in (p.ingredients_csv or "").split(",") if i.strip()]
        p_effects = split_effects_csv(p.effects_csv)
        text = f"{p.name} {p.category or ''} {p.description or ''}".lower()

        ing_hits = sum(1 for d in desired_ingredients if any(d.lower() in pi.lower() for pi in p_ingredients))
        kw_hits  = sum(1 for kw in desired_keywords if kw.lower() in text)
        eff_hits = sum(1 for e in desired_effects if e in p_effects)

        ing_score = ing_hits / max(len(desired_ingredients), 1)
        kw_score  = kw_hits  / max(len(desired_keywords), 1)
        eff_score = eff_hits / max(len(desired_effects), 1)
        score = kw_score * 0.6 + ing_score * 0.25 + eff_score * 0.15

        if age is not None:
            anti_age = {"anti wrinkle", "antifading", "collagen", "eye lines"}
            if age >= 30 and any(e in p_effects for e in anti_age):
                score += 0.05

        if score > 0.05:
            candidates.append((score, p))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top30 = candidates[:30]

    if not top30:
        return []

    # ── Ollama re-ranking ─────────────────────────────────────────────────────
    ollama_input = [
        {
            "sku": p.sku,
            "name": p.name,
            "ingredients": p.ingredients_csv or "",
            "effects": p.effects_csv or "",
        }
        for _, p in top30
    ]
    ranked_skus = ollama_service.rank_products(skin_type, conditions, ollama_input)

    # Build SKU → product map for fast lookup
    sku_map = {p.sku: p for _, p in top30}
    score_map = {p.sku: score for score, p in top30}

    results: list[ProductRecommendation] = []
    for sku in ranked_skus[:10]:
        p = sku_map.get(sku)
        if not p:
            continue
        p_ingredients = [i.strip() for i in (p.ingredients_csv or "").split(",") if i.strip()]
        matched = sorted({d for d in desired_ingredients if any(d.lower() in pi.lower() for pi in p_ingredients)})[:5]
        results.append(ProductRecommendation(
            id=p.sku,
            sku=p.sku,
            name=p.name,
            price=p.price or 0,
            score=round(score_map.get(sku, 0), 4),
            matched_ingredients=matched,
            image_url=p.image_url,
            category=p.category,
            effects=split_effects_csv(p.effects_csv),
        ))

    return results
