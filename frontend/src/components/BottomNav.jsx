import { useNavigate, useLocation } from 'react-router-dom';
import { HomeOutlined, ScanOutlined, UserOutlined } from '@ant-design/icons';

const TABS = [
  { path: '/',          icon: HomeOutlined,  label: 'Home'     },
  { path: '/analysis',  icon: ScanOutlined,  label: 'Analysis' },
  { path: '/profile',   icon: UserOutlined,  label: 'Settings' },
];

export default function BottomNav() {
  const navigate  = useNavigate();
  const { pathname } = useLocation();

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: 60,
      background: 'var(--card)',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      zIndex: 200,
      paddingBottom: 'env(safe-area-inset-bottom)',
    }}>
      {TABS.map(({ path, icon: Icon, label }) => {
        const active = pathname === path;
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              padding: '6px 0',
              color: active ? 'var(--primary)' : 'var(--muted-foreground)',
              transition: 'color 0.2s',
            }}
          >
            <Icon style={{ fontSize: 22 }} />
            <span style={{
              fontSize: 11,
              fontWeight: active ? 600 : 400,
              letterSpacing: 0.3,
              fontFamily: "'Oxanium', sans-serif",
            }}>
              {label}
            </span>
            {active && (
              <span style={{
                position: 'absolute',
                bottom: 0,
                width: 32,
                height: 3,
                borderRadius: '3px 3px 0 0',
                background: 'var(--primary)',
              }} />
            )}
          </button>
        );
      })}
    </nav>
  );
}
