import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, Space, InputNumber, Divider, Tag, App } from 'antd';
import { ShoppingCartOutlined, HeartOutlined } from '@ant-design/icons';
import { getProduct } from '../services/api';
import { addToCart } from '../store/slices/cartSlice';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper function to get proxied image URL
const getProxiedImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  const baseUrl = API_BASE_URL.replace('/api/v1', '');
  return `${baseUrl}/api/v1/proxy/image?url=${encodeURIComponent(imageUrl)}`;
};

export default function ProductDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const dispatch = useDispatch();
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 768);

  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth >= 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    setLoading(true);
    try {
      const response = await getProduct(id);
      setProduct(response.data);
    } catch (error) {
      message.error('Failed to load product details');
      navigate('/recommendations');
    } finally {
      setLoading(false);
    }
  };
  const handleAddToCart = () => {
    if (product) {
      dispatch(addToCart({
        id: product.id,
        name: product.name,
        price: product.price,
        quantity: quantity
      }));
      message.success('Added to cart!');
    }
  };

  if (loading || !product) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <AppHeader title="Product Details" showBack />
        <Content style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Text>Loading...</Text>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="Product Details" showBack />

      <Content style={{ padding: '16px', paddingBottom: 100, overflowX: 'hidden' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', width: '100%' }}>
          {/* Responsive Layout: Stacked on mobile, side-by-side on desktop */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: isDesktop ? '1fr 1fr' : '1fr',
            gap: 16,
            marginBottom: isDesktop ? 0 : 16,
            width: '100%'
          }}>
            {/* Product Image */}
            <Card 
              style={{ 
                borderRadius: 0,
                overflow: 'hidden',
                boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                height: 'fit-content',
                width: '100%',
                maxWidth: '100%'
              }}
              styles={{ body: { padding: 0 } }}
            >
              <>
                {product.image_url && (
                  <img 
                    src={getProxiedImageUrl(product.image_url)} 
                    alt={product.name}
                    style={{
                      width: '100%',
                      height: isDesktop ? 400 : 300,
                      objectFit: 'cover',
                      backgroundColor: '#f0f0f0'
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
                  height: isDesktop ? 400 : 300,
                  background: 'linear-gradient(135deg, #e0e1e7 0%, #e1dde4 100%)',
                  display: product.image_url ? 'none' : 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: 48,
                  fontWeight: 600,
                  letterSpacing: 2
                }}>
                  {product.name.substring(0, 2).toUpperCase()}
                </div>
              </>
            </Card>

            {/* Product Info */}
            <Card style={{ 
              borderRadius: 0, 
              boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
              width: '100%',
              maxWidth: '100%',
              overflow: 'hidden'
            }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: 8, 
                  width: '100%',
                  marginBottom: 8 
                }}>
                  {product.category && product.category.split(',').map((cat, index) => (
                    <Tag key={index} color="blue" style={{ margin: 0 }}>
                      {cat.trim()}
                    </Tag>
                  ))}
                </div>
                <Title level={3} style={{ margin: '8px 0', wordBreak: 'break-word' }}>{product.name}</Title>
                <Title level={2} style={{ color: '#3B82F6', margin: '8px 0', wordBreak: 'break-word' }}>
                  KSh {product.price ? product.price.toLocaleString() : '0'}
                </Title>
                
                <Divider style={{ margin: '16px 0' }} />
                
                <div style={{ width: '100%', overflow: 'hidden' }}>
                  <Text strong style={{ fontSize: 15 }}>Description</Text>
                  <Paragraph style={{ marginTop: 8, color: '#666', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                    {product.description}
                  </Paragraph>
                </div>

                {product.benefits && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15 }}>Key Benefits</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 20, color: '#666' }}>
                        {product.benefits.map((benefit, index) => (
                          <li key={index} style={{ marginBottom: 4, wordBreak: 'break-word', overflowWrap: 'break-word' }}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}

                {product.ingredients && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15 }}>Ingredients</Text>
                      <Paragraph style={{ marginTop: 8, color: '#666', fontSize: 13, wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                        {product.ingredients}
                      </Paragraph>
                    </div>
                  </>
                )}

                {product.usage && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15 }}>How to Use</Text>
                      <Paragraph style={{ marginTop: 8, color: '#666', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                        {product.usage}
                      </Paragraph>
                    </div>
                  </>
                )}
              </Space>
            </Card>
          </div>
        </div>
      </Content>

      {/* Fixed Bottom Bar - Only on Mobile */}
      {!isDesktop && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          padding: '12px 16px',
          boxShadow: '0 -2px 12px rgba(0,0,0,0.1)',
          zIndex: 10
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column',
              minWidth: 80
            }}>
              <Text style={{ fontSize: 12, marginBottom: 4, color: '#666' }}>Quantity</Text>
              <InputNumber
                min={1}
                max={10}
                value={quantity}
                onChange={setQuantity}
                size="large"
                style={{ 
                  width: 80,
                  fontSize: 16,
                  borderRadius: 0
                }}
                styles={{
                  input: {
                    borderRadius: 0
                  }
                }}
                controls={{
                  upIcon: <span style={{ fontSize: 16 }}>+</span>,
                  downIcon: <span style={{ fontSize: 16 }}>−</span>
                }}
              />
            </div>
            <Button
              type="primary"
              icon={<ShoppingCartOutlined />}
              onClick={handleAddToCart}
              size="large"
              block
              style={{
                height: 52,
                fontSize: 16,
                fontWeight: 600,
                borderRadius: 0,
                flex: 1
              }}
            >
              Add to Cart
            </Button>
          </div>
        </div>
      )}

      {/* Desktop: Add to Cart Section Inside Card */}
      {isDesktop && (
        <div style={{ 
          maxWidth: 1200, 
          margin: '16px auto 0',
          padding: '0 16px'
        }}>
          <Card style={{ 
            borderRadius: 0, 
            boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
            background: 'transparent',
            border: 'none'
          }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', justifyContent: 'center' }}>
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column',
                minWidth: 100
              }}>
                <Text style={{ fontSize: 14, marginBottom: 8, color: '#666', fontWeight: 500 }}>Quantity</Text>
                <InputNumber
                  min={1}
                  max={10}
                  value={quantity}
                  onChange={setQuantity}
                  size="large"
                  style={{ 
                    width: 100,
                    fontSize: 18,
                    borderRadius: 0
                  }}
                  styles={{
                    input: {
                      borderRadius: 0
                    }
                  }}
                  controls={{
                    upIcon: <span style={{ fontSize: 18 }}>+</span>,
                    downIcon: <span style={{ fontSize: 18 }}>−</span>
                  }}
                />
              </div>
              <Button
                type="primary"
                icon={<ShoppingCartOutlined />}
                onClick={handleAddToCart}
                size="large"
                style={{
                  height: 56,
                  fontSize: 18,
                  fontWeight: 600,
                  borderRadius: 0,
                  minWidth: 300,
                  paddingLeft: 32,
                  paddingRight: 32
                }}
              >
                Add to Cart
              </Button>
            </div>
          </Card>
        </div>
      )}
    </Layout>
  );
}
