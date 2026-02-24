import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Descriptions, Tag, Space, Progress } from 'antd';
import { ArrowLeftOutlined, ShopOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Results() {
  const navigate = useNavigate();
  const { currentAnalysis } = useSelector((state) => state.analysis);

  if (!currentAnalysis) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Card>
            <Title level={4}>No analysis data available</Title>
            <Button type="primary" onClick={() => navigate('/analysis')}>
              Start New Analysis
            </Button>
          </Card>
        </Content>
      </Layout>
    );
  }

  const { profile } = currentAnalysis;

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
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Analysis Results</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card>
              <Title level={4}>Skin Profile</Title>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Skin Type">
                  <Tag color="blue">{profile.skin_type}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Conditions">
                  <Space wrap>
                    {profile.conditions?.map((condition, index) => (
                      <Tag key={index} color="orange">{condition}</Tag>
                    ))}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Confidence Score">
                  <Progress 
                    percent={Math.round((profile.confidence_score || 0.85) * 100)} 
                    status="active"
                  />
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {profile.recommendations && (
              <Card>
                <Title level={4}>Recommendations</Title>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {profile.recommendations.map((rec, index) => (
                    <Card key={index} type="inner" size="small">
                      <Text strong>{rec.category || 'General'}</Text>
                      <br />
                      <Text>{rec.advice || rec}</Text>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            <Space style={{ width: '100%' }}>
              <Button 
                type="primary" 
                icon={<ShopOutlined />}
                onClick={() => navigate('/recommendations')}
                size="large"
                block
              >
                View Product Recommendations
              </Button>
              <Button 
                onClick={() => navigate('/analysis')}
                size="large"
                block
              >
                New Analysis
              </Button>
            </Space>
          </Space>
        </div>
      </Content>
    </Layout>
  );
}
