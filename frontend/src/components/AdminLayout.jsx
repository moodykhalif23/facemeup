import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Layout, Menu, Typography, Avatar, Dropdown, Button, theme } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  UserOutlined,
  OrderedListOutlined,
  GiftOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SkinOutlined,
} from '@ant-design/icons';
import { logout } from '../store/slices/authSlice';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

const NAV_ITEMS = [
  { key: '/admin', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/admin/products', icon: <ShoppingOutlined />, label: 'Products' },
  { key: '/admin/users', icon: <UserOutlined />, label: 'Users' },
  { key: '/admin/orders', icon: <OrderedListOutlined />, label: 'Orders' },
  { key: '/admin/loyalty', icon: <GiftOutlined />, label: 'Loyalty' },
  { key: '/admin/config', icon: <SettingOutlined />, label: 'Config' },
];

export default function AdminLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { token: antToken } = theme.useToken();

  const userMenuItems = [
    {
      key: 'back',
      icon: <SkinOutlined />,
      label: 'Back to App',
      onClick: () => navigate('/'),
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
      onClick: () => { dispatch(logout()); navigate('/login'); },
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={220}
        style={{
          background: 'var(--card)',
          borderRight: '1px solid var(--border)',
          position: 'fixed',
          insetInlineStart: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflow: 'auto',
        }}
      >
        {/* Logo */}
        <div style={{
          height: 56,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '0' : '0 20px',
          borderBottom: '1px solid var(--border)',
          gap: 10,
        }}>
          <SkinOutlined style={{ fontSize: 20, color: 'var(--primary)', flexShrink: 0 }} />
          {!collapsed && (
            <Text strong style={{ color: 'var(--foreground)', fontSize: 15, whiteSpace: 'nowrap' }}>
              Admin Panel
            </Text>
          )}
        </div>

        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={NAV_ITEMS}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent',
            border: 'none',
            marginTop: 8,
          }}
        />
      </Sider>

      <Layout style={{ marginInlineStart: collapsed ? 80 : 220, transition: 'margin 0.2s' }}>
        <Header style={{
          background: 'var(--card)',
          borderBottom: '1px solid var(--border)',
          padding: '0 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 99,
          height: 56,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: 'var(--foreground)' }}
          />

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <Avatar
                size={32}
                style={{ background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 600 }}
              >
                {user?.email?.[0]?.toUpperCase() ?? 'A'}
              </Avatar>
              {!collapsed && (
                <Text style={{ color: 'var(--foreground)', fontSize: 13 }}>
                  {user?.email}
                </Text>
              )}
            </div>
          </Dropdown>
        </Header>

        <Content style={{
          padding: 24,
          background: 'var(--background)',
          minHeight: 'calc(100vh - 56px)',
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
