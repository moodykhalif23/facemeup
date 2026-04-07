import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, List, InputNumber, Space, Empty, App } from 'antd';
import { DeleteOutlined, ShoppingOutlined } from '@ant-design/icons';
import { removeFromCart, updateQuantity, updateItemMeta } from '../store/slices/cartSlice';
import AppHeader from '../components/AppHeader';
import { getProducts, syncWooCommerceWcIds } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Cart() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { items } = useSelector((state) => state.cart);
  const { message } = App.useApp();
  const [syncing, setSyncing] = useState(false);

  const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const missingWc = items.filter((item) => !item.wc_id);

  /**
   * Build a WooCommerce multi-product cart URL.
   *
   * Uses comma-separated IDs and quantities so the external site can add all
   * items in a single request.  Format (requires a tiny WooCommerce snippet
   * on drrashel.co.ke — see /docs/woocommerce_cart_fill.md):
   *
   *   /checkout/?add-to-cart=ID1,ID2&quantity=QTY1,QTY2
   *
   * Falls back to single-item format when there is only one product.
   */
  const buildCheckoutUrl = (wcMap = new Map()) => {
    const base = import.meta.env.VITE_CHECKOUT_URL || 'https://drrashel.co.ke/checkout/';

    const wcIds = [];
    const quantities = [];

    items.forEach((item) => {
      const wcId = item.wc_id || wcMap.get(item.sku) || wcMap.get(item.id);
      if (!wcId) return;           // skip items without a WC product ID
      wcIds.push(wcId);
      quantities.push(item.quantity);
    });

    if (wcIds.length === 0) return base;

    // Single item: use native WooCommerce single-product URL
    if (wcIds.length === 1) {
      return `${base}?add-to-cart=${wcIds[0]}&quantity=${quantities[0]}`;
    }

    // Multiple items: comma-separated format (requires server-side snippet)
    return (
      `${base}?add-to-cart=${wcIds.join(',')}&quantity=${quantities.join(',')}`
    );
  };

  const ensureWcIds = async () => {
    if (missingWc.length === 0) {
      return new Map();
    }

    setSyncing(true);
    try {
      await syncWooCommerceWcIds();
      const response = await getProducts();
      const wcMap = new Map(response.data.map((p) => [p.sku, p.wc_id]));

      missingWc.forEach((item) => {
        const wcId = wcMap.get(item.sku) || wcMap.get(item.id);
        if (wcId) {
          dispatch(updateItemMeta({ id: item.id, data: { wc_id: wcId } }));
        }
      });

      return wcMap;
    } catch (err) {
      message.error('Failed to sync products with website');
      return null;
    } finally {
      setSyncing(false);
    }
  };

  const handleQuantityChange = (id, quantity) => {
    if (quantity > 0) {
      dispatch(updateQuantity({ id, quantity }));
    }
  };

  const handleRemove = (id) => {
    dispatch(removeFromCart(id));
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Shopping Cart" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {items.length > 0 ? (
            <>
              <Card style={{
                borderRadius: 6,
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
                background: 'var(--card)',
                marginBottom: 16,
              }}>
                <List
                  dataSource={items}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '16px 0', borderColor: 'var(--border)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%' }}>
                        {/* Name + price */}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <Text strong style={{ fontSize: 14, color: 'var(--card-foreground)', display: 'block', lineHeight: '1.4' }}>
                            {item.name}
                          </Text>
                          <Text style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600 }}>
                            KSh {item.price ? item.price.toLocaleString() : '0'}
                          </Text>
                        </div>
                        {/* Quantity */}
                        <InputNumber
                          min={1}
                          value={item.quantity}
                          onChange={(value) => handleQuantityChange(item.id, value)}
                          size="middle"
                          style={{ width: 70, flexShrink: 0 }}
                        />
                        {/* Remove */}
                        <Button
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleRemove(item.id)}
                          size="middle"
                          style={{ flexShrink: 0 }}
                        />
                      </div>
                    </List.Item>
                  )}
                />
              </Card>

              <Card style={{
                borderRadius: 6,
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
                background: 'var(--card)',
              }}>
                <Space direction="vertical" style={{ width: '100%' }} size={16}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>Total:</Text>
                    <Title level={3} style={{ margin: 0, color: 'var(--primary)' }}>
                      KSh {total.toLocaleString()}
                    </Title>
                  </div>
                  <Button
                    type="primary"
                    size="large"
                    block
                    onClick={() => {
                      (async () => {
                        const wcMap = await ensureWcIds();
                        if (wcMap === null) return;   // sync itself failed

                        const stillMissing = items.filter(
                          (item) => !item.wc_id && !wcMap.get(item.sku) && !wcMap.get(item.id)
                        );

                        // Warn about un-synced items but proceed with the rest
                        if (stillMissing.length > 0) {
                          message.warning(
                            `${stillMissing.length} item(s) could not be synced and will be skipped at checkout.`
                          );
                        }

                        const checkoutUrl = buildCheckoutUrl(wcMap);
                        if (checkoutUrl === (import.meta.env.VITE_CHECKOUT_URL || 'https://drrashel.co.ke/checkout/')) {
                          // All items were skipped — nothing to send
                          message.error('No items are available for checkout. Please try syncing again.');
                          return;
                        }

                        window.location.href = checkoutUrl;
                      })();
                    }}
                    loading={syncing}
                    style={{ height: 52, fontSize: 16, fontWeight: 600 }}
                  >
                    Checkout on Website
                  </Button>
                </Space>
              </Card>
            </>
          ) : (
            <Empty
              image={<ShoppingOutlined style={{ fontSize: 64, color: 'var(--border)' }} />}
              description={
                <div>
                  <Title level={4} style={{ marginTop: 16, color: 'var(--card-foreground)' }}>
                    Your cart is empty
                  </Title>
                  <Text style={{ color: 'var(--muted-foreground)' }}>Add some products to get started</Text>
                </div>
              }
            >
              <Button
                type="primary"
                icon={<ShoppingOutlined />}
                onClick={() => navigate('/recommendations')}
                size="large"
                style={{ height: 48, fontSize: 16, marginTop: 16 }}
              >
                Browse Products
              </Button>
            </Empty>
          )}
        </div>
      </Content>
    </Layout>
  );
}

