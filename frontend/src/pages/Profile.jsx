import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Timeline, Tag, App, Spin } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';
import { getProfile } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Title, Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const { user } = useSelector((state) => state.auth);
  const { history } = useSelector((state) => state.analysis);
  const { message } = App.useApp();

  useEffect(() => {
    if (user?.id) {
      fetchProfile();
    }
  }, [user]);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await getProfile(user.id);
      setProfileData(response.data);
    } catch (error) {
      message.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Profile History" showBack />

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : (
            <Card style={{
              borderRadius: 12,
              border: '1px solid var(--border)',
              background: 'var(--card)',
              boxShadow: 'var(--card-shadow)',
            }}>
              <Title level={4} style={{ color: 'var(--card-foreground)', marginBottom: 16 }}>
                Analysis History
              </Title>
              {history.length > 0 ? (
                <Timeline>
                  {history.map((item, index) => (
                    <Timeline.Item
                      key={index}
                      dot={<ClockCircleOutlined style={{ color: 'var(--primary)' }} />}
                    >
                      <Card size="small" style={{
                        marginBottom: 16,
                        border: '1px solid var(--border)',
                        background: 'var(--muted)',
                        borderRadius: 8,
                      }}>
                        <Text strong style={{ color: 'var(--card-foreground)' }}>Skin Type: </Text>
                        <Tag color="orange">{item.profile?.skin_type}</Tag>
                        <br />
                        <Text strong style={{ color: 'var(--card-foreground)' }}>Conditions: </Text>
                        {item.profile?.conditions?.map((c, i) => (
                          <Tag key={i} color="orange">{c}</Tag>
                        ))}
                        <br />
                        <Text style={{ color: 'var(--muted-foreground)', fontSize: 13 }}>
                          {new Date(item.timestamp || Date.now()).toLocaleDateString()}
                        </Text>
                      </Card>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  <Text style={{ color: 'var(--muted-foreground)' }}>No analysis history yet</Text>
                  <br /><br />
                  <Button type="primary" onClick={() => navigate('/analysis')}>
                    Start Your First Analysis
                  </Button>
                </div>
              )}
            </Card>
          )}
        </div>
      </Content>
    </Layout>
  );
}
