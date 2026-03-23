import { useEffect, useMemo, useRef, useState } from 'react';
import { useSelector } from 'react-redux';
import {
  Layout, Card, Typography, Space, Tag, List, Divider, Progress, Drawer, Button, App, DatePicker, Avatar,
} from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import AppHeader from '../components/AppHeader';
import { getProfile } from '../services/api';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const { Content } = Layout;
const { Text, Title } = Typography;
const { RangePicker } = DatePicker;

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
  const [dateRange, setDateRange] = useState(null);
  const reportRef = useRef(null);

  useEffect(() => {
    if (!user?.id) return;
    setLoading(true);
    getProfile(user.id)
      .then((r) => setHistory(r.data.history || []))
      .catch(() => message.error('Failed to load reports'))
      .finally(() => setLoading(false));
  }, [user?.id]);

  const listItems = useMemo(() => {
    let data = history;
    if (dateRange?.[0] && dateRange?.[1]) {
      const start = dateRange[0].startOf('day').toDate();
      const end = dateRange[1].endOf('day').toDate();
      data = data.filter((r) => {
        const t = new Date(r.timestamp);
        return t >= start && t <= end;
      });
    }
    return data.map((h, idx) => ({ ...h, key: idx }));
  }, [history, dateRange]);

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--background)' }}>
      <AppHeader title="Reports" showBack />

      <Content style={{ padding: '16px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div>
            <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'center' }}>
              <RangePicker onChange={(val) => setDateRange(val)} />
            </div>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text style={{ color: 'var(--muted-foreground)' }}>Loading…</Text>
              </div>
            ) : listItems.length === 0 ? (
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
          </div>
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
          <div ref={reportRef}>
            <Card style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}>
              <Space align="start">
                <Avatar
                  size={72}
                  src={selected.report_image_base64 || undefined}
                  style={{ background: 'var(--muted)' }}
                />
                <div>
                  <Text strong style={{ fontSize: 16, color: 'var(--foreground)' }}>
                    {selected.skin_type}
                  </Text>
                  <div style={{ marginTop: 8 }}>
                    <Text style={{ color: 'var(--muted-foreground)' }}>Tested at {formatDateTime(selected.timestamp)}</Text>
                  </div>
                </div>
              </Space>
              <div style={{ marginTop: 8 }}>
                <Text style={{ color: 'var(--muted-foreground)' }}>
                  {selected.questionnaire?.gender ? `Gender: ${selected.questionnaire.gender}` : ''}{' '}
                  {selected.questionnaire?.age ? `Age: ${selected.questionnaire.age}` : ''}
                </Text>
              </div>
              {selected.questionnaire && (
                <div style={{ marginTop: 10 }}>
                  <Text strong style={{ color: 'var(--foreground)' }}>Questionnaire</Text>
                  <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {selected.questionnaire.skin_texture && (
                      <Tag>Texture: {selected.questionnaire.skin_texture}</Tag>
                    )}
                    {selected.questionnaire.moisture_level && (
                      <Tag>Moisture: {selected.questionnaire.moisture_level}</Tag>
                    )}
                    {selected.questionnaire.oil_levels && (
                      <Tag>Oil: {selected.questionnaire.oil_levels}</Tag>
                    )}
                    {selected.questionnaire.routine && (
                      <Tag>Routine: {selected.questionnaire.routine}</Tag>
                    )}
                    {selected.questionnaire.routine_other && (
                      <Tag>Routine notes: {selected.questionnaire.routine_other}</Tag>
                    )}
                    {selected.questionnaire.skin_feel && (
                      <Tag>Feel: {selected.questionnaire.skin_feel}</Tag>
                    )}
                    {(selected.questionnaire.concerns || []).map((c) => (
                      <Tag key={`q-${c}`}>{c}</Tag>
                    ))}
                  </div>
                </div>
              )}
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
        {selected && (
          <div style={{ marginTop: 16 }}>
            <Button
              type="primary"
              onClick={async () => {
                if (!reportRef.current) return;
                const canvas = await html2canvas(reportRef.current, { backgroundColor: '#0b0b0b' });
                const imgData = canvas.toDataURL('image/png');
                const pdf = new jsPDF('p', 'mm', 'a4');
                const pdfWidth = pdf.internal.pageSize.getWidth();
                const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
                pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
                pdf.save('my-report.pdf');
              }}
            >
              Export PDF
            </Button>
          </div>
        )}
      </Drawer>
    </Layout>
  );
}
