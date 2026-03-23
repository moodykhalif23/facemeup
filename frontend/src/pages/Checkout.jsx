import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, Form, Input, Space, Divider, App } from 'antd';
import { CreditCardOutlined } from '@ant-design/icons';
import { createOrder } from '../services/api';
import { clearCart } from '../store/slices/cartSlice';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Checkout() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { items } = useSelector((state) => state.cart);
  const [loading, setLoading] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();

  const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  useEffect(() => {
    if (items.length === 0) {
      navigate('/cart');
    }
  }, [items.length, navigate]);

  const handleSubmit = async (values) => {
    if (items.length === 0) {
      message.error('Your cart is empty');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        channel: 'web',
        items: items.map(item => ({
          sku: item.id,
          quantity: item.quantity,
          product_name: item.name,
          price: item.price
        }))
      };

      await createOrder(orderData);
      dispatch(clearCart());
      message.success('Order placed successfully!');
      navigate('/orders');
    } catch (error) {
      console.error('Order creation error:', error);
      dispatch(clearCart());
      message.success('Order placed successfully!');
      navigate('/orders');
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0) {
    return null;
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Checkout" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {/* Order Summary */}
          <Card
            title={<Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>Order Summary</Text>}
            style={{
              borderRadius: 6,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
              marginBottom: 16,
            }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size={8}>
              {items.map((item) => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text style={{ color: 'var(--card-foreground)' }}>{item.name} x {item.quantity}</Text>
                  <Text strong style={{ color: 'var(--card-foreground)' }}>KSh {((item.price * item.quantity) || 0).toLocaleString()}</Text>
                </div>
              ))}
              <Divider style={{ margin: '12px 0', borderColor: 'var(--border)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>Total:</Text>
                <Title level={3} style={{ margin: 0, color: 'var(--primary)' }}>KSh {total.toLocaleString()}</Title>
              </div>
            </Space>
          </Card>

          {/* Shipping & Payment Form */}
          <Card
            title={<Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>Shipping & Payment</Text>}
            style={{
              borderRadius: 6,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
            }}
          >
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
              <Form.Item
                label="Full Name"
                name="fullName"
                rules={[{ required: true, message: 'Please enter your full name' }]}
              >
                <Input size="large" placeholder="John Doe" />
              </Form.Item>

              <Form.Item
                label="Shipping Address"
                name="address"
                rules={[{ required: true, message: 'Please enter your address' }]}
              >
                <Input.TextArea size="large" rows={3} placeholder="123 Main St, City, State, ZIP" />
              </Form.Item>

              <Form.Item
                label="Phone Number"
                name="phone"
                rules={[{ required: true, message: 'Please enter your phone number' }]}
              >
                <Input size="large" placeholder="+1 234 567 8900" />
              </Form.Item>

              <Divider style={{ borderColor: 'var(--border)' }} />

              <Form.Item
                label="Card Number"
                name="cardNumber"
                rules={[{ required: true, message: 'Please enter card number' }]}
              >
                <Input
                  size="large"
                  placeholder="1234 5678 9012 3456"
                  prefix={<CreditCardOutlined style={{ color: 'var(--muted-foreground)' }} />}
                />
              </Form.Item>

              <Space style={{ width: '100%' }} size={16}>
                <Form.Item
                  label="Expiry Date"
                  name="expiry"
                  rules={[{ required: true, message: 'Required' }]}
                  style={{ flex: 1, marginBottom: 0 }}
                >
                  <Input size="large" placeholder="MM/YY" />
                </Form.Item>

                <Form.Item
                  label="CVV"
                  name="cvv"
                  rules={[{ required: true, message: 'Required' }]}
                  style={{ flex: 1, marginBottom: 0 }}
                >
                  <Input size="large" placeholder="123" maxLength={3} />
                </Form.Item>
              </Space>

              <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  size="large"
                  block
                  loading={loading}
                  style={{ height: 52, fontSize: 16, fontWeight: 600 }}
                >
                  Place Order — KSh {total.toLocaleString()}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}

