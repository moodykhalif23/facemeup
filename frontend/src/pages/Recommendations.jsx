import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Row, Col, App, Spin } from 'antd';
import { ShoppingCartOutlined } from '@ant-design/icons';
import { getRecommendations } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper function to get proxied image URL
const getProxiedImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  const baseUrl = API_BASE_URL.replace('/api/v1', '');
  return `${baseUrl}/api/v1/proxy/image?url=${encodeURIComponent(imageUrl)}`;
};

export default function Recommendations() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const { currentAnalysis } = useSelector((state) => state.analysis);
  const { message } = App.useApp();

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
                <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                  <Card
                    hoverable
                    onClick={() => navigate(`/product/${product.id}`)}
                    style={{ 
                      borderRadius: 12,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                      height: '100%',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      minHeight: isMobile ? 320 : 360,
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                    }}
                    styles={{
                      body: { 
                        padding: isMobile ? '12px' : '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        flex: 1
                      }
                    }}
                    cover={
                      <>
                        {product.image_url && (
                          <img 
                            src={getProxiedImageUrl(product.image_url)} 
                            alt={product.name}
                            style={{ 
                              height: isMobile ? 160 : 180, 
                              objectFit: 'cover',
                              borderRadius: '12px 12px 0 0',
                              width: '100%',
                              backgroundColor: '#f0f0f0',
                              transition: 'transform 0.3s ease'
                            }}
                            onMouseEnter={(e) => {
                              if (!isMobile) {
                                e.target.style.transform = 'scale(1.05)';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (!isMobile) {
                                e.target.style.transform = 'scale(1)';
                              }
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                              if (e.target.nextSibling) {
                                e.target.nextSibling.style.display = 'flex';
                              }
                            }}
                          />
                        )}
                        <div style={{ 
                          height: isMobile ? 160 : 180, 
                          background: 'linear-gradient(135deg, #ffff #ffff 0%,  100%)',
                          display: product.image_url ? 'none' : 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          borderRadius: '12px 12px 0 0',
                          color: 'white',
                          fontSize: isMobile ? 18 : 20,
                          fontWeight: 600,
                          textShadow: '0 2px 4px rgba(0,0,0,0.3)'
                        }}>
                          {product.name.substring(0, 2).toUpperCase()}
                        </div>
                      </>
                    }
                  >
                    <div style={{ 
                      marginBottom: 12,
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column'
                    }}>
                      <Text 
                        strong 
                        style={{ 
                          fontSize: isMobile ? 14 : 15, 
                          display: 'block',
                          marginBottom: 8,
                          minHeight: isMobile ? 48 : 42,
                          lineHeight: '1.4',
                          wordBreak: 'break-word',
                          color: '#2d3748'
                        }}
                      >
                        {product.name}
                      </Text>
                      <Text strong style={{ fontSize: isMobile ? 16 : 18, color: '#3B82F6', marginTop: 'auto', fontWeight: 700 }}>
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
                      size={isMobile ? "middle" : "large"}
                      block
                      style={{ 
                        borderRadius: 8, 
                        fontSize: isMobile ? 14 : 16, 
                        height: isMobile ? 40 : 44,
                        fontWeight: 600,
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        if (!isMobile) {
                          e.target.style.transform = 'translateY(-2px)';
                          e.target.style.boxShadow = '0 8px 15px -3px rgba(0, 0, 0, 0.2)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isMobile) {
                          e.target.style.transform = 'translateY(0)';
                          e.target.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
                        }
                      }}
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
                    borderRadius: 12,
                    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isMobile) {
                      e.target.style.transform = 'translateY(-2px)';
                      e.target.style.boxShadow = '0 8px 20px rgba(59, 130, 246, 0.4)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isMobile) {
                      e.target.style.transform = 'translateY(0)';
                      e.target.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                    }
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
