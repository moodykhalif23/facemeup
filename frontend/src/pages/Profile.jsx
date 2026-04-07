import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import {
  Layout, Card, Button, Typography, Timeline, Tag,
  App, Spin, Space, Tooltip,
} from 'antd';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { getProfile, submitAnalysisFeedback } from '../services/api';
import AppHeader from '../components/AppHeader';

const { Content } = Layout;
const { Text } = Typography;

export default function Profile() {
  const navigate = useNavigate();
  const { user } = useSelector((state) => state.auth);
  const { message } = App.useApp();

  const [loading, setLoading]           = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [feedbackMap, setFeedbackMap]   = useState({});
  const [submitting, setSubmitting]     = useState({});

  const fetchProfile = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const response = await getProfile(user.id);
      const items = (response.data?.history ?? [])
        .slice()
        .sort((a, b) => new Date(b.created_at ?? 0) - new Date(a.created_at ?? 0));
      setHistoryItems(items);

      // Pre-populate feedbackMap from existing feedback stored in DB
      const map = {};
      items.forEach((item) => {
        if (item.user_feedback) map[item.id] = item.user_feedback;
      });
      setFeedbackMap(map);
    } catch {
      message.error('Failed to load profile history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProfile(); }, [user]);

  const handleFeedback = async (profileId, confirmed) => {
    setSubmitting((prev) => ({ ...prev, [profileId]: true }));
    try {
      await submitAnalysisFeedback(profileId, confirmed);
      setFeedbackMap((prev) => ({
        ...prev,
        [profileId]: confirmed ? 'confirmed' : 'rejected',
      }));
      message.success(confirmed ? 'Result confirmed — thank you!' : 'Feedback recorded');
    } catch {
      message.error('Could not save feedback');
    } finally {
      setSubmitting((prev) => ({ ...prev, [profileId]: false }));
    }
  };

  const timelineItems = historyItems.map((item) => {
    const conditions = Array.isArray(item.conditions)
      ? item.conditions.filter(Boolean)
      : [];
    const feedback = feedbackMap[item.id];
    const isBusy   = !!submitting[item.id];

    return {
      key: item.id,
      dot: (
        <ClockCircleOutlined 
          style={{ 
            color: 'var(--primary)',
            fontSize: 16,
            background: 'transparent',
            border: 'none',
            padding: 0,
          }} 
        />
      ),
      children: (
        <Card
          size="small"
          style={{
            marginBottom: 16,
            border: '1px solid var(--border)',
            background: 'var(--muted)',
            borderRadius: 4,
          }}
        >
          <div style={{ marginBottom: 6 }}>
            <Text strong style={{ color: 'var(--card-foreground)' }}>Skin Type: </Text>
            <Tag color="orange">{item.skin_type}</Tag>
          </div>

          <div style={{ marginBottom: 6 }}>
            <Text strong style={{ color: 'var(--card-foreground)' }}>Conditions: </Text>
            <Space wrap size={4}>
              {conditions.length > 0
                ? conditions.map((c) => <Tag key={c} color="blue">{c}</Tag>)
                : <Tag>None detected</Tag>}
            </Space>
          </div>

          <div style={{ marginBottom: 10 }}>
            <Text style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>
              {new Date(item.created_at ?? item.timestamp).toLocaleString()}
              {item.inference_mode && (
                <span style={{ marginLeft: 8, opacity: 0.6 }}>
                  · {item.inference_mode}
                </span>
              )}
            </Text>
          </div>

          {/* Feedback buttons — spec §9 continuous learning */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8 }}>
            {feedback ? (
              <Tag
                color={feedback === 'confirmed' ? 'success' : 'error'}
                icon={feedback === 'confirmed' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              >
                {feedback === 'confirmed' ? 'You confirmed this result' : 'You flagged this result'}
              </Tag>
            ) : (
              <Space size={6}>
                <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>
                  Was this accurate?
                </Text>
                <Tooltip title="Yes, this is accurate">
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    loading={isBusy}
                    onClick={() => handleFeedback(item.id, true)}
                    style={{ fontSize: 12 }}
                  >
                    Yes
                  </Button>
                </Tooltip>
                <Tooltip title="No, this was wrong">
                  <Button
                    size="small"
                    danger
                    icon={<CloseCircleOutlined />}
                    loading={isBusy}
                    onClick={() => handleFeedback(item.id, false)}
                    style={{ fontSize: 12 }}
                  >
                    No
                  </Button>
                </Tooltip>
              </Space>
            )}
          </div>
        </Card>
      ),
    };
  });

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Profile History" />

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : historyItems.length > 0 ? (
            <Timeline items={timelineItems} />
          ) : (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Text style={{ color: 'var(--muted-foreground)' }}>No analysis history yet</Text>
              <br /><br />
              <Button type="primary" onClick={() => navigate('/analysis')}>
                Start Your First Analysis
              </Button>
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
}
