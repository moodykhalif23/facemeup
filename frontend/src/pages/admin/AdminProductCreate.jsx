import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card, Form, Input, InputNumber, Select, Space, Button, Typography, App, Grid,
} from 'antd';
import { PlusOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import AdminLayout from '../../components/AdminLayout';
import { adminCreateProduct } from '../../services/api';

const { Title, Text } = Typography;

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

export default function AdminProductCreate() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const screens = Grid.useBreakpoint();
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const imageUrl = Form.useWatch('image_url', form);

  const handleSave = async (values) => {
    setSaving(true);
    const payload = { ...values, ingredients: values.ingredients ?? [] };
    try {
      await adminCreateProduct(payload);
      message.success('Product created');
      navigate('/admin/products');
    } catch (err) {
      message.error(err.response?.data?.error?.message ?? 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <AdminLayout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, gap: 12, flexWrap: 'wrap' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/admin/products')}>
            Back
          </Button>
          <Text style={{ color: 'var(--muted-foreground)', fontSize: 13 }}>
            Add a new product to the local catalog
          </Text>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => form.submit()} loading={saving}>
          Save Product
        </Button>
      </div>

      <Form form={form} layout="vertical" onFinish={handleSave}>
        <div
          style={{
            display: 'grid',
            gap: 16,
            gridTemplateColumns: screens.lg ? '1.2fr 0.8fr' : '1fr',
          }}
        >
          <Card
            style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}
            styles={{ body: { padding: 20 } }}
          >
            <Title level={5} style={{ marginTop: 0, color: 'var(--foreground)' }}>Product Info</Title>

            <Form.Item label="Product Name" name="name" rules={[{ required: true }]}>
              <Input placeholder="e.g. Niacinamide 10% Serum" />
            </Form.Item>

            <Form.Item label="SKU" name="sku" rules={[{ required: true, message: 'SKU required' }]}>
              <Input placeholder="e.g. NIAC-001" />
            </Form.Item>

            <Form.Item label="Price (KES)" name="price" rules={[{ required: true }]}>
              <InputNumber min={0} step={50} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item label="Stock" name="stock" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: '100%' }} />
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

            <Form.Item label="Description" name="description">
              <Input.TextArea rows={4} placeholder="Short product description" />
            </Form.Item>
          </Card>

          <Card
            style={{ border: '1px solid var(--border)', background: 'var(--card)', borderRadius: 10 }}
            styles={{ body: { padding: 20 } }}
          >
            <Title level={5} style={{ marginTop: 0, color: 'var(--foreground)' }}>Product Image</Title>

            <Form.Item label="Image URL" name="image_url">
              <Input placeholder="https://..." />
            </Form.Item>

            <div
              style={{
                border: '1px dashed var(--border)',
                borderRadius: 12,
                padding: 16,
                background: 'var(--muted)',
                minHeight: 220,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--muted-foreground)',
              }}
            >
              {imageUrl ? (
                <img
                  src={imageUrl}
                  alt="Preview"
                  style={{ maxWidth: '100%', maxHeight: 220, borderRadius: 10, objectFit: 'contain' }}
                />
              ) : (
                <Text style={{ color: 'var(--muted-foreground)' }}>Image preview</Text>
              )}
            </div>
          </Card>
        </div>
      </Form>
    </AdminLayout>
  );
}
