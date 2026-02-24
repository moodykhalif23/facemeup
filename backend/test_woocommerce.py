#!/usr/bin/env python3
"""Test WooCommerce connection and fetch products"""

from app.services.woocommerce_service import woocommerce_service

try:
    print("Fetching products from Dr. Rashel WooCommerce store...")
    products = woocommerce_service.fetch_all_products()
    print(f"\n✓ Successfully fetched {len(products)} products")
    
    if products:
        print("\nSample products:")
        for i, product in enumerate(products[:3], 1):
            print(f"\n{i}. {product.get('name', 'Unknown')}")
            print(f"   Price: {product.get('price', 'N/A')}")
            print(f"   SKU: {product.get('sku', 'N/A')}")
            print(f"   Stock: {product.get('stock_quantity', 'N/A')}")
            if product.get('images'):
                print(f"   Image: {product['images'][0].get('src', 'N/A')}")
    else:
        print("\n⚠ No products found in the store")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
