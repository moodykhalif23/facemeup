import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Layout, Typography, Space, Avatar, Dropdown, Button, Badge } from 'antd';
import { 
  UserOutlined,
  LogoutOutlined,
  GiftOutlined,
  ShoppingCartOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons';
import { logout } from '../store/slices/authSlice';

const { Header } = Layout;
const { Title } = Typography;

export default function AppHeader({ title, showBack = false }) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { items } = useSelector((state) => state.cart);

  // Calculate total cart items
  const cartCount = items.reduce((total, item) => total + item.quantity, 0);

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  // Get user initials for avatar
  const getUserInitials = () => {
    if (user?.email) {
      return user.email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  // Dropdown menu items
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
      key: 'orders',
      icon: <ShoppingCartOutlined />,
      label: 'My Orders',
      onClick: () => navigate('/orders'),
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
      background: '#fff', 
      padding: '0 16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {showBack && (
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate(-1)}
            type="text"
            size="large"
            style={{ marginRight: 8 }}
          />
        )}
        <Title level={4} style={{ margin: 0 }}>{title || 'SkinCare AI'}</Title>
      </div>
      
      <Dropdown 
        menu={{ items: menuItems }}
        placement="bottomRight"
        trigger={['click']}
      >
        <Space style={{ cursor: 'pointer' }}>
          <Badge count={cartCount} offset={[-5, 5]}>
            <Avatar 
              style={{ 
                backgroundColor: '#3B82F6',
                cursor: 'pointer'
              }}
              size="large"
            >
              {getUserInitials()}
            </Avatar>
          </Badge>
        </Space>
      </Dropdown>
    </Header>
  );
}
