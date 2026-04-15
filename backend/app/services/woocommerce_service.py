"""WooCommerce integration service for fetching products from Dr. Rashel store"""
import json
import logging
from datetime import datetime
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
        ingredients = []
        benefits = []
        usage = ""

        # Extract fields from meta data
        meta_key_map = {
            'ingredients': 'ingredients',
            '_ingredients': 'ingredients',
            'key_benefits': 'benefits',
            '_key_benefits': 'benefits',
            'benefits': 'benefits',
            '_benefits': 'benefits',
            'how_to_use': 'usage',
            '_how_to_use': 'usage',
            'usage': 'usage',
            '_usage': 'usage',
            'directions': 'usage',
        }
        for meta in wc_product.get('meta_data', []):
            key = meta.get('key', '').lower()
            value = meta.get('value', '')
            if not isinstance(value, str) or not value.strip():
                continue
            field = meta_key_map.get(key)
            if field == 'ingredients' and not ingredients:
                ingredients = [i.strip() for i in value.split(',') if i.strip()]
            elif field == 'benefits' and not benefits:
                benefits = [b.strip() for b in value.split('|') if b.strip()]
                if not benefits:
                    benefits = [b.strip() for b in value.split('\n') if b.strip()]
            elif field == 'usage' and not usage:
                usage = value.strip()

        if not ingredients:
            ingredients = []

        return {
            'sku': wc_product.get('sku') or f"WC-{wc_product['id']}",
            'name': wc_product.get('name', 'Unknown Product'),
            'ingredients_csv': ','.join(ingredients),
            'benefits_csv': '|'.join(benefits),
            'usage': usage,
            'stock': wc_product.get('stock_quantity', 0) or 0,
            'price': float(wc_product.get('price', 0) or 0),
            'description': wc_product.get('short_description', '') or wc_product.get('description', ''),
            'category': ', '.join([cat['name'] for cat in wc_product.get('categories', [])]),
            'image_url': wc_product.get('images', [{}])[0].get('src', '') if wc_product.get('images') else '',
            'suitable_for': 'all',
            'effects_csv': '',
            'wc_id': wc_product['id']
        }


    # WooCommerce status → local status
    WC_STATUS_MAP: dict[str, str] = {
        "pending": "created",
        "processing": "paid",
        "on-hold": "created",
        "completed": "delivered",
        "cancelled": "cancelled",
        "refunded": "cancelled",
        "failed": "cancelled",
    }

    def fetch_orders(self, per_page: int = 100, after: datetime | None = None) -> list[dict[str, Any]]:
        """Fetch all orders from WooCommerce (newest first)."""
        all_orders: list[dict[str, Any]] = []
        page = 1
        params: dict[str, Any] = {"per_page": per_page, "page": page, "orderby": "date", "order": "desc"}
        if after:
            params["after"] = after.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            while True:
                params["page"] = page
                response = self.wcapi.get("orders", params=params)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch orders page {page}: {response.status_code}")
                    break
                orders = response.json()
                if not orders:
                    break
                all_orders.extend(orders)
                total_pages = int(response.headers.get("X-WP-TotalPages", 1))
                if page >= total_pages:
                    break
                page += 1
        except Exception as e:
            logger.error(f"Error fetching orders from WooCommerce: {e}")
            raise

        logger.info(f"Fetched {len(all_orders)} orders from WooCommerce")
        return all_orders

    def parse_order_for_db(self, wc_order: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Convert a WooCommerce order payload into local DB fields."""
        items = []
        for line in wc_order.get("line_items", []):
            items.append({
                "product_name": line.get("name", "Product"),
                "sku": line.get("sku", ""),
                "quantity": line.get("quantity", 1),
                "price": float(line.get("price", 0) or 0),
            })

        local_status = self.WC_STATUS_MAP.get(wc_order.get("status", ""), "created")
        total = float(wc_order.get("total", 0) or 0)

        # Parse WC date — comes as ISO 8601 without timezone suffix
        date_str = wc_order.get("date_created", "")
        try:
            created_at = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            created_at = datetime.utcnow()

        return {
            "wc_order_id": wc_order["id"],
            "user_id": user_id,
            "channel": "woocommerce",
            "items_json": __import__("json").dumps(items),
            "status": local_status,
            "total": total,
            "created_at": created_at,
        }

    def billing_email(self, wc_order: dict[str, Any]) -> str:
        """Extract billing email from a WooCommerce order."""
        return (wc_order.get("billing", {}).get("email", "") or "").lower().strip()


# Singleton instance
woocommerce_service = WooCommerceService()
