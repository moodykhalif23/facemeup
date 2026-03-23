import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Layout, Typography, Space, Avatar, Dropdown, Button, Badge } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  GiftOutlined,
  ShoppingCartOutlined,
  ArrowLeftOutlined,
  SunOutlined,
  MoonOutlined
} from '@ant-design/icons';
import { logout } from '../store/slices/authSlice';
import { useTheme } from '../contexts/ThemeContext';

const { Header } = Layout;
const { Title } = Typography;

export default function AppHeader({ title, showBack = false }) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { items } = useSelector((state) => state.cart);
  const { isDark, toggleTheme } = useTheme();

  const cartCount = items.reduce((total, item) => total + item.quantity, 0);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const getUserInitials = () => {
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  const menuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'My Profile',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'cart',
      icon: (
        <Badge count={cartCount} size="small" offset={[5, 0]}>
          <ShoppingCartOutlined />
        </Badge>
      ),
      label: `Shopping Cart ${cartCount > 0 ? `(${cartCount})` : ''}`,
      onClick: () => navigate('/cart'),
    },
    {
      key: 'loyalty',
      icon: <GiftOutlined />,
      label: 'Loyalty Rewards',
      onClick: () => navigate('/loyalty'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
      danger: true,
    },
  ];

  return (
    <Header style={{
      background: 'var(--card)',
      padding: '0 16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: 'var(--card-shadow)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky',
      top: 0,
      zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {showBack && (
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            type="text"
            size="large"
            style={{ marginRight: 8, color: 'var(--foreground)' }}
          />
        )}
        <Title level={4} style={{ margin: 0, color: 'var(--foreground)', fontFamily: "'Oxanium', sans-serif" }}>
          {title || 'SkinCare AI'}
        </Title>
      </div>

      <Space size={8}>
        <Button
          type="text"
          icon={isDark ? <SunOutlined /> : <MoonOutlined />}
          onClick={toggleTheme}
          size="large"
          style={{ color: 'var(--muted-foreground)' }}
        />
        <Dropdown
          menu={{ items: menuItems }}
          placement="bottomRight"
          trigger={['click']}
        >
          <Space style={{ cursor: 'pointer' }}>
            <Badge count={cartCount} offset={[-5, 5]}>
              <Avatar
                style={{
                  backgroundColor: 'var(--primary)',
                  cursor: 'pointer',
                  color: 'var(--primary-foreground)',
                  fontFamily: "'Oxanium', sans-serif",
                  fontWeight: 600,
                }}
                size="large"
              >
                {getUserInitials()}
              </Avatar>
            </Badge>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
}
