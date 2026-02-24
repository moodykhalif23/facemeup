#!/usr/bin/env python3
"""Sync products from WooCommerce to database"""

from app.core.database import SessionLocal
from app.models.product import ProductCatalog
from app.services.woocommerce_service import woocommerce_service

def sync_products():
    db = SessionLocal()
    
    try:
        print("Fetching products from WooCommerce...")
        wc_products = woocommerce_service.fetch_all_products()
        print(f"✓ Fetched {len(wc_products)} products from WooCommerce\n")
        
        products_added = 0
        products_updated = 0
        products_failed = 0
        
        for wc_product in wc_products:
            try:
                # Parse product data
                product_data = woocommerce_service.parse_product_for_db(wc_product)
                
                # Check if product exists
                existing_product = db.query(ProductCatalog).filter(
                    ProductCatalog.sku == product_data['sku']
                ).first()
                
                if existing_product:
                    # Update existing product
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    products_updated += 1
                else:
                    # Add new product
                    new_product = ProductCatalog(**product_data)
                    db.add(new_product)
                    products_added += 1
                    
                # Commit every 50 products to avoid memory issues
                if (products_added + products_updated) % 50 == 0:
                    db.commit()
                    print(f"Progress: {products_added + products_updated}/{len(wc_products)} products processed...")
                    
            except Exception as e:
                products_failed += 1
                print(f"Failed to sync product {wc_product.get('id')}: {e}")
                continue
        
        # Final commit
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Sync Complete!")
        print(f"{'='*60}")
        print(f"✓ Products added: {products_added}")
        print(f"✓ Products updated: {products_updated}")
        print(f"✗ Products failed: {products_failed}")
        print(f"Total synced: {products_added + products_updated}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    sync_products()
