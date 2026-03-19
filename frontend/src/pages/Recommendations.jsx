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

const getProxiedImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  const baseUrl = API_BASE_URL.replace('/api/v1', '');
  return `${baseUrl}/api/v1/proxy/image?url=${encodeURIComponent(imageUrl)}`;
};

const PLACEHOLDER_BG = '#ffffff';
const PLACEHOLDER_BORDER = '1px solid #f0f0f0';

export default function Recommendations() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const { currentAnalysis } = useSelector((state) => state.analysis);
  const { message } = App.useApp();

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
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

  const imgHeight = isMobile ? 160 : 180;
  const cardRadius = 8;

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
              {products.map((product) => {
                const proxied = getProxiedImageUrl(product.image_url);

                return (
                  <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                    <Card
                      hoverable
                      onClick={() => navigate(`/product/${product.id}`)}
                      style={{
                        borderRadius: cardRadius,
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                        overflow: 'hidden',
                        height: '100%',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                      }}
                      styles={{
                        body: {
                          padding: isMobile ? '12px' : '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          flex: 1,
                        },
                      }}
                      cover={
                        <div
                          style={{
                            height: imgHeight,
                            overflow: 'hidden',
                            position: 'relative',
                            flexShrink: 0,
                          }}
                        >
                          {proxied ? (
                            <img
                              src={proxied}
                              alt={product.name}
                              style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'cover',
                                display: 'block',
                                transition: 'transform 0.35s ease',
                              }}
                              onMouseEnter={(e) => { if (!isMobile) e.currentTarget.style.transform = 'scale(1.06)'; }}
                              onMouseLeave={(e) => { if (!isMobile) e.currentTarget.style.transform = 'scale(1)'; }}
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.nextSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}

                          {/* Placeholder — shown when no real image */}
                          <div
                            style={{
                              display: proxied ? 'none' : 'flex',
                              width: '100%',
                              height: '100%',
                              background: PLACEHOLDER_BG,
                              border: PLACEHOLDER_BORDER,
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexDirection: 'column',
                              position: proxied ? 'absolute' : 'relative',
                              top: 0,
                              left: 0,
                            }}
                          >
                            <span style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color: '#bbb',
                              textTransform: 'uppercase',
                              letterSpacing: 1,
                            }}>
                              {product.category || 'Skincare'}
                            </span>
                          </div>
                        </div>
                      }
                    >
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', marginBottom: 12 }}>
                        <Text
                          strong
                          style={{
                            fontSize: isMobile ? 13 : 14,
                            display: 'block',
                            marginBottom: 8,
                            lineHeight: '1.4',
                            color: '#2d3748',
                            flex: 1,
                          }}
                        >
                          {product.name}
                        </Text>
                        <Text strong style={{ fontSize: isMobile ? 15 : 17, color: '#3B82F6', fontWeight: 700 }}>
                          KSh {product.price ? product.price.toLocaleString() : '—'}
                        </Text>
                      </div>

                      <Button
                        type="primary"
                        icon={<ShoppingCartOutlined />}
                        onClick={(e) => { e.stopPropagation(); navigate(`/product/${product.id}`); }}
                        size={isMobile ? 'middle' : 'large'}
                        block
                        style={{
                          borderRadius: 10,
                          fontSize: isMobile ? 13 : 14,
                          height: isMobile ? 38 : 42,
                          fontWeight: 600,
                        }}
                      >
                        View Details
                      </Button>
                    </Card>
                  </Col>
                );
              })}
            </Row>
          ) : (
            <Card style={{ borderRadius: cardRadius, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
              <div style={{ textAlign: 'center', padding: '50px 20px' }}>
                <Title level={4}>No recommendations available</Title>
                <Text type="secondary">Complete a skin analysis to get personalized recommendations</Text>
                <br /><br />
                <Button
                  type="primary"
                  onClick={() => navigate('/analysis')}
                  size="large"
                  style={{ height: 48, fontSize: 16, borderRadius: 10 }}
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
