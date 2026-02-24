import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Row, Col, message, Spin } from 'antd';
import { ArrowLeftOutlined, ShoppingCartOutlined } from '@ant-design/icons';
import { getRecommendations } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Recommendations() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);
  const { currentAnalysis } = useSelector((state) => state.analysis);

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
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/')}
          type="text"
        />
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Recommendations</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : products.length > 0 ? (
            <Row gutter={[16, 16]}>
              {products.map((product) => (
                <Col xs={24} sm={12} md={8} key={product.id}>
                  <Card
                    hoverable
                    cover={
                      <div style={{ 
                        height: 200, 
                        background: '#f0f0f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        <Text type="secondary">Product Image</Text>
                      </div>
                    }
                    actions={[
                      <Button 
                        type="primary" 
                        icon={<ShoppingCartOutlined />}
                        onClick={() => navigate(`/product/${product.id}`)}
                      >
                        View Details
                      </Button>
                    ]}
                  >
                    <Card.Meta
                      title={product.name}
                      description={
                        <>
                          <Text strong>${product.price}</Text>
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
            <Card>
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Title level={4}>No recommendations available</Title>
                <Text type="secondary">Complete a skin analysis to get personalized recommendations</Text>
                <br /><br />
                <Button type="primary" onClick={() => navigate('/analysis')}>
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
