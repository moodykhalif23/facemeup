import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Descriptions, Tag, Space, Progress } from 'antd';
import { ShopOutlined } from '@ant-design/icons';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Results() {
  const navigate = useNavigate();
  const { currentAnalysis } = useSelector((state) => state.analysis);

  if (!currentAnalysis) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <AppHeader title="Analysis Results" showBack />
        <Content style={{ 
          padding: '24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center' 
        }}>
          <Card style={{ borderRadius: 16, textAlign: 'center' }}>
            <Title level={4}>No analysis data available</Title>
            <Button 
              type="primary" 
              onClick={() => navigate('/analysis')}
              size="large"
              style={{ marginTop: 16, borderRadius: 8 }}
            >
              Start New Analysis
            </Button>
          </Card>
        </Content>
      </Layout>
    );
  }

  const { profile } = currentAnalysis;

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <AppHeader title="Analysis Results" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* Skin Profile - No Card Background */}
            <div>
              <Title level={4} style={{ marginBottom: 16, textAlign: 'center' }}>Skin Profile</Title>
              <div style={{ 
                background: '#fff',
                borderRadius: 12,
                overflow: 'hidden',
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
              }}>
                {/* Skin Type */}
                <div style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15 }}>Skin Type</Text>
                  <div style={{ flex: 1 }}>
                    <Tag color="blue" style={{ fontSize: 14, padding: '6px 16px', margin: 0 }}>
                      {profile.skin_type}
                    </Tag>
                  </div>
                </div>

                {/* Conditions */}
                <div style={{ 
                  display: 'flex',
                  padding: '16px',
                  borderBottom: '1px solid #f0f0f0'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15 }}>Conditions</Text>
                  <div style={{ flex: 1 }}>
                    <Space wrap size={[8, 8]}>
                      {profile.conditions?.map((condition, index) => (
                        <Tag key={index} color="orange" style={{ fontSize: 13, padding: '4px 12px', margin: 0 }}>
                          {condition}
                        </Tag>
                      ))}
                    </Space>
                  </div>
                </div>

                {/* Confidence */}
                <div style={{ 
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15 }}>Confidence</Text>
                  <div style={{ flex: 1, paddingRight: 8 }}>
                    <Progress 
                      percent={Math.round((profile.confidence || 0.85) * 100)} 
                      status="active"
                      strokeColor="#3B82F6"
                      style={{ margin: 0 }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {profile.recommendations && (
              <Card style={{ borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)' }}>
                <Title level={4} style={{ marginBottom: 16 }}>Recommendations</Title>
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {profile.recommendations.map((rec, index) => (
                    <Card 
                      key={index} 
                      type="inner" 
                      size="small"
                      style={{ borderRadius: 8 }}
                    >
                      <Text strong style={{ fontSize: 15 }}>
                        {rec.category || 'General'}
                      </Text>
                      <br />
                      <Text style={{ fontSize: 14, color: '#666' }}>
                        {rec.advice || rec}
                      </Text>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Button 
                type="primary" 
                icon={<ShopOutlined />}
                onClick={() => navigate('/recommendations')}
                size="large"
                block
                style={{
                  height: 56,
                  fontSize: 16,
                  fontWeight: 600,
                  borderRadius: 12
                }}
              >
                View Product Recommendations
              </Button>
              <Button 
                onClick={() => navigate('/analysis')}
                size="large"
                block
                style={{
                  height: 48,
                  fontSize: 15,
                  borderRadius: 12
                }}
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
