import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Row, Col, App, Spin } from 'antd';
import { ArrowLeftOutlined, ShoppingCartOutlined } from '@ant-design/icons';
import { getRecommendations } from '../services/api';

const { Header, Content } = Layout;
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
      <Header style={{ 
        background: '#fff', 
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 1
      }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/')}
          type="text"
          size="large"
        />
        <Title level={4} style={{ margin: '0 0 0 12px' }}>Recommendations</Title>
      </Header>

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : products.length > 0 ? (
            <Row gutter={[12, 12]}>
              {products.map((product) => (
                <Col xs={24} sm={12} md={8} key={product.id}>
                  <Card
                    hoverable
                    style={{ 
                      borderRadius: 16,
                      boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
                    }}
                    cover={
                      <div style={{ 
                        height: 200, 
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        borderRadius: '16px 16px 0 0'
                      }}>
                        <Text style={{ color: '#fff', fontSize: 16 }}>Product Image</Text>
                      </div>
                    }
                    actions={[
                      <Button 
                        key="view"
                        type="primary" 
                        icon={<ShoppingCartOutlined />}
                        onClick={() => navigate(`/product/${product.id}`)}
                        size="large"
                        style={{ borderRadius: 8 }}
                      >
                        View Details
                      </Button>
                    ]}
                  >
                    <Card.Meta
                      title={<Text strong style={{ fontSize: 16 }}>{product.name}</Text>}
                      description={
                        <>
                          <Text strong style={{ fontSize: 18, color: '#3B82F6' }}>
                            ${product.price}
                          </Text>
                          <br />
                          <Text type="secondary">{product.category}</Text>
                        </>
                      }
                    />
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
