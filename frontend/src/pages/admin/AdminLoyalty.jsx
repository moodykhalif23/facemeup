import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, InputNumber, Input, Select,
  Tag, Typography, App, Space, Avatar,
} from 'antd';
import { PlusOutlined, MinusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetUsers, awardPoints } from '../../services/api';

const { Title, Text } = Typography;

const TIER = (pts) => {
  if (pts >= 2000) return { label: 'Platinum', color: '#7c3aed' };
  if (pts >= 1000) return { label: 'Gold', color: '#d97706' };
  if (pts >= 500)  return { label: 'Silver', color: '#6b7280' };
  return { label: 'Bronze', color: '#92400e' };
};

const PRESET_REASONS = [
  'Purchase reward',
  'Referral bonus',
  'Review reward',
  'Birthday bonus',
  'Redemption',
  'Manual adjustment',
];

export default function AdminLoyalty() {
  const { message } = App.useApp();
  const [users, setUsers] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  // We fetch users and derive loyalty balances from them
  // In a full impl this would be a dedicated endpoint; here we use user list + note
  const load = () => {
    setLoading(true);
    adminGetUsers()
      .then((r) => { setUsers(r.data.users); setFiltered(r.data.users); })
      .catch(() => message.error('Failed to load users'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(q ? users.filter((u) => u.email.toLowerCase().includes(q)) : users);
  }, [search, users]);

  const openModal = (user, isEarn) => {
    setSelectedUser(user);
    form.setFieldsValue({ points: isEarn ? 100 : -100, reason: isEarn ? 'Purchase reward' : 'Redemption' });
    setModalOpen(true);
  };

  const handleSubmit = async ({ points, reason }) => {
    setSaving(true);
    try {
      await awardPoints(selectedUser.id, points, reason);
      message.success(`${Math.abs(points)} points ${points > 0 ? 'awarded to' : 'deducted from'} ${selectedUser.email}`);
      setModalOpen(false);
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Failed to update points');
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_, r) => (
        <Space>
          <Avatar size={30} style={{ background: 'var(--primary)', color: '#fff', fontSize: 12, fontWeight: 600 }}>
            {r.email[0].toUpperCase()}
          </Avatar>
          <div>
            <Text style={{ display: 'block', color: 'var(--foreground)', fontSize: 13 }}>
              {r.full_name ?? '—'}
            </Text>
            <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{r.email}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      width: 90,
      render: (v) => <Tag color={v === 'admin' ? 'red' : v === 'advisor' ? 'orange' : 'blue'}>{v}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal(record, true)}
          >
            Award
          </Button>
          <Button
            size="small"
            danger
            icon={<MinusOutlined />}
            onClick={() => openModal(record, false)}
          >
            Deduct
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <AdminLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: 'var(--foreground)' }}>Loyalty Points</Title>
        <Space>
          <Input
            prefix={<SearchOutlined />}
            placeholder="Search users"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 220 }}
            allowClear
          />
          <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
        </Space>
      </div>

      {/* Tier reference */}
      <div style={{
        display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap',
      }}>
        {[
          { label: 'Bronze', range: '0–499 pts', color: '#92400e' },
          { label: 'Silver', range: '500–999 pts', color: '#6b7280' },
          { label: 'Gold', range: '1 000–1 999 pts', color: '#d97706' },
          { label: 'Platinum', range: '2 000+ pts', color: '#7c3aed' },
        ].map((t) => (
          <div key={t.label} style={{
            background: 'var(--card)',
            border: `1px solid ${t.color}44`,
            borderRadius: 8,
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: t.color }} />
            <Text strong style={{ color: t.color, fontSize: 13 }}>{t.label}</Text>
            <Text style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>{t.range}</Text>
          </div>
        ))}
      </div>

      <div style={{ background: 'var(--card)', borderRadius: 10, border: '1px solid var(--border)', overflow: 'hidden' }}>
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

      <Modal
        title={`${(form.getFieldValue('points') ?? 0) > 0 ? 'Award' : 'Deduct'} Points — ${selectedUser?.email}`}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText="Confirm"
        confirmLoading={saving}
      >
        {modalOpen && (
          <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ marginTop: 16 }}>
            <Form.Item
              label="Points (use negative to deduct)"
              name="points"
              rules={[{ required: true }, { type: 'number', message: 'Enter a number' }]}
            >
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="Reason" name="reason" rules={[{ required: true }]}>
              <Select
                options={PRESET_REASONS.map((r) => ({ label: r, value: r }))}
                allowClear
                showSearch
                placeholder="Select or type a reason"
              />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </AdminLayout>
  );
}
