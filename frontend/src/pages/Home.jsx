import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Typography, Row, Col } from 'antd';
import { 
  CameraOutlined, 
  HistoryOutlined, 
  ShoppingCartOutlined, 
  UserOutlined,
  GiftOutlined,
  ShopOutlined
} from '@ant-design/icons';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const navigate = useNavigate();
  const { items } = useSelector((state) => state.cart);

  const cardMenuItems = [
    {
      title: 'Skin Analysis',
      description: 'Analyze your skin with AI',
      icon: <CameraOutlined style={{ fontSize: 32 }} />,
      color: '#3B82F6',
      path: '/analysis',
    },
    {
      title: 'Recommendations',
      description: 'Get personalized product',
      icon: <ShopOutlined style={{ fontSize: 32 }} />,
      color: '#10B981',
      path: '/recommendations',
    },
    {
      title: 'Profile History',
      description: 'View your analysis history',
      icon: <HistoryOutlined style={{ fontSize: 32 }} />,
      color: '#8B5CF6',
      path: '/profile',
    },
    {
      title: 'Shopping Cart',
      description: `${items.length} items in cart`,
      icon: <ShoppingCartOutlined style={{ fontSize: 32 }} />,
      color: '#F59E0B',
      path: '/cart',
    },
    {
      title: 'My Orders',
      description: 'Track your orders',
      icon: <UserOutlined style={{ fontSize: 32 }} />,
      color: '#EF4444',
      path: '/orders',
    },
    {
      title: 'Loyalty Rewards',
      description: 'View your rewards',
      icon: <GiftOutlined style={{ fontSize: 32 }} />,
      color: '#EC4899',
      path: '/loyalty',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="SkinCare AI" />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 24, textAlign: 'center', padding: '16px 0' }}>
            <Title level={3} style={{ marginBottom: 8 }}>Welcome to Your Skincare Journey</Title>
            <Text type="secondary" style={{ fontSize: 15 }}>
              AI-powered skin analysis and personalized recommendations
            </Text>
          </div>

          <Row gutter={[12, 12]}>
            {cardMenuItems.map((item, index) => (
              <Col xs={12} sm={12} md={8} key={index}>
                <Card
                  hoverable
                  onClick={() => navigate(item.path)}
                  style={{ 
                    height: '100%',
                    borderRadius: 16,
                    boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
                  }}
                  styles={{
                    body: { padding: '20px 16px' }
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      color: item.color, 
                      marginBottom: 12 
                    }}>
                      {item.icon}
                    </div>
                    <Title level={5} style={{ marginBottom: 4, fontSize: 15 }}>
                      {item.title}
                    </Title>
                    <Text type="secondary" style={{ fontSize: 13 }}>
                      {item.description}
                    </Text>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </Content>
    </Layout>
  );
}
