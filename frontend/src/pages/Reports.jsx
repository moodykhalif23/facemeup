import { useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import {
  Layout, Card, Typography, Space, Tag, List, Divider, Progress, Drawer, Button, App,
} from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import AppHeader from '../components/AppHeader';
import { getProfile } from '../services/api';

const { Content } = Layout;
const { Text, Title } = Typography;

const formatDateTime = (value) => {
  if (!value) return '—';
  const d = new Date(value);
  return d.toLocaleString();
};

export default function Reports() {
  const { user } = useSelector((state) => state.auth);
  const { message } = App.useApp();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    getProfile(user.id)
      .then((r) => setHistory(r.data.history || []))
      .catch(() => message.error('Failed to load reports'))
      .finally(() => setLoading(false));
  }, [user?.id]);

  const listItems = useMemo(() => history.map((h, idx) => ({ ...h, key: idx })), [history]);

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Reports" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <Card style={{ borderRadius: 12, border: '1px solid var(--border)', background: 'var(--card)' }}>
            <Title level={4} style={{ color: 'var(--card-foreground)', marginTop: 0 }}>
              My Analysis Reports
            </Title>
            <Text style={{ color: 'var(--muted-foreground)' }}>
              View your skin analysis history and detailed reports.
            </Text>
          </Card>

          <Card
            style={{ marginTop: 16, borderRadius: 12, border: '1px solid var(--border)', background: 'var(--card)' }}
            loading={loading}
          >
            {listItems.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text style={{ color: 'var(--muted-foreground)' }}>No reports yet</Text>
              </div>
            ) : (
              <List
                dataSource={listItems}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        key="view"
                        type="link"
                        icon={<EyeOutlined />}
                        onClick={() => { setSelected(item); setDrawerOpen(true); }}
                      >
                        View
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={(
                        <Space size={8} wrap>
                          <Text strong style={{ color: 'var(--card-foreground)' }}>{item.skin_type}</Text>
                          {(item.conditions || []).map((c) => <Tag key={c}>{c}</Tag>)}
                        </Space>
                      )}
                      description={(
                        <Text style={{ color: 'var(--muted-foreground)' }}>
                          {formatDateTime(item.timestamp)}
                        </Text>
                      )}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </div>
      </Content>

      <Drawer
        title="Report Details"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={520}
        styles={{
          body: { background: 'var(--background)' },
          header: { background: 'var(--card)', borderBottom: '1px solid var(--border)' },
        }}
      >
        {selected && (
          <div>
            <Card style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}>
              <Text strong style={{ fontSize: 16, color: 'var(--foreground)' }}>
                {selected.skin_type}
              </Text>
              <div style={{ marginTop: 8 }}>
                <Text style={{ color: 'var(--muted-foreground)' }}>Tested at {formatDateTime(selected.timestamp)}</Text>
              </div>
              <Divider style={{ borderColor: 'var(--border)' }} />
              <Text strong style={{ color: 'var(--foreground)' }}>Conditions</Text>
              <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {(selected.conditions || []).length > 0
                  ? selected.conditions.map((c) => <Tag key={c}>{c}</Tag>)
                  : <Text type="secondary">None detected</Text>}
              </div>
              <Divider style={{ borderColor: 'var(--border)' }} />
              <Text strong style={{ color: 'var(--foreground)' }}>Confidence</Text>
              <Progress percent={Math.round((selected.confidence ?? 0) * 100)} strokeColor="var(--primary)" />
            </Card>

            {(selected.skin_type_scores || selected.condition_scores) && (
              <>
                <Divider style={{ borderColor: 'var(--border)' }} />
                <Card style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}>
                  <Text strong style={{ color: 'var(--foreground)' }}>Score Breakdown</Text>
                  <div style={{ marginTop: 10 }}>
                    {selected.skin_type_scores && (
                      <>
                        <Text style={{ color: 'var(--muted-foreground)' }}>Skin Type Scores</Text>
                        <div style={{ marginTop: 6 }}>
                          {Object.entries(selected.skin_type_scores).map(([k, v]) => (
                            <div key={k} style={{ marginBottom: 6 }}>
                              <Text style={{ fontSize: 12, color: 'var(--foreground)' }}>{k}</Text>
                              <Progress percent={Math.round(v * 100)} size="small" />
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                    {selected.condition_scores && (
                      <>
                        <Divider style={{ borderColor: 'var(--border)' }} />
                        <Text style={{ color: 'var(--muted-foreground)' }}>Condition Scores</Text>
                        <div style={{ marginTop: 6 }}>
                          {Object.entries(selected.condition_scores).map(([k, v]) => (
                            <div key={k} style={{ marginBottom: 6 }}>
                              <Text style={{ fontSize: 12, color: 'var(--foreground)' }}>{k}</Text>
                              <Progress percent={Math.round(v * 100)} size="small" />
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </Card>
              </>
            )}
          </div>
        )}
      </Drawer>
    </Layout>
  );
}
