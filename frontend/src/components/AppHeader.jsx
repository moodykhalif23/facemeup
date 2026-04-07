import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Layout, Typography, Space, Avatar, Dropdown, Button, Badge } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  GiftOutlined,
  ShoppingCartOutlined,
  ArrowLeftOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { logout } from '../store/slices/authSlice';

const { Header } = Layout;
const { Title } = Typography;

export default function AppHeader({ title, showBack = false }) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { items } = useSelector((state) => state.cart);
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
      key: 'reports',
      icon: <FileTextOutlined />,
      label: 'My Reports',
      onClick: () => navigate('/reports'),
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
    <>
      <Header style={{
        background: 'rgba(15, 8, 4, 0.72)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        padding: '0 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 1px 0 rgba(249,115,22,0.2), 0 4px 32px rgba(0,0,0,0.35)',
        borderBottom: '1px solid rgba(249,115,22,0.2)',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}>
        <Title level={4} style={{
          margin: 0,
          fontFamily: "'Oxanium', sans-serif",
          background: 'linear-gradient(135deg, #F97316 0%, #fb923c 55%, #fdba74 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          {title || 'SkinCare AI'}
        </Title>

        <Space size={8}>
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

      {showBack && (
        <div style={{ padding: '6px 12px' }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            type="text"
            style={{ color: 'var(--foreground)', paddingLeft: 0 }}
          >
            Back
          </Button>
        </div>
      )}
    </>
  );
}
