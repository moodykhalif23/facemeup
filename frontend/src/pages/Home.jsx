import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Row, Col, Space } from 'antd';
import { 
  CameraOutlined, 
  HistoryOutlined, 
  ShoppingCartOutlined, 
  UserOutlined,
  LogoutOutlined,
  GiftOutlined,
  ShopOutlined
} from '@ant-design/icons';
import { logout } from '../store/slices/authSlice';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { items } = useSelector((state) => state.cart);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const menuItems = [
    {
      title: 'Skin Analysis',
      description: 'Analyze your skin with AI',
      icon: <CameraOutlined style={{ fontSize: 32 }} />,
      color: '#3B82F6',
      path: '/analysis',
    },
    {
      title: 'Recommendations',
      description: 'Get personalized product recommendations',
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
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <Title level={3} style={{ margin: 0 }}>SkinCare AI</Title>
        <Space>
          <Text>Welcome, {user?.email}</Text>
          <Button 
            icon={<LogoutOutlined />} 
            onClick={handleLogout}
          >
            Logout
          </Button>
        </Space>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 32, textAlign: 'center' }}>
            <Title level={2}>Welcome to Your Skincare Journey</Title>
            <Text type="secondary">
              AI-powered skin analysis and personalized recommendations
            </Text>
          </div>

          <Row gutter={[16, 16]}>
            {menuItems.map((item, index) => (
              <Col xs={24} sm={12} md={8} key={index}>
                <Card
                  hoverable
                  onClick={() => navigate(item.path)}
                  style={{ height: '100%' }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      color: item.color, 
                      marginBottom: 16 
                    }}>
                      {item.icon}
                    </div>
                    <Title level={4}>{item.title}</Title>
                    <Text type="secondary">{item.description}</Text>
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
