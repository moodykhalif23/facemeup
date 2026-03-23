import { useEffect, useState } from 'react';
import {
  Table, Select, Tag, Typography, App, Space, Button, Input, Descriptions, Modal,
} from 'antd';
import { ReloadOutlined, SearchOutlined, EyeOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminGetOrders, adminUpdateOrderStatus } from '../../services/api';

const { Text } = Typography;

const STATUS_OPTIONS = ['created', 'paid', 'shipped', 'delivered', 'cancelled'];
const STATUS_COLOR = {
  created: 'blue', paid: 'green', shipped: 'cyan', delivered: 'success', cancelled: 'red',
};

export default function AdminOrders() {
  const { message } = App.useApp();
  const [orders, setOrders] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [detail, setDetail] = useState(null);

  const load = () => {
    setLoading(true);
    adminGetOrders()
      .then((r) => { setOrders(r.data.orders); setFiltered(r.data.orders); })
      .catch(() => message.error('Failed to load orders'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(
      q
        ? orders.filter(
            (o) =>
              o.user_email?.toLowerCase().includes(q) ||
              String(o.id).includes(q) ||
              o.order_number?.toLowerCase().includes(q)
          )
        : orders
    );
  }, [search, orders]);

  const updateStatus = async (orderId, status) => {
    try {
      await adminUpdateOrderStatus(orderId, status);
      message.success('Status updated');
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Update failed');
    }
  };

  const columns = [
    {
      title: 'Order #',
      dataIndex: 'order_number',
      key: 'order_number',
      width: 120,
      ellipsis: true,
      render: (v) => <Text code style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{v}</Text>,
    },
    {
      title: 'Customer',
      dataIndex: 'user_email',
      key: 'user_email',
      ellipsis: true,
      responsive: ['sm'],
    },
    {
      title: 'Channel',
      dataIndex: 'channel',
      key: 'channel',
      width: 90,
      render: (v) => <Tag>{v ?? 'web'}</Tag>,
      responsive: ['md'],
    },
    {
      title: 'Items',
      dataIndex: 'items_count',
      key: 'items_count',
      width: 70,
      render: (v) => v ?? '—',
      responsive: ['md'],
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 96,
      align: 'right',
      render: (v) => <Text style={{ whiteSpace: 'nowrap' }}>{`KES ${(v ?? 0).toLocaleString()}`}</Text>,
      sorter: (a, b) => a.total - b.total,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 160,
      filters: STATUS_OPTIONS.map((s) => ({ text: s, value: s })),
      onFilter: (value, record) => record.status === value,
      render: (status, record) => (
        <Select
          value={status}
          size="small"
          style={{ width: 130 }}
          onChange={(val) => updateStatus(record.id, val)}
          options={STATUS_OPTIONS.map((s) => ({
            label: <Tag color={STATUS_COLOR[s]} style={{ margin: 0 }}>{s}</Tag>,
            value: s,
          }))}
        />
      ),
      responsive: ['sm'],
    },
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 110,
      render: (v) => new Date(v).toLocaleDateString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      defaultSortOrder: 'descend',
      responsive: ['sm'],
    },
    {
      title: '',
      key: 'view',
      width: 44,
      align: 'center',
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          size="small"
          onClick={() => setDetail(record)}
        />
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
            placeholder="Search by customer or order #"
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
          tableLayout="fixed"
          scroll={{ x: 'max-content' }}
          style={{ background: 'transparent' }}
        />
      </div>

      {/* Order detail modal */}
      <Modal
        title={`Order ${detail?.order_number}`}
        open={!!detail}
        onCancel={() => setDetail(null)}
        footer={null}
        width={480}
      >
        {detail && (
          <Descriptions column={1} size="small" bordered style={{ marginTop: 12 }}>
            <Descriptions.Item label="Customer">{detail.user_email}</Descriptions.Item>
            <Descriptions.Item label="Channel">{detail.channel ?? 'web'}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={STATUS_COLOR[detail.status]}>{detail.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Total">
              KES {(detail.total ?? 0).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="Date">
              {new Date(detail.created_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </AdminLayout>
  );
}

