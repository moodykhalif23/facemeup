import { useEffect, useState } from 'react';
import {
  Table, Button, Select, Space, Popconfirm, Tag,
  Typography, App, Input, Avatar, Tooltip,
} from 'antd';
import { DeleteOutlined, ReloadOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetUsers, adminUpdateUserRole, adminDeleteUser } from '../../services/api';
import { useSelector } from 'react-redux';

const { Title, Text } = Typography;

const ROLE_COLOR = { admin: 'red', advisor: 'orange', customer: 'blue' };
const ROLES = ['customer', 'advisor', 'admin'];

export default function AdminUsers() {
  const { message } = App.useApp();
  const { user: me } = useSelector((s) => s.auth);
  const [users, setUsers] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

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
    setFiltered(
      q ? users.filter((u) => u.email.toLowerCase().includes(q) || (u.full_name ?? '').toLowerCase().includes(q)) : users
    );
  }, [search, users]);

  const changeRole = async (userId, role) => {
    try {
      await adminUpdateUserRole(userId, role);
      message.success('Role updated');
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Update failed');
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
      title: 'User',
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
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      width: 160,
      filters: ROLES.map((r) => ({ text: r, value: r })),
      onFilter: (value, record) => record.role === value,
      render: (role, record) =>
        record.id === me?.id ? (
          <Tag color={ROLE_COLOR[role]}>{role}</Tag>
        ) : (
          <Select
            value={role}
            size="small"
            style={{ width: 120 }}
            onChange={(val) => changeRole(record.id, val)}
            options={ROLES.map((r) => ({ label: r, value: r }))}
          />
        ),
    },
    {
      title: 'Joined',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (v) => new Date(v).toLocaleDateString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_, record) =>
        record.id === me?.id ? null : (
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <Title level={4} style={{ margin: 0, color: 'var(--foreground)' }}>Users</Title>
        <Space>
          <Input
            prefix={<SearchOutlined />}
            placeholder="Search by email or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240 }}
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
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell colSpan={4}>
                <Text style={{ color: 'var(--muted-foreground)', fontSize: 12 }}>
                  {filtered.length} user{filtered.length !== 1 ? 's' : ''}
                </Text>
              </Table.Summary.Cell>
            </Table.Summary.Row>
          )}
        />
      </div>
    </AdminLayout>
  );
}
