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
            <Row gutter={[16, 16]}>
              {products.map((product) => (
                <Col xs={12} sm={12} md={8} lg={6} key={product.id}>
                  <Card
                    hoverable
                    onClick={() => navigate(`/product/${product.id}`)}
                    style={{ 
                      borderRadius: 12,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      height: '100%',
                      cursor: 'pointer'
                    }}
                    styles={{
                      body: { padding: '16px' }
                    }}
                    cover={
                      product.image_url ? (
                        <>
                          <img 
                            src={product.image_url} 
                            alt={product.name}
                            style={{ 
                              height: 180, 
                              objectFit: 'cover',
                              borderRadius: '12px 12px 0 0',
                              width: '100%'
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                              if (e.target.nextSibling) {
                                e.target.nextSibling.style.display = 'flex';
                              }
                            }}
                          />
                          <div style={{ 
                            height: 180, 
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            display: 'none',
                            alignItems: 'center',
                            justifyContent: 'center',
                            borderRadius: '12px 12px 0 0',
                            color: 'white',
                            fontSize: 16,
                            fontWeight: 500
                          }}>
                            {product.name.substring(0, 2).toUpperCase()}
                          </div>
                        </>
                      ) : (
                        <div style={{ 
                          height: 180, 
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: '12px 12px 0 0',
                          color: 'white',
                          fontSize: 16,
                          fontWeight: 500
                        }}>
                          {product.name.substring(0, 2).toUpperCase()}
                        </div>
                      )
                    }
                  >
                    <div style={{ marginBottom: 12 }}>
                      <Text 
                        strong 
                        style={{ 
                          fontSize: 14, 
                          display: 'block',
                          marginBottom: 4
                        }}
                      >
                        {product.name}
                      </Text>
                      <Text strong style={{ fontSize: 16, color: '#3B82F6' }}>
                        KSh {product.price ? product.price.toLocaleString() : '0'}
                      </Text>
                    </div>
                    <Button 
                      type="primary" 
                      icon={<ShoppingCartOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/product/${product.id}`);
                      }}
                      size="middle"
                      block
                      style={{ borderRadius: 8, fontSize: 14, height: 40 }}
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
