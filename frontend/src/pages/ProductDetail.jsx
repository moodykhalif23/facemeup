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

      <Content style={{ padding: '16px', paddingBottom: 80 }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* Product Image */}
            <Card 
              style={{ 
                borderRadius: 16,
                overflow: 'hidden',
                boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
              }}
              styles={{ body: { padding: 0 } }}
            >
              <div style={{
                height: 300,
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Text style={{ fontSize: 18, color: '#666' }}>Product Image</Text>
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
          </Space>
        </div>
      </Content>

      {/* Fixed Bottom Bar */}
      <div style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: '#fff',
        padding: '12px 16px',
        boxShadow: '0 -2px 12px rgba(0,0,0,0.1)',
        zIndex: 10
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto', display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text>Qty:</Text>
            <InputNumber
              min={1}
              max={10}
              value={quantity}
              onChange={setQuantity}
              style={{ width: 60 }}
            />
          </div>
          <Button
            type="primary"
            icon={<ShoppingCartOutlined />}
            onClick={handleAddToCart}
            size="large"
            block
            style={{
              height: 48,
              fontSize: 16,
              fontWeight: 600,
              borderRadius: 8
            }}
          >
            Add to Cart
          </Button>
        </div>
      </div>
    </Layout>
  );
}
