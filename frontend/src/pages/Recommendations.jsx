import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Row, Col, App, Spin } from 'antd';
import { ShoppingCartOutlined } from '@ant-design/icons';
import { getRecommendations } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Recommendations() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const { currentAnalysis } = useSelector((state) => state.analysis);
  const { message } = App.useApp();

  useEffect(() => {
    if (currentAnalysis?.profile) {
      fetchRecommendations();
    }
  }, [currentAnalysis]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await getRecommendations(
        currentAnalysis.profile.skin_type,
        currentAnalysis.profile.conditions || []
      );
      setProducts(response.data.products || []);
    } catch (error) {
      message.error('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="Recommendations" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : products.length > 0 ? (
            <Row gutter={[12, 12]}>
              {products.map((product) => (
                <Col xs={12} sm={12} md={8} key={product.id}>
                  <Card
                    hoverable
                    style={{ 
                      borderRadius: 12,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      height: '100%'
                    }}
                    styles={{
                      body: { padding: '12px' }
                    }}
                    cover={
                      <div style={{ 
                        height: 120, 
                        background: '#f5f5f5',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '12px 12px 0 0'
                      }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>Product Image</Text>
                      </div>
                    }
                  >
                    <div style={{ marginBottom: 8 }}>
                      <Text 
                        strong 
                        style={{ 
                          fontSize: 13, 
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {product.name}
                      </Text>
                      <Text strong style={{ fontSize: 15, color: '#3B82F6' }}>
                        ${product.price}
                      </Text>
                    </div>
                    <Button 
                      type="primary" 
                      icon={<ShoppingCartOutlined />}
                      onClick={() => navigate(`/product/${product.id}`)}
                      size="small"
                      block
                      style={{ borderRadius: 6, fontSize: 12 }}
                    >
                      View Details
                    </Button>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Card style={{ borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
              <div style={{ textAlign: 'center', padding: '50px 20px' }}>
                <Title level={4}>No recommendations available</Title>
                <Text type="secondary">Complete a skin analysis to get personalized recommendations</Text>
                <br /><br />
                <Button 
                  type="primary" 
                  onClick={() => navigate('/analysis')}
                  size="large"
                  style={{ 
                    height: 48,
                    fontSize: 16,
                    borderRadius: 12
                  }}
                >
                  Start Analysis
                </Button>
              </div>
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}
