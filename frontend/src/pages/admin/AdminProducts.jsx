import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select,
  Space, Popconfirm, Tag, Typography, App, Image, Tooltip,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import {
  getProducts,
  adminCreateProduct,
  adminUpdateProduct,
  adminDeleteProduct,
  adminBulkDeleteProducts,
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

export default function AdminProducts() {
  const { message } = App.useApp();
  const [products, setProducts] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null); // null = create, object = edit
  const [saving, setSaving] = useState(false);
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

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({
      sku: record.sku,
      name: record.name,
      price: record.price,
      stock: record.stock,
      category: record.category,
      ingredients: record.ingredients ?? [],
      image_url: record.image_url ?? '',
      description: '',
    });
    setModalOpen(true);
  };

  const handleSave = async (values) => {
    setSaving(true);
    const payload = { ...values, ingredients: values.ingredients ?? [] };
    try {
      if (editing) {
        await adminUpdateProduct(editing.sku, payload);
        message.success('Product updated');
      } else {
        await adminCreateProduct(payload);
        message.success('Product created');
      }
      setModalOpen(false);
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
            title="Delete this product?"
            onConfirm={() => handleDelete(record.sku)}
            okText="Delete"
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
            title="Delete all products from this system?"
            description="This only clears the local catalog and does not affect WooCommerce."
            onConfirm={handleBulkDelete}
            okText="Delete All"
            okButtonProps={{ danger: true }}
          >
            <Button danger>Bulk Delete</Button>
          </Popconfirm>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Add Product</Button>
        </Space>
      </div>

      <div style={{ background: 'var(--card)', borderRadius: 10, border: '1px solid var(--border)', overflow: 'hidden' }}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="sku"
          loading={loading}
          size="small"
          pagination={{ pageSize: 20 }}
          tableLayout="fixed"
          scroll={{ x: 'max-content' }}
          style={{ background: 'transparent' }}
        />
      </div>

      <Modal
        title={editing ? 'Edit Product' : 'Add Product'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
        okText={editing ? 'Update' : 'Create'}
        confirmLoading={saving}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 16 }}>
          <Form.Item label="SKU" name="sku" rules={[{ required: true, message: 'SKU required' }]}>
            <Input placeholder="e.g. NIAC-001" disabled={!!editing} />
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
