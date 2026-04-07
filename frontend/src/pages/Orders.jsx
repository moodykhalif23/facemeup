import { useState, useEffect } from 'react';
import { Layout, Card, Typography, List, Tag, Space, Empty, Spin, App } from 'antd';
import { ShoppingOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { getOrders } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Orders() {
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
      console.error('Failed to load orders:', error);
      message.error('Failed to load orders');
      setOrders([]);
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
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
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
                    borderRadius: 4,
                    boxShadow: 'var(--card-shadow)',
                    border: '1px solid var(--border)',
                    background: 'var(--card)',
                  }}
                  styles={{ body: { padding: '16px' } }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: 12,
                    flexWrap: 'wrap',
                    gap: 8
                  }}>
                    <div>
                      <Text strong style={{ fontSize: 16, color: 'var(--card-foreground)' }}>
                        {order.order_number}
                      </Text>
                      <br />
                      <Text style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>
                        <ClockCircleOutlined /> {formatDate(order.created_at)}
                      </Text>
                    </div>
                    <Tag color={getStatusColor(order.status)} style={{ fontSize: 13 }}>
                      {order.status.toUpperCase()}
                    </Tag>
                  </div>

                  <List
                    size="small"
                    dataSource={order.items}
                    renderItem={(item) => (
                      <List.Item style={{ padding: '8px 0', border: 'none' }}>
                        <div style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text style={{ fontSize: 14, color: 'var(--card-foreground)' }}>
                              {item.product_name}
                            </Text>
                            <Text strong style={{ fontSize: 14, color: 'var(--card-foreground)' }}>
                              KSh {item.price ? item.price.toLocaleString() : '0'}
                            </Text>
                          </div>
                          <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>
                            Qty: {item.quantity}
                          </Text>
                        </div>
                      </List.Item>
                    )}
                    style={{ marginBottom: 12 }}
                  />

                  <div style={{
                    borderTop: '1px solid var(--border)',
                    paddingTop: 12,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>Total</Text>
                    <Text strong style={{ fontSize: 18, color: 'var(--primary)' }}>
                      KSh {order.total ? order.total.toLocaleString() : '0'}
                    </Text>
                  </div>
                </Card>
              ))}
            </Space>
          ) : (
            <Card style={{
              borderRadius: 4,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
            }}>
              <Empty
                image={<ShoppingOutlined style={{ fontSize: 64, color: 'var(--border)' }} />}
                description={
                  <div>
                    <Title level={4} style={{ marginTop: 16, color: 'var(--card-foreground)' }}>No orders yet</Title>
                    <Text style={{ color: 'var(--muted-foreground)' }}>Start shopping to see your orders here</Text>
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

