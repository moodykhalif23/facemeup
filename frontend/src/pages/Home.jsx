import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Typography, Row, Col } from 'antd';
import {
  CameraOutlined,
  HistoryOutlined,
  ShoppingCartOutlined,
  GiftOutlined,
  ShopOutlined,
  SettingOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const navigate = useNavigate();
  const { items } = useSelector((state) => state.cart);
  const { user } = useSelector((state) => state.auth);

  const cardMenuItems = [
    {
      title: 'Skin Analysis',
      description: 'Get AI-powered skin analysis',
      icon: <CameraOutlined style={{ fontSize: 32 }} />,
      path: '/analysis',
    },
    {
      title: 'Recommendations',
      description: 'Personalized product picks',
      icon: <ShopOutlined style={{ fontSize: 32 }} />,
      path: '/recommendations',
    },
    {
      title: 'Profile History',
      description: 'View your analysis history',
      icon: <HistoryOutlined style={{ fontSize: 32 }} />,
      path: '/profile',
    },
    {
      title: 'My Reports',
      description: 'Download detailed reports',
      icon: <FileTextOutlined style={{ fontSize: 32 }} />,
      path: '/reports',
    },
    {
      title: 'Shopping Cart',
      description: 'Review selected items',
      icon: <ShoppingCartOutlined style={{ fontSize: 32 }} />,
      path: '/cart',
    },
    {
      title: 'Loyalty Rewards',
      description: 'Earn and redeem points',
      icon: <GiftOutlined style={{ fontSize: 32 }} />,
      path: '/loyalty',
    },
  ];

  const adminCard = {
    title: 'Admin Panel',
    description: 'Manage system settings',
    icon: <SettingOutlined style={{ fontSize: 32 }} />,
    path: '/admin',
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="SkinCare AI" />

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 48, textAlign: 'center', paddingTop: 16 }}>
            <Title level={2} style={{
              margin: '0 0 8px 0',
              color: 'var(--card-foreground)',
              fontSize: 28,
              fontWeight: 600,
            }}>
              Welcome Back
            </Title>
            <Text style={{ fontSize: 15, color: 'var(--muted-foreground)' }}>
              Analyze your skin and discover personalized skincare solutions
            </Text>
          </div>

          <Row gutter={[16, 16]}>
            {[...cardMenuItems, ...(user?.role === 'admin' ? [adminCard] : [])].map((item, index) => (
              <Col xs={12} sm={12} md={8} lg={6} key={index}>
                <Card
                  hoverable
                  onClick={() => navigate(item.path)}
                  style={{
                    height: '100%',
                    borderRadius: 8,
                    boxShadow: 'var(--card-shadow)',
                    border: '1px solid var(--border)',
                    background: 'var(--card)',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 12px 32px rgba(0,0,0,0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'var(--card-shadow)';
                  }}
                  styles={{
                    body: { padding: '24px 20px' }
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 56,
                      height: 56,
                      borderRadius: 8,
                      background: 'var(--muted)',
                      color: 'var(--primary)',
                      marginBottom: 16,
                      transition: 'all 0.3s ease',
                    }}>
                      {item.icon}
                    </div>
                    <Title level={5} style={{
                      marginBottom: 8,
                      fontSize: 15,
                      fontWeight: 600,
                      color: 'var(--card-foreground)',
                    }}>
                      {item.title}
                    </Title>
                    <Text style={{
                      fontSize: 13,
                      color: 'var(--muted-foreground)',
                      lineHeight: 1.5,
                    }}>
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

