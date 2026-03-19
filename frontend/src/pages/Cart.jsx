import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, List, InputNumber, Space, Empty } from 'antd';
import { DeleteOutlined, ShoppingOutlined } from '@ant-design/icons';
import { removeFromCart, updateQuantity } from '../store/slices/cartSlice';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Cart() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { items } = useSelector((state) => state.cart);

  const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

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
                borderRadius: 12,
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
                background: 'var(--card)',
                marginBottom: 16,
              }}>
                <List
                  dataSource={items}
                  renderItem={(item) => (
                    <List.Item
                      style={{ padding: '16px 0', borderColor: 'var(--border)' }}
                      actions={[
                        <InputNumber
                          key="quantity"
                          min={1}
                          value={item.quantity}
                          onChange={(value) => handleQuantityChange(item.id, value)}
                          size="large"
                          style={{ width: 80 }}
                        />,
                        <Button
                          key="delete"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleRemove(item.id)}
                          size="large"
                        >
                          Remove
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        title={<Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>{item.name}</Text>}
                        description={<Text style={{ fontSize: 14, color: 'var(--muted-foreground)' }}>KSh {item.price ? item.price.toLocaleString() : '0'} each</Text>}
                      />
                    </List.Item>
                  )}
                />
              </Card>

              <Card style={{
                borderRadius: 12,
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
                    onClick={() => navigate('/checkout')}
                    style={{ height: 52, fontSize: 16, fontWeight: 600 }}
                  >
                    Proceed to Checkout
                  </Button>
                </Space>
              </Card>
            </>
          ) : (
            <Card style={{
              borderRadius: 12,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
            }}>
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
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}
