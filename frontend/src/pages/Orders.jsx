import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Card, Typography, List, Tag, Space, Empty, Spin, App } from 'antd';
import { ShoppingOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { getOrders } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Orders() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState([]);
  const { message } = App.useApp();

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await getOrders();
      setOrders(response.data.orders || []);
    } catch (error) {
      message.error('Failed to load orders');
      // Mock data for demo
      setOrders([
        {
          id: 1,
          order_number: 'ORD-2024-001',
          created_at: '2024-02-20T10:30:00',
          status: 'delivered',
          total: 149.97,
          items: [
            { product_name: 'Dr Rashel Salicylic Clear Serum', quantity: 2, price: 49.99 },
            { product_name: 'Estelm Deep Hydration Cream', quantity: 1, price: 49.99 }
          ]
        },
        {
          id: 2,
          order_number: 'ORD-2024-002',
          created_at: '2024-02-22T14:15:00',
          status: 'processing',
          total: 99.98,
          items: [
            { product_name: 'Dr Rashel Bright Tone Essence', quantity: 2, price: 49.99 }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'orange',
      processing: 'blue',
      shipped: 'cyan',
      delivered: 'green',
      cancelled: 'red'
    };
    return colors[status] || 'default';
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="My Orders" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : orders.length > 0 ? (
            <Space direction="vertical" size={16} style={{ width: '100%' }}>
              {orders.map((order) => (
                <Card
                  key={order.id}
                  style={{ 
                    borderRadius: 12,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
                  }}
                  styles={{ body: { padding: '16px' } }}
                >
                  {/* Order Header */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',
                    marginBottom: 12,
                    flexWrap: 'wrap',
                    gap: 8
                  }}>
                    <div>
                      <Text strong style={{ fontSize: 16 }}>
                        {order.order_number}
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 13 }}>
                        <ClockCircleOutlined /> {formatDate(order.created_at)}
                      </Text>
                    </div>
                    <Tag color={getStatusColor(order.status)} style={{ fontSize: 13 }}>
                      {order.status.toUpperCase()}
                    </Tag>
                  </div>

                  {/* Order Items */}
                  <List
                    size="small"
                    dataSource={order.items}
                    renderItem={(item) => (
                      <List.Item style={{ padding: '8px 0', border: 'none' }}>
                        <div style={{ width: '100%' }}>
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between',
                            alignItems: 'center'
                          }}>
                            <Text style={{ fontSize: 14 }}>
                              {item.product_name}
                            </Text>
                            <Text strong style={{ fontSize: 14 }}>
                              ${item.price}
                            </Text>
                          </div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            Qty: {item.quantity}
                          </Text>
                        </div>
                      </List.Item>
                    )}
                    style={{ marginBottom: 12 }}
                  />

                  {/* Order Total */}
                  <div style={{ 
                    borderTop: '1px solid #f0f0f0',
                    paddingTop: 12,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <Text strong style={{ fontSize: 15 }}>Total</Text>
                    <Text strong style={{ fontSize: 18, color: '#3B82F6' }}>
                      ${order.total.toFixed(2)}
                    </Text>
                  </div>
                </Card>
              ))}
            </Space>
          ) : (
            <Card style={{ borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
              <Empty
                image={<ShoppingOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
                description={
                  <div>
                    <Title level={4} style={{ marginTop: 16 }}>No orders yet</Title>
                    <Text type="secondary">Start shopping to see your orders here</Text>
                  </div>
                }
              />
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}
