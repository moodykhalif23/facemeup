import { useState } from 'react';
import {
  Card, Button, Typography, Space, Divider, Tag, Row, Col, App, List, Alert,
} from 'antd';
import {
  SyncOutlined,
  ClearOutlined,
  DatabaseOutlined,
  CloudSyncOutlined,
  ExperimentOutlined,
  ShopOutlined,
} from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminClearCache, adminSeedProducts, adminSyncWooCommerce } from '../../services/api';

const { Text } = Typography;

function ActionCard({ icon, title, description, buttonLabel, buttonProps, onAction, result, danger }) {
  const [loading, setLoading] = useState(false);
  const [outcome, setOutcome] = useState(result ?? null);

  const run = async () => {
    setLoading(true);
    setOutcome(null);
    try {
      const res = await onAction();
      setOutcome({ type: 'success', text: typeof res === 'string' ? res : JSON.stringify(res, null, 2) });
    } catch (err) {
      setOutcome({ type: 'error', text: err.response?.data?.error?.message ?? 'Action failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      style={{
        border: `1px solid ${danger ? '#fca5a544' : 'var(--border)'}`,
        background: 'var(--card)',
        borderRadius: 10,
      }}
      styles={{ body: { padding: 20 } }}
    >
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{
          width: 42,
          height: 42,
          borderRadius: 10,
          background: danger ? '#fca5a522' : 'var(--muted)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: danger ? '#ef4444' : 'var(--primary)',
          fontSize: 20,
          flexShrink: 0,
        }}>
          {icon}
        </div>
        <div style={{ flex: 1 }}>
          <Text strong style={{ display: 'block', color: 'var(--foreground)', marginBottom: 4 }}>{title}</Text>
          <Text style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>{description}</Text>

          {outcome && (
            <Alert
              type={outcome.type}
              message={<Text style={{ fontSize: 12, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>{outcome.text}</Text>}
              style={{ marginTop: 10 }}
              closable
              onClose={() => setOutcome(null)}
            />
          )}

          <Button
            {...buttonProps}
            loading={loading}
            danger={danger}
            style={{ marginTop: 12 }}
            onClick={run}
          >
            {buttonLabel}
          </Button>
        </div>
      </div>
    </Card>
  );
}

export default function AdminConfig() {
  const { message } = App.useApp();

  const actions = [
    {
      icon: <ClearOutlined />,
      title: 'Clear Redis Cache',
      description: 'Invalidate all cached product lists and recommendation results. Data will be freshly fetched on the next request.',
      buttonLabel: 'Clear Cache',
      onAction: async () => {
        const r = await adminClearCache();
        return `Cleared ${r.data.cleared} key(s): ${(r.data.keys ?? []).join(', ') || 'none'}`;
      },
    },
    {
      icon: <CloudSyncOutlined />,
      title: 'Sync WooCommerce Products',
      description: 'Pull all published products from the Dr. Rashel WooCommerce store and upsert them into the local catalog.',
      buttonLabel: 'Sync Now',
      onAction: async () => {
        const r = await adminSyncWooCommerce();
        const d = r.data;
        return `Synced ${d.products_synced} | Added ${d.products_added} | Updated ${d.products_updated} | Failed ${d.products_failed}`;
      },
    },
    {
      icon: <DatabaseOutlined />,
      title: 'Seed Default Products',
      description: 'Reset the product catalog to the built-in default product set. This will delete any manually added products.',
      buttonLabel: 'Seed Catalog',
      danger: true,
      onAction: async () => {
        const r = await adminSeedProducts();
        return `Catalog reset — ${r.data.products} products loaded`;
      },
    },
  ];

  const endpoints = [
    { method: 'GET', path: '/admin/stats', description: 'Dashboard statistics' },
    { method: 'GET', path: '/admin/users', description: 'List all users' },
    { method: 'PUT', path: '/admin/users/{id}/role', description: 'Change user role' },
    { method: 'DELETE', path: '/admin/users/{id}', description: 'Delete a user' },
    { method: 'GET', path: '/admin/orders', description: 'List all orders' },
    { method: 'PUT', path: '/admin/orders/{id}/status', description: 'Update order status' },
    { method: 'POST', path: '/admin/cache/clear', description: 'Clear Redis cache' },
    { method: 'POST', path: '/products/admin/create', description: 'Create product' },
    { method: 'PUT', path: '/products/admin/{sku}', description: 'Update product' },
    { method: 'DELETE', path: '/products/admin/{sku}', description: 'Delete product' },
    { method: 'DELETE', path: '/products/admin/bulk', description: 'Bulk delete all products (local only)' },
    { method: 'POST', path: '/products/admin/seed', description: 'Seed default products' },
    { method: 'POST', path: '/sync/woocommerce', description: 'Sync from WooCommerce' },
    { method: 'POST', path: '/loyalty/earn', description: 'Award / deduct points' },
  ];

  const METHOD_COLOR = { GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red' };

  return (
    <AdminLayout>
      {/* System actions */}
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {actions.map((a) => (
          <Col xs={24} md={12} xl={8} key={a.title}>
            <ActionCard {...a} />
          </Col>
        ))}
      </Row>

      <Divider style={{ borderColor: 'var(--border)' }} />

      {/* API reference */}
      <Card
        style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}
        styles={{ body: { padding: 0 } }}
      >
        <List
          dataSource={endpoints}
          renderItem={(item) => (
            <List.Item style={{ padding: '10px 20px', borderBottom: '1px solid var(--border)' }}>
              <Space>
                <Tag
                  color={METHOD_COLOR[item.method]}
                  style={{ width: 60, textAlign: 'center', fontFamily: 'monospace', fontSize: 11 }}
                >
                  {item.method}
                </Tag>
                <Text code style={{ fontSize: 13 }}>{item.path}</Text>
              </Space>
              <Text style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>{item.description}</Text>
            </List.Item>
          )}
        />
      </Card>

      <div style={{ marginTop: 16 }}>
        <Text style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>
          All admin endpoints require a valid JWT with <Text code style={{ fontSize: 11 }}>role = admin</Text>.
          Interactive API docs available at <Text code style={{ fontSize: 11 }}>/docs</Text>.
        </Text>
      </div>
    </AdminLayout>
  );
}
