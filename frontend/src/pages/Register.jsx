import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, App, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { register } from '../services/api';

const { Title, Text } = Typography;

export default function Register() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { message } = App.useApp();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await register(values.email, values.password, values.fullName);
      message.success('Registration successful! Please login.');
      navigate('/login');
    } catch (error) {
      message.error(error.response?.data?.error?.message || 'Registration failed');
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
      background: '#ffffff',
      padding: '20px'
    }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>SkinCare AI</Title>
      </div>
      <Card style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0 }}>Create Account</Title>
        </div>

        <Form
          name="register"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="fullName"
            rules={[{ required: true, message: 'Please input your name!' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Full Name" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please input your email!' },
              { type: 'email', message: 'Please enter a valid email!' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="Email" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please input your password!' },
              { min: 6, message: 'Password must be at least 6 characters!' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm your password!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match!'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm Password"
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="acceptTerms"
            valuePropName="checked"
            rules={[
              {
                validator(_, value) {
                  if (value) return Promise.resolve();
                  return Promise.reject(new Error('You must accept the Terms & Conditions to continue'));
                },
              },
            ]}
          >
            <Checkbox>
              I agree to the{' '}
              <a href="/terms" target="_blank" rel="noopener noreferrer">
                Terms & Conditions
              </a>{' '}
              and{' '}
              <a href="/privacy" target="_blank" rel="noopener noreferrer">
                Privacy Policy
              </a>
            </Checkbox>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              Sign Up
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text>Already have an account? </Text>
            <Link to="/login">Sign in</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
