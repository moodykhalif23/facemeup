import { useEffect, useState } from 'react';
import {
  Table, Button, Space, Popconfirm,
  Typography, App, Input, Avatar, Tooltip, Drawer, Tag, Divider, Spin,
} from 'antd';
import { DeleteOutlined, ReloadOutlined, SearchOutlined, UserOutlined, EyeOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetUsers, adminDeleteUser, adminGetUserReports } from '../../services/api';

const { Text } = Typography;

export default function AdminUsers() {
  const { message } = App.useApp();
  const [users, setUsers] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [drawerUser, setDrawerUser] = useState(null);
  const [drawerHistory, setDrawerHistory] = useState([]);
  const [drawerLoading, setDrawerLoading] = useState(false);

  const load = () => {
    setLoading(true);
    adminGetUsers()
      .then((r) => {
        const nonAdmins = (r.data.users ?? []).filter((u) => u.role !== 'admin');
        setUsers(nonAdmins);
        setFiltered(nonAdmins);
      })
      .catch(() => message.error('Failed to load users'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(
      q ? users.filter((u) => u.email.toLowerCase().includes(q) || (u.full_name ?? '').toLowerCase().includes(q)) : users
    );
  }, [search, users]);

  const openReports = async (user) => {
    setDrawerUser(user);
    setDrawerHistory([]);
    setDrawerLoading(true);
    try {
      const r = await adminGetUserReports(user.id);
      setDrawerHistory(r.data.history || []);
    } catch {
      message.error('Failed to load user reports');
    } finally {
      setDrawerLoading(false);
    }
  };

  const deleteUser = async (userId) => {
    try {
      await adminDeleteUser(userId);
      message.success('User deleted');
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Delete failed');
    }
  };

  const columns = [
    {
      title: 'Client',
      key: 'user',
      render: (_, r) => (
        <Space>
          <Avatar
            size={32}
            style={{ background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 600 }}
          >
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
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (v) => new Date(v).toLocaleDateString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      responsive: ['sm'],
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="View reports">
            <Button type="text" icon={<EyeOutlined />} size="small" onClick={() => openReports(record)} />
          </Tooltip>
          <Popconfirm
            title="Delete this user?"
            description="All their data will be permanently removed."
            onConfirm={() => deleteUser(record.id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Delete user">
              <Button type="text" danger icon={<DeleteOutlined />} size="small" />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <AdminLayout>
      <div style={{
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        marginBottom: 20,
        gap: 12,
        flexWrap: 'wrap',
      }}>
        <Space style={{ width: '100%', maxWidth: 420 }}>
          <Input
            prefix={<SearchOutlined />}
            placeholder="Search by email or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%' }}
            allowClear
          />
          <Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button>
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
        title={drawerUser ? `${drawerUser.full_name || drawerUser.email} — Analysis History` : ''}
        open={!!drawerUser}
        onClose={() => setDrawerUser(null)}
        width={520}
        styles={{
          body: { background: 'var(--background)' },
          header: { background: 'var(--card)', borderBottom: '1px solid var(--border)' },
        }}
      >
        {drawerLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>
        ) : drawerHistory.length === 0 ? (
          <Text style={{ color: 'var(--muted-foreground)' }}>No analysis history for this user.</Text>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {drawerHistory.map((record, idx) => (
              <div key={record.id ?? idx}>
                {idx > 0 && <Divider style={{ borderColor: 'var(--border)', margin: '0 0 16px' }} />}

                {/* Date + skin type */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <Text style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>
                    {new Date(record.created_at).toLocaleString()}
                    {record.inference_mode && (
                      <span style={{ marginLeft: 8, opacity: 0.6 }}>· {record.inference_mode}</span>
                    )}
                  </Text>
                  <Tag color="blue">{record.skin_type}</Tag>
                </div>

                {/* Captured poses grid */}
                {record.capture_images?.length > 0 ? (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginBottom: 10 }}>
                    {record.capture_images.map((img, i) => (
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
                        }}
                      />
                    ))}
                  </div>
                ) : record.report_image_base64 ? (
                  <img
                    src={record.report_image_base64}
                    alt="Analysis capture"
                    style={{ width: '100%', borderRadius: 6, border: '1px solid var(--border)', marginBottom: 10 }}
                  />
                ) : null}

                {/* Conditions */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {(record.conditions || []).length > 0
                    ? record.conditions.map((c) => <Tag key={c}>{c}</Tag>)
                    : <Text style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>No conditions detected</Text>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Drawer>
    </AdminLayout>
  );
}

