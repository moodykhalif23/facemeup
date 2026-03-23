import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Typography, Table, Tag, Spin, App, Grid } from 'antd';
import {
  UserOutlined,
  ShoppingOutlined,
  OrderedListOutlined,
  DollarOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import AdminLayout from '../../components/AdminLayout';
import { adminGetStats } from '../../services/api';

const { Title, Text } = Typography;

const STATUS_COLOR = {
  created: 'blue',
  paid: 'green',
  shipped: 'cyan',
  delivered: 'success',
  cancelled: 'red',
};

export default function AdminDashboard() {
  const { message } = App.useApp();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const screens = Grid.useBreakpoint();

  useEffect(() => {
    adminGetStats()
      .then((r) => setStats(r.data))
      .catch(() => message.error('Failed to load stats'))
      .finally(() => setLoading(false));
  }, []);

  const skinChartOption = stats?.skin_distribution
    ? {
        tooltip: { trigger: 'item' },
        legend: { bottom: 0, textStyle: { color: 'var(--foreground)' } },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            data: Object.entries(stats.skin_distribution).map(([name, value]) => ({
              name,
              value,
            })),
            label: { color: 'var(--foreground)' },
          },
        ],
      }
    : null;

  const recentColumns = [
    { title: 'Order ID', dataIndex: 'id', key: 'id', render: (v) => `#${v}` },
    { title: 'User', dataIndex: 'user_id', key: 'user_id', ellipsis: true, render: (v) => v.slice(0, 8) + '…', responsive: ['sm'] },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s) => <Tag color={STATUS_COLOR[s] ?? 'default'}>{s}</Tag>,
    },
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v) => new Date(v).toLocaleDateString(),
      responsive: ['sm'],
    },
  ];

  return (
    <AdminLayout>
      <Title level={4} style={{ marginBottom: 24, color: 'var(--foreground)' }}>
        Dashboard
      </Title>

      {loading ? (
        <div style={{ textAlign: 'center', paddingTop: 60 }}><Spin size="large" /></div>
      ) : (
        <>
          {/* Stat cards */}
          <div
            style={{
              display: 'grid',
              gap: 16,
              marginBottom: 24,
              gridTemplateColumns: screens.xl
                ? 'repeat(5, minmax(0, 1fr))'
                : screens.lg
                  ? 'repeat(3, minmax(0, 1fr))'
                  : screens.md
                    ? 'repeat(3, minmax(0, 1fr))'
                    : screens.sm
                      ? 'repeat(2, minmax(0, 1fr))'
                      : 'repeat(1, minmax(0, 1fr))',
            }}
          >
            {[
              { title: 'Total Users', value: stats?.total_users, icon: <UserOutlined />, color: '#B45309' },
              { title: 'Products', value: stats?.total_products, icon: <ShoppingOutlined />, color: '#0891b2' },
              { title: 'Orders', value: stats?.total_orders, icon: <OrderedListOutlined />, color: '#7c3aed' },
              {
                title: 'Revenue',
                value: `KES ${(stats?.total_revenue ?? 0).toLocaleString()}`,
                icon: <DollarOutlined />,
                color: '#059669',
                isString: true,
              },
              { title: 'Skin Analyses', value: stats?.total_analyses, icon: <ExperimentOutlined />, color: '#db2777' },
            ].map((s) => (
              <Card
                key={s.title}
                style={{
                  border: '1px solid var(--border)',
                  background: 'var(--card)',
                  borderRadius: 10,
                }}
                styles={{ body: { padding: '16px 20px' } }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: s.color + '22',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: s.color,
                    fontSize: 18,
                    flexShrink: 0,
                  }}>
                    {s.icon}
                  </div>
                  <div>
                    <Text style={{ fontSize: 12, color: 'var(--muted-foreground)', display: 'block' }}>
                      {s.title}
                    </Text>
                    {s.isString ? (
                      <Text strong style={{ fontSize: 18, color: 'var(--foreground)' }}>{s.value}</Text>
                    ) : (
                      <Statistic
                        value={s.value ?? 0}
                        valueStyle={{ fontSize: 20, color: 'var(--foreground)' }}
                      />
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Charts + recent orders */}
          <Row gutter={[16, 16]}>
            <Col xs={24} md={10}>
              <Card
                title={<span style={{ color: 'var(--foreground)' }}>Skin Type Distribution</span>}
                style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}
              >
                {skinChartOption && Object.keys(stats.skin_distribution).length > 0 ? (
                  <ReactECharts option={skinChartOption} style={{ height: 280 }} />
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--muted-foreground)' }}>
                    No analysis data yet
                  </div>
                )}
              </Card>
            </Col>

            <Col xs={24} md={14}>
              <Card
                title={<span style={{ color: 'var(--foreground)' }}>Recent Orders</span>}
                style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10, overflow: 'hidden' }}
              >
                <Table
                  dataSource={stats?.recent_orders ?? []}
                  columns={recentColumns}
                  rowKey="id"
                  pagination={false}
                  size="small"
                  scroll={{ x: true }}
                  style={{ background: 'transparent' }}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </AdminLayout>
  );
}
