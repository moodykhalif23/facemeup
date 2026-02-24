"""WooCommerce integration service for fetching products from Dr. Rashel store"""
import logging
from typing import Any

from woocommerce import API

from app.core.config import settings

logger = logging.getLogger(__name__)


class WooCommerceService:
    """Service for interacting with WooCommerce API"""

    def __init__(self):
        """Initialize WooCommerce API client"""
        self.wcapi = API(
            url=settings.woocommerce_url,
            consumer_key=settings.woocommerce_consumer_key,
            consumer_secret=settings.woocommerce_consumer_secret,
            version="wc/v3",
            timeout=30
        )

    def fetch_all_products(self, per_page: int = 100) -> list[dict[str, Any]]:
        """
        Fetch all products from WooCommerce store
        
        Args:
            per_page: Number of products to fetch per page (max 100)
            
        Returns:
            List of product dictionaries
        """
        all_products = []
        page = 1
        
        try:
            while True:
                logger.info(f"Fetching products page {page}")
                response = self.wcapi.get("products", params={
                    "per_page": per_page,
                    "page": page,
                    "status": "publish"
                })
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch products: {response.status_code} - {response.text}")
                    break
                
                products = response.json()
                
                if not products:
                    break
                
                all_products.extend(products)
                logger.info(f"Fetched {len(products)} products from page {page}")
                
                # Check if there are more pages
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                
                page += 1
                
        except Exception as e:
            logger.error(f"Error fetching products from WooCommerce: {e}")
            raise
        
        logger.info(f"Total products fetched: {len(all_products)}")
        return all_products

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        """
        Fetch a single product by ID
        
        Args:
            product_id: WooCommerce product ID
            
        Returns:
            Product dictionary or None if not found
        """
        try:
            response = self.wcapi.get(f"products/{product_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Product {product_id} not found: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None

    def parse_product_for_db(self, wc_product: dict[str, Any]) -> dict[str, Any]:
        """
        Parse WooCommerce product data into database format
        
        Args:
            wc_product: Raw WooCommerce product data
            
        Returns:
            Parsed product data for database
        """
        # Extract ingredients from description or meta data
        ingredients = []
        
        # Try to extract from short description or description
        description = wc_product.get('short_description', '') or wc_product.get('description', '')
        
        # Look for ingredients in meta data
        for meta in wc_product.get('meta_data', []):
            if meta.get('key', '').lower() in ['ingredients', '_ingredients']:
                ingredients_text = meta.get('value', '')
                if isinstance(ingredients_text, str):
                    ingredients = [i.strip() for i in ingredients_text.split(',')]
                break
        
        # If no ingredients found, use a default
        if not ingredients:
            ingredients = ['Natural Extracts', 'Vitamins', 'Moisturizers']
        
        return {
            'sku': wc_product.get('sku') or f"WC-{wc_product['id']}",
            'name': wc_product.get('name', 'Unknown Product'),
            'ingredients_csv': ','.join(ingredients),
            'stock': wc_product.get('stock_quantity', 0) or 0,
            'price': float(wc_product.get('price', 0) or 0),
            'description': wc_product.get('short_description', ''),
            'category': ', '.join([cat['name'] for cat in wc_product.get('categories', [])]),
            'image_url': wc_product.get('images', [{}])[0].get('src', '') if wc_product.get('images') else '',
            'wc_id': wc_product['id']
        }


# Singleton instance
woocommerce_service = WooCommerceService()
