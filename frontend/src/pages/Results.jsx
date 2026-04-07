import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Tag, Space, Progress } from 'antd';
import { ShopOutlined } from '@ant-design/icons';
import AppHeader from '../components/AppHeader';
import SkinCharts from '../components/SkinCharts';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Results() {
  const navigate = useNavigate();
  const { currentAnalysis } = useSelector((state) => state.analysis);

  if (!currentAnalysis) {
    return (
      <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
        <AppHeader title="Analysis Results" showBack />
        <Content style={{
          padding: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Card style={{
            borderRadius: 6,
            textAlign: 'center',
            border: '1px solid var(--border)',
            background: 'var(--card)',
          }}>
            <Title level={4} style={{ color: 'var(--card-foreground)' }}>No analysis data available</Title>
            <Button
              type="primary"
              onClick={() => navigate('/analysis')}
              size="large"
              style={{ marginTop: 16 }}
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
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Analysis Results" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* Skin Profile */}
            <div>
              <div style={{
                background: 'var(--card)',
                borderRadius: 6,
                overflow: 'hidden',
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px',
                  borderBottom: '1px solid var(--border)'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15, color: 'var(--card-foreground)' }}>
                    Skin Type
                  </Text>
                  <div style={{ flex: 1 }}>
                    <Tag color="orange" style={{ fontSize: 14, padding: '6px 16px', margin: 0 }}>
                      {profile.skin_type}
                    </Tag>
                  </div>
                </div>

                <div style={{
                  display: 'flex',
                  padding: '16px',
                  borderBottom: '1px solid var(--border)'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15, color: 'var(--card-foreground)' }}>
                    Conditions
                  </Text>
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

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '16px'
                }}>
                  <Text strong style={{ flex: '0 0 120px', fontSize: 15, color: 'var(--card-foreground)' }}>
                    Confidence
                  </Text>
                  <div style={{ flex: 1, paddingRight: 8 }}>
                    <Progress
                      percent={Math.round((profile.confidence || 0.85) * 100)}
                      status="active"
                      strokeColor="var(--primary)"
                      style={{ margin: 0 }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {profile.recommendations && (
              <Card style={{
                borderRadius: 6,
                boxShadow: 'var(--card-shadow)',
                border: '1px solid var(--border)',
                background: 'var(--card)',
              }}>
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {profile.recommendations.map((rec, index) => (
                    <Card
                      key={index}
                      type="inner"
                      size="small"
                      style={{ borderRadius: 6, border: '1px solid var(--border)' }}
                    >
                      <Text strong style={{ fontSize: 15, color: 'var(--card-foreground)' }}>
                        {rec.category || 'General'}
                      </Text>
                      <br />
                      <Text style={{ fontSize: 14, color: 'var(--muted-foreground)' }}>
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
                style={{ height: 56, fontSize: 16, fontWeight: 600 }}
              >
                View Product Recommendations
              </Button>
              <Button
                onClick={() => navigate('/analysis')}
                size="large"
                block
                style={{ height: 48, fontSize: 15 }}
              >
                New Analysis
              </Button>
            </Space>

            {/* ── Visualisation breakdown (ECharts) ── */}
            <SkinCharts profile={profile} />
          </Space>
        </div>
      </Content>
    </Layout>
  );
}

