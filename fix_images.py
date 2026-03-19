import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.product import ProductCatalog
from sqlalchemy import select
import random

random.seed(42)
db = SessionLocal()

seeds = db.execute(select(ProductCatalog).where(ProductCatalog.image_url == None)).scalars().all()
woo = db.execute(select(ProductCatalog).where(ProductCatalog.image_url != None)).scalars().all()

print(f"Seeds without image: {len(seeds)}, WooCommerce with image: {len(woo)}")

# Build keyword -> image pool
cat_pool = {}
for p in woo:
    for kw in ['serum','toner','cleanser','face wash','moisturizer','sunscreen','mask','cream','lotion','treatment','oil','gel','essence','eye','lip','body','scrub','powder']:
        if kw in p.name.lower() or kw in (p.category or '').lower():
            cat_pool.setdefault(kw, []).append(p.image_url)

brand_pool = {}
for p in woo:
    for brand in ['dr rashel','estelin','neutrogena','garnier','cerave','la roche','olay','aveeno','pond','vaseline']:
        if brand in p.name.lower():
            brand_pool.setdefault(brand, []).append(p.image_url)

updated = 0
for seed in seeds:
    name_lower = seed.name.lower()
    cat_lower = (seed.category or '').lower()
    chosen = None

    for brand, imgs in brand_pool.items():
        if brand in name_lower and imgs:
            chosen = random.choice(imgs)
            break

    if not chosen:
        for kw in ['serum','toner','face wash','cleanser','moisturizer','sunscreen','mask','cream','lotion','treatment','oil','gel','essence','eye','lip','body','scrub','powder']:
            if kw in name_lower or kw in cat_lower:
                pool = cat_pool.get(kw, [])
                if pool:
                    chosen = random.choice(pool)
                    break

    if not chosen and woo:
        chosen = random.choice(woo).image_url

    if chosen:
        seed.image_url = chosen
        updated += 1

db.commit()
db.close()
print(f"Updated {updated} products with matched images")
