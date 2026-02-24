import { useNavigate, useParams } from 'react-router-dom';
import { Layout, Card, Button, Typography } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title } = Typography;

export default function ProductDetail() {
  const navigate = useNavigate();
  const { id } = useParams();

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
          onClick={() => navigate(-1)}
          type="text"
        />
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Product Details</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Card>
          <Title level={4}>Product {id}</Title>
        </Card>
      </Content>
    </Layout>
  );
}
