import { useEffect, useState } from 'react';
import {
  Table, Button, Space, Popconfirm,
  Typography, App, Input, Avatar, Tooltip,
} from 'antd';
import { DeleteOutlined, ReloadOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetUsers, adminDeleteUser } from '../../services/api';

const { Text } = Typography;

export default function AdminUsers() {
  const { message } = App.useApp();
  const [users, setUsers] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

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
      width: 60,
      render: (_, record) =>
        (
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
    </AdminLayout>
  );
}
