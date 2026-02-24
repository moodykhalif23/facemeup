import { useNavigate } from 'react-router-dom';
import { Layout, Card, Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title } = Typography;

export default function Orders() {
  const navigate = useNavigate();

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
        <Title level={3} style={{ margin: '0 0 0 16px' }}>My Orders</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Card>
          <Title level={4}>Orders Page</Title>
        </Card>
      </Content>
    </Layout>
  );
}
