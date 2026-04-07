import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, App, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { DotLottieReact } from '@lottiefiles/dotlottie-react';
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

      {/* Animation */}
      <div style={{ 
        width: '100%', 
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 24,
        minHeight: 150,
        backgroundColor: 'transparent'
      }}>
        <DotLottieReact
          src="/animations/Face.lottie"
          loop
          autoplay
          renderConfig={{
            autoResize: true,
          }}
          style={{ 
            width: 150, 
            height: 150,
            display: 'block',
          }}
        />
      </div>

      <Card style={{
        width: '100%',
        maxWidth: 400,
        borderRadius: 6,
        border: '1px solid var(--border)',
        background: 'var(--card)',
        boxShadow: 'var(--card-shadow)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ margin: 0, color: 'var(--card-foreground)' }}>Create Account</Title>
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
              prefix={<UserOutlined style={{ color: 'var(--muted-foreground)' }} />}
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
              prefix={<MailOutlined style={{ color: 'var(--muted-foreground)' }} />}
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
              prefix={<LockOutlined style={{ color: 'var(--muted-foreground)' }} />}
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
              prefix={<LockOutlined style={{ color: 'var(--muted-foreground)' }} />}
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
              style={{ height: 48, fontWeight: 600 }}
            >
              Sign Up
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center' }}>
            <Text style={{ color: 'var(--muted-foreground)' }}>Already have an account? </Text>
            <Link to="/login">Sign in</Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
