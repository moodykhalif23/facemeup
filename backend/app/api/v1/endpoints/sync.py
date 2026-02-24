from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.product import ProductCatalog
from app.models.user import User
from app.schemas.sync import BitmojiSyncRequest, BitmojiSyncResponse, WooCommerceSyncResponse
from app.services.profile_service import append_profile
from app.services.woocommerce_service import woocommerce_service


router = APIRouter()


@router.post("/bitmoji", response_model=BitmojiSyncResponse)
def sync_bitmoji(
    payload: BitmojiSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BitmojiSyncResponse:
    append_profile(db, current_user.id, payload.skin_type, payload.conditions, confidence=0.95)
    return BitmojiSyncResponse(synced=True)


@router.post("/woocommerce", response_model=WooCommerceSyncResponse)
def sync_woocommerce_products(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> WooCommerceSyncResponse:
    """
    Sync products from WooCommerce store (Dr. Rashel)
    Admin only endpoint
    """
    try:
        # Fetch all products from WooCommerce
        wc_products = woocommerce_service.fetch_all_products()
        
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
                    
            except Exception as e:
                products_failed += 1
                print(f"Failed to sync product {wc_product.get('id')}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        
        return WooCommerceSyncResponse(
            success=True,
            products_synced=products_added + products_updated,
            products_added=products_added,
            products_updated=products_updated,
            products_failed=products_failed,
            message=f"Successfully synced {products_added + products_updated} products from WooCommerce"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync WooCommerce products: {str(e)}"
        )
