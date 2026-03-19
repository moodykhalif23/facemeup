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

const CATEGORY_STYLES = {
  Serum:        { gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
  Moisturizer:  { gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' },
  Cleanser:     { gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
  Toner:        { gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
  Treatment:    { gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' },
  Sunscreen:    { gradient: 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)' },
  Mask:         { gradient: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)' },
  Exfoliant:    { gradient: 'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)' },
  'Eye Cream':  { gradient: 'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)' },
  'Eye Serum':  { gradient: 'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)' },
  Essence:      { gradient: 'linear-gradient(135deg, #96fbc4 0%, #f9f586 100%)' },
  'Body Lotion':{ gradient: 'linear-gradient(135deg, #fddb92 0%, #d1fdff 100%)' },
  'Body Balm':  { gradient: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)' },
  'Body Milk':  { gradient: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)' },
  'Body Wash':  { gradient: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)' },
  'Lip Care':   { gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)' },
  Powder:       { gradient: 'linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%)' },
  Gel:          { gradient: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)' },
};

const getProductVisual = (category) =>
  CATEGORY_STYLES[category] || { gradient: 'linear-gradient(135deg, #c3cfe2 0%, #a8b8d0 100%)' };

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
                const visual = getProductVisual(product.category);
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

                          {/* Category visual — always rendered, hidden when real image loads */}
                          <div
                            style={{
                              display: proxied ? 'none' : 'flex',
                              width: '100%',
                              height: '100%',
                              background: visual.gradient,
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
                              color: 'rgba(255,255,255,0.9)',
                              textTransform: 'uppercase',
                              letterSpacing: 1,
                              textShadow: '0 1px 3px rgba(0,0,0,0.25)',
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
