import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, List, InputNumber, Space, Empty } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined, ShoppingOutlined } from '@ant-design/icons';
import { removeFromCart, updateQuantity } from '../store/slices/cartSlice';

const { Header, Content } = Layout;
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
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/')}
          type="text"
        />
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Shopping Cart</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {items.length > 0 ? (
            <>
              <Card>
                <List
                  dataSource={items}
                  renderItem={(item) => (
                    <List.Item
                      actions={[
                        <InputNumber
                          min={1}
                          value={item.quantity}
                          onChange={(value) => handleQuantityChange(item.id, value)}
                        />,
                        <Button
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleRemove(item.id)}
                        >
                          Remove
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        title={item.name}
                        description={`$${item.price} each`}
                      />
                    </List.Item>
                  )}
                />
              </Card>

              <Card style={{ marginTop: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text strong>Total:</Text>
                    <Title level={4}>${total.toFixed(2)}</Title>
                  </div>
                  <Button 
                    type="primary" 
                    size="large" 
                    block
                    onClick={() => navigate('/checkout')}
                  >
                    Proceed to Checkout
                  </Button>
                </Space>
              </Card>
            </>
          ) : (
            <Card>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="Your cart is empty"
              >
                <Button 
                  type="primary" 
                  icon={<ShoppingOutlined />}
                  onClick={() => navigate('/recommendations')}
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
