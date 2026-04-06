# WooCommerce Multi-Product Cart Fill Snippet

The skin-analysis app sends customers to `drrashel.co.ke/checkout/` with
pre-filled cart items using this URL format:

```
/checkout/?add-to-cart=123,456,789&quantity=2,1,3
```

WooCommerce natively only supports a **single** `add-to-cart` parameter.
To support multiple products in one redirect, add the following snippet to
your theme's `functions.php` (or a custom plugin):

```php
/**
 * Allow filling the WooCommerce cart with multiple products via URL.
 * Expected query params:
 *   add-to-cart=ID1,ID2,ID3
 *   quantity=QTY1,QTY2,QTY3  (optional; defaults to 1 each)
 *
 * Example:
 *   /checkout/?add-to-cart=45,67&quantity=2,1
 */
add_action( 'wp_loaded', 'skincare_app_fill_cart_from_url', 20 );
function skincare_app_fill_cart_from_url() {
    if ( ! isset( $_GET['add-to-cart'] ) ) {
        return;
    }

    $ids       = array_map( 'absint', explode( ',', sanitize_text_field( $_GET['add-to-cart'] ) ) );
    $raw_qty   = isset( $_GET['quantity'] ) ? explode( ',', sanitize_text_field( $_GET['quantity'] ) ) : [];
    $quantities = array_map( 'absint', $raw_qty );

    // Only proceed when comma-separated (single ID is handled natively)
    if ( count( $ids ) <= 1 ) {
        return;
    }

    // Remove the params so WooCommerce's default handler doesn't double-add
    unset( $_GET['add-to-cart'], $_GET['quantity'] );

    WC()->cart->empty_cart();

    foreach ( $ids as $i => $product_id ) {
        $qty = isset( $quantities[ $i ] ) && $quantities[ $i ] > 0 ? $quantities[ $i ] : 1;
        WC()->cart->add_to_cart( $product_id, $qty );
    }

    wp_safe_redirect( wc_get_checkout_url() );
    exit;
}
```

## Steps to install

1. Log in to your WordPress admin (`drrashel.co.ke/wp-admin`).
2. Go to **Appearance → Theme File Editor** (or use a child theme).
3. Open `functions.php`.
4. Paste the snippet above at the bottom of the file.
5. Click **Update File**.
6. Test with: `https://drrashel.co.ke/checkout/?add-to-cart=PRODUCT_ID1,PRODUCT_ID2&quantity=1,2`

> **Note**: replace `PRODUCT_ID1` / `PRODUCT_ID2` with real WooCommerce product IDs.
> These are the `wc_id` values stored in the skin-analysis product catalog.
