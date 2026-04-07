import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Table, Card, Typography, Space, Input, Tag, Avatar, Button, Drawer, Divider, Progress, App, DatePicker, Popconfirm,
} from 'antd';
import { SearchOutlined, EyeOutlined, UserOutlined, DeleteOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetReports, adminDeleteReport } from '../../services/api';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const { Text } = Typography;
const { RangePicker } = DatePicker;

const formatDateTime = (value) => {
  if (!value) return '—';
  const d = new Date(value);
  return d.toLocaleString();
};

const prettyGender = (value) => {
  if (!value) return '—';
  return value.charAt(0).toUpperCase() + value.slice(1);
};

export default function AdminReports() {
  const { message } = App.useApp();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [dateRange, setDateRange] = useState(null);
  const reportRef = useRef(null);

  const load = () => {
    setLoading(true);
    adminGetReports()
      .then((r) => setReports(r.data.reports || []))
      .catch(() => message.error('Failed to load reports'))
      .finally(() => setLoading(false));
  };

  const handleDelete = async (reportId) => {
    try {
      await adminDeleteReport(reportId);
      message.success('Report deleted');
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      if (selected?.id === reportId) setDrawerOpen(false);
    } catch {
      message.error('Failed to delete report');
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let data = reports;
    if (dateRange?.[0] && dateRange?.[1]) {
      const start = dateRange[0].startOf('day').toDate();
      const end = dateRange[1].endOf('day').toDate();
      data = data.filter((r) => {
        const t = new Date(r.created_at);
        return t >= start && t <= end;
      });
    }
    if (!q) return data;
    return data.filter((r) => {
      const questionnaire = r.questionnaire || {};
      const concerns = Array.isArray(questionnaire.concerns) ? questionnaire.concerns : [];
      const target = [
        r.email,
        r.full_name,
        r.skin_type,
        ...(r.conditions || []),
        r.inference_mode,
        questionnaire.skin_texture,
        questionnaire.moisture_level,
        questionnaire.oil_levels,
        questionnaire.routine,
        questionnaire.routine_other,
        questionnaire.skin_feel,
        questionnaire.gender,
        questionnaire.age,
        ...concerns,
      ].filter(Boolean).join(' ').toLowerCase();
      return target.includes(q);
    });
  }, [reports, search, dateRange]);

  const columns = [
    {
      title: 'Photo',
      key: 'photo',
      width: 70,
      render: (_, r) => (
        <Avatar
          size={40}
          src={r.report_image_base64 || undefined}
          icon={<UserOutlined />}
          style={{ background: 'var(--muted)' }}
        />
      ),
    },
    {
      title: 'Customer',
      key: 'customer',
      render: (_, r) => (
        <div>
          <Text style={{ display: 'block', color: 'var(--foreground)', fontSize: 13 }}>
            {r.full_name || 'Unknown'}
          </Text>
          <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{r.email}</Text>
        </div>
      ),
    },
    {
      title: 'Gender',
      dataIndex: 'questionnaire',
      key: 'gender',
      width: 90,
      render: (q) => prettyGender(q?.gender),
      responsive: ['sm'],
    },
    {
      title: 'Age',
      dataIndex: 'questionnaire',
      key: 'age',
      width: 70,
      render: (q) => q?.age ?? '—',
      responsive: ['sm'],
    },
    {
      title: 'Skin Type',
      dataIndex: 'skin_type',
      key: 'skin_type',
      width: 120,
      render: (v) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: 'Conditions',
      dataIndex: 'conditions',
      key: 'conditions',
      render: (list) => (
        <Space size={[4, 4]} wrap>
          {(list || []).length > 0 ? list.map((c) => <Tag key={c}>{c}</Tag>) : <Text type="secondary">—</Text>}
        </Space>
      ),
    },
    {
      title: 'Test Time',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (v) => formatDateTime(v),
      responsive: ['md'],
    },
    {
      title: 'Action',
      key: 'action',
      width: 120,
      render: (_, r) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => { setSelected(r); setDrawerOpen(true); }}
          >
            View
          </Button>
          <Popconfirm
            title="Delete this report?"
            description="This cannot be undone."
            onConfirm={() => handleDelete(r.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
          >
            <Button type="text" danger icon={<DeleteOutlined />} size="small" />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <AdminLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 12, flexWrap: 'wrap' }}>
        <Space wrap>
          <Input
            prefix={<SearchOutlined />}
            placeholder="Search by name, email, skin type, condition..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
            style={{ width: 320 }}
          />
          <RangePicker
            onChange={(val) => setDateRange(val)}
            style={{ minWidth: 260 }}
          />
        </Space>
      </div>

      <div style={{ background: 'var(--card)', borderRadius: 6, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{ pageSize: 20 }}
          style={{ background: 'transparent' }}
        />
      </div>

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
          <div ref={reportRef} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── Customer header ── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Avatar
                size={52}
                src={selected.report_image_base64 || undefined}
                icon={<UserOutlined />}
                style={{ background: 'var(--primary)', flexShrink: 0 }}
              />
              <div>
                <Text strong style={{ display: 'block', color: 'var(--foreground)', fontSize: 15 }}>
                  {selected.full_name || 'Unknown'}
                </Text>
                <Text style={{ color: 'var(--muted-foreground)', fontSize: 13 }}>{selected.email}</Text>
                <Text style={{ display: 'block', color: 'var(--muted-foreground)', fontSize: 12, marginTop: 2 }}>
                  {formatDateTime(selected.created_at)}
                </Text>
              </div>
            </div>

            {/* ── Captured poses grid ── */}
            {(selected.capture_images?.length > 0) ? (
              <div>
                <Text strong style={{ color: 'var(--foreground)', fontSize: 13, display: 'block', marginBottom: 8 }}>
                  Captured Poses ({selected.capture_images.length})
                </Text>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
                  {selected.capture_images.map((img, i) => (
                    <img
                      key={i}
                      src={img}
                      alt={`Pose ${i + 1}`}
                      style={{
                        width: '100%',
                        aspectRatio: '1',
                        objectFit: 'cover',
                        borderRadius: 6,
                        border: '1px solid var(--border)',
                        display: 'block',
                      }}
                    />
                  ))}
                </div>
              </div>
            ) : selected.report_image_base64 ? (
              <img
                src={selected.report_image_base64}
                alt="Analysis capture"
                style={{ width: '100%', borderRadius: 6, border: '1px solid var(--border)' }}
              />
            ) : null}

            <Divider style={{ borderColor: 'var(--border)', margin: '4px 0' }} />

            {/* ── Skin result ── */}
            <div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                <Tag color="blue">{selected.skin_type}</Tag>
                {selected.questionnaire?.gender && <Tag>{prettyGender(selected.questionnaire.gender)}</Tag>}
                {selected.questionnaire?.age && <Tag>Age {selected.questionnaire.age}</Tag>}
              </div>
              <Text strong style={{ color: 'var(--foreground)', fontSize: 13 }}>Conditions</Text>
              <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {(selected.conditions || []).length > 0
                  ? selected.conditions.map((c) => <Tag key={c}>{c}</Tag>)
                  : <Text type="secondary">None detected</Text>}
              </div>
            </div>

            {/* ── Questionnaire ── */}
            {selected.questionnaire && (
              <div>
                <Text strong style={{ color: 'var(--foreground)', fontSize: 13 }}>Questionnaire</Text>
                <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {selected.questionnaire.skin_texture && <Tag>Texture: {selected.questionnaire.skin_texture}</Tag>}
                  {selected.questionnaire.moisture_level && <Tag>Moisture: {selected.questionnaire.moisture_level}</Tag>}
                  {selected.questionnaire.oil_levels && <Tag>Oil: {selected.questionnaire.oil_levels}</Tag>}
                  {selected.questionnaire.routine && <Tag>Routine: {selected.questionnaire.routine}</Tag>}
                  {selected.questionnaire.routine_other && <Tag>Notes: {selected.questionnaire.routine_other}</Tag>}
                  {selected.questionnaire.skin_feel && <Tag>Feel: {selected.questionnaire.skin_feel}</Tag>}
                  {(selected.questionnaire.concerns || []).map((c) => <Tag key={`q-${c}`}>{c}</Tag>)}
                </div>
              </div>
            )}

            {/* ── Score breakdown ── */}
            {(selected.skin_type_scores || selected.condition_scores) && (
              <div>
                <Divider style={{ borderColor: 'var(--border)', margin: '4px 0' }} />
                {selected.skin_type_scores && (
                  <>
                    <Text strong style={{ color: 'var(--foreground)', fontSize: 13 }}>Skin Type Scores</Text>
                    <div style={{ marginTop: 6, marginBottom: 12 }}>
                      {Object.entries(selected.skin_type_scores).map(([k, v]) => (
                        <div key={k} style={{ marginBottom: 4 }}>
                          <Text style={{ fontSize: 12, color: 'var(--foreground)' }}>{k}</Text>
                          <Progress percent={Math.round(v * 100)} size="small" />
                        </div>
                      ))}
                    </div>
                  </>
                )}
                {selected.condition_scores && (
                  <>
                    <Text strong style={{ color: 'var(--foreground)', fontSize: 13 }}>Condition Scores</Text>
                    <div style={{ marginTop: 6 }}>
                      {Object.entries(selected.condition_scores).map(([k, v]) => (
                        <div key={k} style={{ marginBottom: 4 }}>
                          <Text style={{ fontSize: 12, color: 'var(--foreground)' }}>{k}</Text>
                          <Progress percent={Math.round(v * 100)} size="small" />
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
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
                pdf.save(`report-${selected.id}.pdf`);
              }}
            >
              Export PDF
            </Button>
          </div>
        )}
      </Drawer>
    </AdminLayout>
  );
}

