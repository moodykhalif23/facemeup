import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select,
  Space, Popconfirm, Tag, Typography, App, Image, Tooltip, Segmented, Alert,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, InfoCircleOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import {
  getProducts,
  adminUpdateProduct,
  adminDeleteProduct,
  adminBulkDeleteProducts,
  adminSyncWooCommerce,
  adminClearCache,
} from '../../services/api';

const { Text } = Typography;

const CATEGORIES = [
  'Cleanser', 'Moisturizer', 'Serum', 'Toner', 'Sunscreen',
  'Mask', 'Eye Cream', 'Exfoliator', 'Oil', 'Treatment', 'Other',
];

const INGREDIENT_OPTIONS = [
  'Niacinamide', 'Salicylic Acid', 'Hyaluronic Acid', 'Retinol',
  'Vitamin C', 'Ceramides', 'Glycerin', 'Tea Tree', 'Peptides',
  'Alpha Arbutin', 'Kojic Acid', 'Centella', 'Shea Butter', 'Zinc',
  'Aloe Vera', 'Benzoyl Peroxide', 'Lactic Acid', 'Glycolic Acid',
  'Panthenol', 'Squalane', 'Jojoba Oil', 'Rosehip Oil',
].map((v) => ({ label: v, value: v }));

const EFFECT_OPTIONS = [
  'clean',
  'oil control',
  'pore shrinkage',
  'replenishment',
  'moisture',
  'lock water',
  'skin whitening',
  'light spot',
  'sunscreen',
  'oxygen injection',
  'compact',
  'anti wrinkle',
  'antifading',
  'repair',
  'soothe',
  'acne treatment',
  'detoxification',
  'eye care',
  'antioxidant',
  'anti free radical',
  'collagen',
  'water oil balance',
  'brighten skin color',
  'fade acne print',
  'pouch',
  'eye lines',
  'dark circles',
  'lymphatic detoxification',
].map((v) => ({ label: v, value: v }));

export default function AdminProducts() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // null = create, object = edit
  const [saving, setSaving] = useState(false);
  const [resyncing, setResyncing] = useState(false);
  const [search, setSearch] = useState('');
  const [form] = Form.useForm();

  const load = () => {
    setLoading(true);
    getProducts()
      .then((r) => {
        setProducts(r.data);
        setFiltered(r.data);
      })
      .catch(() => message.error('Failed to load products'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const q = search.trim().toLowerCase();
    if (!q) {
      setFiltered(products);
      return;
    }
    setFiltered(
      products.filter((p) =>
        [p.name, p.sku, p.category]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(q))
      )
    );
  }, [search, products]);

  const openEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({
      sku: record.sku,
      name: record.name,
      price: record.price,
      stock: record.stock,
      category: record.category,
      ingredients: record.ingredients ?? [],
      suitable_for: record.suitable_for ?? 'all',
      effects: record.effects ?? [],
      image_url: record.image_url ?? '',
      // Pre-populate description so admin sees current value
      description: record.description ?? '',
    });
  };

  const handleSave = async (values) => {
    setSaving(true);
    const payload = { ...values, ingredients: values.ingredients ?? [] };
    try {
      await adminUpdateProduct(editing.sku, payload);
      message.success('Product updated');
      setEditing(null);
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (sku) => {
    try {
      await adminDeleteProduct(sku);
      message.success('Product deleted');
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Delete failed');
    }
  };

  const handleBulkDelete = async () => {
    try {
      const r = await adminBulkDeleteProducts();
      message.success(`Deleted ${r.data.deleted} product(s)`);
      setSearch('');
      load();
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Bulk delete failed');
    }
  };

  const handleDeleteAndResync = async () => {
    setResyncing(true);
    try {
      // Step 1: flush all Redis product caches (kills stale "Product not found" entries)
      await adminClearCache().catch(() => {}); // non-fatal if Redis is unavailable

      // Step 2: wipe all local products
      const del = await adminBulkDeleteProducts();
      setProducts([]);
      setFiltered([]);
      message.info(`Cleared ${del.data.deleted} old product(s). Syncing from WooCommerce…`);

      // Step 3: pull fresh data from WooCommerce
      const sync = await adminSyncWooCommerce();
      message.success(
        `Sync complete — ${sync.data.products_added} added, ${sync.data.products_updated} updated, ${sync.data.products_failed} failed.`
      );
      setSearch('');
      load();
    } catch (err) {
      message.error(err.response?.data?.detail ?? err.response?.data?.error?.message ?? 'Resync failed');
    } finally {
      setResyncing(false);
    }
  };

  const columns = [
    {
      title: 'Image',
      dataIndex: 'image_url',
      key: 'image_url',
      width: 60,
      render: (url) =>
        url ? (
          <Image src={url} width={44} height={44} style={{ objectFit: 'cover', borderRadius: 6 }} preview={false} />
        ) : (
          <div style={{ width: 44, height: 44, background: 'var(--muted)', borderRadius: 6 }} />
        ),
    },
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 120,
      responsive: ['lg'],
      render: (v) => <Text code style={{ fontSize: 12 }}>{v}</Text>,
    },
    { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 160,
      ellipsis: true,
      responsive: ['md'],
      render: (v) => v ? (
        <Tag style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v}</Tag>
      ) : '—',
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      width: 110,
      render: (v) => <Text style={{ whiteSpace: 'nowrap' }}>{`KES ${(v ?? 0).toLocaleString()}`}</Text>,
      sorter: (a, b) => a.price - b.price,
    },
    {
      title: 'Stock',
      dataIndex: 'stock',
      key: 'stock',
      width: 80,
      render: (v) => (
        <Tag color={v > 10 ? 'green' : v > 0 ? 'orange' : 'red'}>{v}</Tag>
      ),
      sorter: (a, b) => a.stock - b.stock,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit">
            <Button type="text" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          </Tooltip>
          <Popconfirm
            title="Remove from local catalog?"
            description="This only removes the product from this app. Your WooCommerce store is not affected."
            onConfirm={() => handleDelete(record.sku)}
            okText="Remove"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Delete">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <AdminLayout>
      {/* Local-only scope notice */}
      <Alert
        icon={<InfoCircleOutlined />}
        showIcon
        type="info"
        message="Changes here only affect this app's local product catalog."
        description="Deleting or editing products does not modify your live WooCommerce store (drrashel.co.ke). Use the Sync button to pull fresh data from WooCommerce."
        style={{ marginBottom: 16, borderRadius: 6 }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 12, flexWrap: 'wrap' }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder="Search products by name, SKU, or category"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          style={{ width: '100%', maxWidth: 420 }}
        />
        <Space>
          <Popconfirm
            title="Delete all &amp; re-sync from WooCommerce?"
            description={`This wipes all ${products.length} local products and replaces them with a fresh pull from drrashel.co.ke. Images will be included.`}
            onConfirm={handleDeleteAndResync}
            okText="Delete & Re-sync"
            okButtonProps={{ danger: true }}
          >
            <Button danger loading={resyncing}>Delete All &amp; Re-sync WooCommerce</Button>
          </Popconfirm>
          <Popconfirm
            title="Delete all products from this system?"
            description="This only clears the local catalog and does not affect WooCommerce."
            onConfirm={handleBulkDelete}
            okText="Delete All"
            okButtonProps={{ danger: true }}
          >
            <Button danger>Bulk Delete</Button>
          </Popconfirm>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/admin/products/new')}>Add Product</Button>
        </Space>
      </div>

      <div style={{ background: 'var(--card)', borderRadius: 6, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="sku"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100'],
            showTotal: (total) => `${total} product${total !== 1 ? 's' : ''}`,
          }}
          tableLayout="fixed"
          scroll={{ x: 'max-content' }}
          style={{ background: 'transparent' }}
        />
      </div>

      <Modal
        title="Edit Product"
        open={!!editing}
        onCancel={() => setEditing(null)}
        onOk={() => form.submit()}
        okText="Update"
        confirmLoading={saving}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 16 }}>
          <Form.Item label="SKU" name="sku" rules={[{ required: true, message: 'SKU required' }]}>
            <Input placeholder="e.g. NIAC-001" disabled />
          </Form.Item>

          <Form.Item label="Product Name" name="name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Niacinamide 10% Serum" />
          </Form.Item>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} placeholder="Short product description" />
          </Form.Item>

          <Form.Item label="Image URL" name="image_url">
            <Input placeholder="https://..." />
          </Form.Item>

          <Form.Item label="Category" name="category">
            <Select options={CATEGORIES.map((c) => ({ label: c, value: c }))} placeholder="Select category" allowClear />
          </Form.Item>

          <Form.Item label="Ingredients" name="ingredients">
            <Select
              mode="tags"
              options={INGREDIENT_OPTIONS}
              placeholder="Select or type ingredients"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item label="Suitable For" name="suitable_for" rules={[{ required: true }]}>
            <Segmented
              options={[
                { label: 'Male', value: 'male' },
                { label: 'Female', value: 'female' },
                { label: 'All', value: 'all' },
              ]}
              block
            />
          </Form.Item>

          <Form.Item label="Effects" name="effects">
            <Select
              mode="multiple"
              options={EFFECT_OPTIONS}
              placeholder="Select product effects"
              maxTagCount="responsive"
            />
          </Form.Item>

          <Form.Item label="Price (KES)" name="price" rules={[{ required: true }]}>
            <InputNumber min={0} step={50} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item label="Stock" name="stock" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </AdminLayout>
  );
}

