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
      description: '',
      icon: <CameraOutlined style={{ fontSize: 32 }} />,
      color: 'var(--primary)',
      bg: 'var(--muted)',
      path: '/analysis',
    },
    {
      title: 'Recommendations',
      description: '',
      icon: <ShopOutlined style={{ fontSize: 32 }} />,
      color: '#10B981',
      bg: '#10B98115',
      path: '/recommendations',
    },
    {
      title: 'Profile History',
      description: '',
      icon: <HistoryOutlined style={{ fontSize: 32 }} />,
      color: '#7C3AED',
      bg: '#7C3AED15',
      path: '/profile',
    },
    {
      title: 'My Reports',
      description: '',
      icon: <FileTextOutlined style={{ fontSize: 32 }} />,
      color: '#0EA5E9',
      bg: '#0EA5E915',
      path: '/reports',
    },
    {
      title: 'Shopping Cart',
      description: '',
      icon: <ShoppingCartOutlined style={{ fontSize: 32 }} />,
      color: 'var(--chart-5)',
      bg: 'var(--accent)',
      path: '/cart',
    },
    {
      title: 'Loyalty Rewards',
      description: '',
      icon: <GiftOutlined style={{ fontSize: 32 }} />,
      color: '#DB2777',
      bg: '#DB277715',
      path: '/loyalty',
    },
  ];

  const adminCard = {
    title: 'Admin Panel',
    description: '',
    icon: <SettingOutlined style={{ fontSize: 32 }} />,
    color: '#ef4444',
    bg: '#ef444415',
    path: '/admin',
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="SkinCare AI" />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ marginBottom: 24, textAlign: 'center', padding: '16px 0' }}>
            <Title level={3} style={{ marginBottom: 8, color: 'var(--foreground)' }}>
              Welcome to Your Skincare Journey
            </Title>
            <Text style={{ fontSize: 15, color: 'var(--muted-foreground)' }}>
              AI-powered skin analysis and personalized recommendations
            </Text>
          </div>

          <Row gutter={[12, 12]}>
            {[...cardMenuItems, ...(user?.role === 'admin' ? [adminCard] : [])].map((item, index) => (
              <Col xs={12} sm={12} md={8} key={index}>
                <Card
                  hoverable
                  onClick={() => navigate(item.path)}
                  style={{
                    height: '100%',
                    borderRadius: 12,
                    boxShadow: 'var(--card-shadow)',
                    border: '1px solid var(--border)',
                    background: 'var(--card)',
                    cursor: 'pointer',
                  }}
                  styles={{
                    body: { padding: '20px 16px' }
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 64,
                      height: 64,
                      borderRadius: 16,
                      background: item.bg,
                      color: item.color,
                      marginBottom: 12,
                    }}>
                      {item.icon}
                    </div>
                    <Title level={5} style={{ marginBottom: 4, fontSize: 15, color: 'var(--card-foreground)' }}>
                      {item.title}
                    </Title>
                    {item.description ? (
                      <Text style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>
                        {item.description}
                      </Text>
                    ) : null}
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
