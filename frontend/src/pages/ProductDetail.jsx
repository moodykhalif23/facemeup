import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Layout, Card, Button, Typography, Space, InputNumber, Divider, Tag, App } from 'antd';
import { ShoppingCartOutlined } from '@ant-design/icons';
import { getProduct } from '../services/api';
import { addToCart } from '../store/slices/cartSlice';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

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
                borderRadius: 8,
                overflow: 'hidden',
                boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                height: 'fit-content',
                width: '100%',
              }}
              styles={{ body: { padding: 0 } }}
            >
              {(() => {
                const visual = getProductVisual(product.category);
                const proxied = getProxiedImageUrl(product.image_url);
                const imgH = isDesktop ? 400 : 300;
                return (
                  <div style={{ height: imgH, overflow: 'hidden', position: 'relative' }}>
                    {proxied && (
                      <img
                        src={proxied}
                        alt={product.name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.nextSibling.style.display = 'flex';
                        }}
                      />
                    )}
                    <div style={{
                      display: proxied ? 'none' : 'flex',
                      width: '100%',
                      height: '100%',
                      background: visual.gradient,
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                      position: proxied ? 'absolute' : 'relative',
                      top: 0, left: 0,
                    }}>
                      <span style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: 'rgba(255,255,255,0.9)',
                        textTransform: 'uppercase',
                        letterSpacing: 2,
                        textShadow: '0 1px 3px rgba(0,0,0,0.25)',
                      }}>
                        {product.category || 'Skincare'}
                      </span>
                    </div>
                  </div>
                );
              })()}
            </Card>

            {/* Product Info */}
            <Card style={{
              borderRadius: 8,
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
                  <div 
                    style={{ 
                      marginTop: 8, 
                      color: '#666', 
                      wordBreak: 'break-word', 
                      overflowWrap: 'break-word',
                      lineHeight: '1.6'
                    }}
                    dangerouslySetInnerHTML={{ __html: product.description }}
                  />
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
                  borderRadius: 8
                }}
                styles={{
                  input: {
                    borderRadius: 8
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
                borderRadius: 8,
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
            borderRadius: 8, 
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
                    borderRadius: 8
                  }}
                  styles={{
                    input: {
                      borderRadius: 8
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
                  borderRadius: 8,
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
