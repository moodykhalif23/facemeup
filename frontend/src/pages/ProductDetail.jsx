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
      // For demo, create a mock product
      setProduct({
        id: id,
        name: 'Premium Skincare Product',
        price: 49.99,
        category: 'Moisturizer',
        description: 'A premium skincare product designed for your specific skin type. This product contains natural ingredients that help nourish and protect your skin.',
        benefits: [
          'Deeply hydrates skin',
          'Reduces fine lines',
          'Improves skin texture',
          'Non-comedogenic formula'
        ],
        ingredients: 'Aqua, Glycerin, Hyaluronic Acid, Vitamin E, Natural Extracts',
        usage: 'Apply twice daily to clean, dry skin. Gently massage until fully absorbed.'
      });
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

      <Content style={{ padding: '16px', paddingBottom: 100 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {/* Responsive Layout: Stacked on mobile, side-by-side on desktop */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: isDesktop ? '1fr 1fr' : '1fr',
            gap: 16,
            marginBottom: isDesktop ? 0 : 16
          }}>
            {/* Product Image */}
            <Card 
              style={{ 
                borderRadius: 16,
                overflow: 'hidden',
                boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                height: 'fit-content'
              }}
              styles={{ body: { padding: 0 } }}
            >
              <div style={{
                height: isDesktop ? 400 : 300,
                background: '#f5f5f5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Text style={{ fontSize: 18, color: '#999' }}>Product Image</Text>
              </div>
            </Card>

            {/* Product Info */}
            <Card style={{ borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Tag color="blue">{product.category}</Tag>
                <Title level={3} style={{ margin: '8px 0' }}>{product.name}</Title>
                <Title level={2} style={{ color: '#3B82F6', margin: '8px 0' }}>
                  ${product.price}
                </Title>
                
                <Divider style={{ margin: '16px 0' }} />
                
                <div>
                  <Text strong style={{ fontSize: 15 }}>Description</Text>
                  <Paragraph style={{ marginTop: 8, color: '#666' }}>
                    {product.description}
                  </Paragraph>
                </div>

                {product.benefits && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div>
                      <Text strong style={{ fontSize: 15 }}>Key Benefits</Text>
                      <ul style={{ marginTop: 8, paddingLeft: 20, color: '#666' }}>
                        {product.benefits.map((benefit, index) => (
                          <li key={index} style={{ marginBottom: 4 }}>{benefit}</li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}

                {product.ingredients && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div>
                      <Text strong style={{ fontSize: 15 }}>Ingredients</Text>
                      <Paragraph style={{ marginTop: 8, color: '#666', fontSize: 13 }}>
                        {product.ingredients}
                      </Paragraph>
                    </div>
                  </>
                )}

                {product.usage && (
                  <>
                    <Divider style={{ margin: '16px 0' }} />
                    <div>
                      <Text strong style={{ fontSize: 15 }}>How to Use</Text>
                      <Paragraph style={{ marginTop: 8, color: '#666' }}>
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
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
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
                  fontSize: 16
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
            borderRadius: 16, 
            boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
            background: 'transparent',
            border: 'none'
          }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center',
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
                    fontSize: 18
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
                  borderRadius: 12,
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
