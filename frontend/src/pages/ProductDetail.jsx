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
    const handleResize = () => setIsDesktop(window.innerWidth >= 768);
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
      <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
        <AppHeader title="Product Details" showBack />
        <Content>
          <div style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ color: 'var(--muted-foreground)' }}>Loading...</Text>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Product Details" showBack />

      <Content style={{ overflowX: 'hidden' }}>
        <div style={{ padding: '16px 16px 100px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
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
                borderRadius: 10,
                overflow: 'hidden',
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
                background: 'var(--card)',
                height: 'fit-content',
                width: '100%',
              }}
              styles={{ body: { padding: 0 } }}
            >
              {(() => {
                const proxied = getProxiedImageUrl(product.image_url);
                const imgH = isDesktop ? 400 : 300;
                return (
                  <div style={{
                    height: imgH,
                    overflow: 'hidden',
                    position: 'relative',
                    background: 'var(--muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    {proxied && (
                      <img
                        src={proxied}
                        alt={product.name}
                        style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block', padding: '12px' }}
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
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: proxied ? 'absolute' : 'relative',
                      top: 0, left: 0,
                    }}>
                      <span style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: 'var(--muted-foreground)',
                        textTransform: 'uppercase',
                        letterSpacing: 2,
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
              borderRadius: 10,
              boxShadow: 'var(--card-shadow)',
              border: '1px solid var(--border)',
              background: 'var(--card)',
              width: '100%',
              maxWidth: '100%',
              overflow: 'hidden'
            }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, width: '100%', marginBottom: 8 }}>
                  {product.category && product.category.split(',').map((cat, index) => (
                    <Tag key={index} color="orange" style={{ margin: 0 }}>
                      {cat.trim()}
                    </Tag>
                  ))}
                </div>
                <Title level={3} style={{ margin: '8px 0', wordBreak: 'break-word', color: 'var(--card-foreground)' }}>
                  {product.name}
                </Title>
                <Title level={2} style={{ color: 'var(--primary)', margin: '8px 0', wordBreak: 'break-word' }}>
                  KSh {product.price ? product.price.toLocaleString() : '0'}
                </Title>

                <Divider style={{ margin: '16px 0', borderColor: 'var(--border)' }} />

                <div style={{ width: '100%', overflow: 'hidden' }}>
                  <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>Description</Text>
                  <div
                    style={{
                      marginTop: 8,
                      color: 'var(--muted-foreground)',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word',
                      lineHeight: '1.6'
                    }}
                    dangerouslySetInnerHTML={{ __html: product.description }}
                  />
                </div>

                {product.benefits && (
                  <>
                    <Divider style={{ margin: '16px 0', borderColor: 'var(--border)' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>Key Benefits</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 20, color: 'var(--muted-foreground)' }}>
                        {product.benefits.map((benefit, index) => (
                          <li key={index} style={{ marginBottom: 4, wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                            {benefit}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}

                {product.ingredients && (
                  <>
                    <Divider style={{ margin: '16px 0', borderColor: 'var(--border)' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>Ingredients</Text>
                      <Paragraph style={{ marginTop: 8, color: 'var(--muted-foreground)', fontSize: 13, wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                        {product.ingredients}
                      </Paragraph>
                    </div>
                  </>
                )}

                {product.usage && (
                  <>
                    <Divider style={{ margin: '16px 0', borderColor: 'var(--border)' }} />
                    <div style={{ width: '100%', overflow: 'hidden' }}>
                      <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>How to Use</Text>
                      <Paragraph style={{ marginTop: 8, color: 'var(--muted-foreground)', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
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

      {/* Fixed Bottom Bar - Mobile */}
      {!isDesktop && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'var(--card)',
          backdropFilter: 'blur(10px)',
          padding: '12px 16px',
          boxShadow: '0 -2px 12px rgba(0,0,0,0.12)',
          borderTop: '1px solid var(--border)',
          zIndex: 10
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 80 }}>
              <Text style={{ fontSize: 12, marginBottom: 4, color: 'var(--muted-foreground)' }}>Quantity</Text>
              <InputNumber
                min={1}
                max={10}
                value={quantity}
                onChange={setQuantity}
                size="large"
                style={{ width: 80, fontSize: 16 }}
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
              style={{ height: 52, fontSize: 16, fontWeight: 600, flex: 1 }}
            >
              Add to Cart
            </Button>
          </div>
        </div>
      )}

      {/* Desktop: Add to Cart */}
      {isDesktop && (
        <div style={{ maxWidth: 1200, margin: '16px auto 0', padding: '0 16px' }}>
          <Card style={{
            borderRadius: 10,
            boxShadow: 'var(--card-shadow)',
            border: '1px solid var(--border)',
            background: 'var(--card)',
          }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', justifyContent: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', minWidth: 100 }}>
                <Text style={{ fontSize: 14, marginBottom: 8, color: 'var(--muted-foreground)', fontWeight: 500 }}>Quantity</Text>
                <InputNumber
                  min={1}
                  max={10}
                  value={quantity}
                  onChange={setQuantity}
                  size="large"
                  style={{ width: 100, fontSize: 18 }}
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
                style={{ height: 56, fontSize: 18, fontWeight: 600, minWidth: 300, paddingLeft: 32, paddingRight: 32 }}
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
