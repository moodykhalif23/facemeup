import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Form, Input, Button, Card, Typography, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../services/api';
import { setCredentials } from '../store/slices/authSlice';

const { Title, Text } = Typography;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { message } = App.useApp();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await login(values.email, values.password);
      dispatch(setCredentials(response.data));
      message.success('Login successful!');
      if (response.data?.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (error) {
      message.error(error.response?.data?.error?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--background)',
      padding: '20px'
    }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: 'var(--foreground)', fontFamily: "'Oxanium', sans-serif" }}>
          SkinCare AI
        </Title>
        <Text style={{ color: 'var(--muted-foreground)', fontSize: 14 }}>
          Your personal AI skincare advisor
        </Text>
      </div>

      <Card style={{
        width: '100%',
        maxWidth: 400,
        borderRadius: 12,
        border: '1px solid var(--border)',
        background: 'var(--card)',
        boxShadow: 'var(--card-shadow)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Text style={{ color: 'var(--muted-foreground)' }}>Sign in to your account</Text>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please input your email!' },
              { type: 'email', message: 'Please enter a valid email!' }
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: 'var(--muted-foreground)' }} />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: 'var(--muted-foreground)' }} />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{ height: 48, fontWeight: 600 }}
            >
              Sign In
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text style={{ color: 'var(--muted-foreground)' }}>Don't have an account? </Text>
            <Link to="/register">Sign up</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
