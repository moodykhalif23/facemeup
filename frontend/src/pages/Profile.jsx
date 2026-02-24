import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Layout, Card, Button, Typography, Timeline, Tag, message, Spin } from 'antd';
import { ArrowLeftOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { getProfile } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const { user } = useSelector((state) => state.auth);
  const { history } = useSelector((state) => state.analysis);

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
        <Title level={3} style={{ margin: '0 0 0 16px' }}>Profile History</Title>
      </Header>

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : (
            <Card>
              <Title level={4}>Analysis History</Title>
              {history.length > 0 ? (
                <Timeline>
                  {history.map((item, index) => (
                    <Timeline.Item 
                      key={index}
                      dot={<ClockCircleOutlined />}
                    >
                      <Card size="small" style={{ marginBottom: 16 }}>
                        <Text strong>Skin Type: </Text>
                        <Tag color="blue">{item.profile?.skin_type}</Tag>
                        <br />
                        <Text strong>Conditions: </Text>
                        {item.profile?.conditions?.map((c, i) => (
                          <Tag key={i} color="orange">{c}</Tag>
                        ))}
                        <br />
                        <Text type="secondary">
                          {new Date(item.timestamp || Date.now()).toLocaleDateString()}
                        </Text>
                      </Card>
                    </Timeline.Item>
                  ))}
                </Timeline>
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  <Text type="secondary">No analysis history yet</Text>
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
