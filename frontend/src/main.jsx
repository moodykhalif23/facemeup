import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { ConfigProvider, App as AntApp, theme } from 'antd';
import { store, persistor } from './store';
import App from './App';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import './index.css';

function AntdConfig({ children }) {
  const { isDark } = useTheme();
  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDark ? '#F97316' : '#B45309',
          colorBgBase: isDark ? '#1C1917' : '#FDFBF7',
          colorBgContainer: isDark ? '#292524' : '#F8F4EE',
          colorBgElevated: isDark ? '#292524' : '#F8F4EE',
          colorBorder: isDark ? '#44403C' : '#E4D9BC',
          colorText: isDark ? '#F5F5F4' : '#4A3B33',
          colorTextSecondary: isDark ? '#A8A29E' : '#78716C',
          borderRadius: 5,
          fontFamily: "'Oxanium', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
      }}
    >
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ThemeProvider>
          <AntdConfig>
            <App />
          </AntdConfig>
        </ThemeProvider>
      </PersistGate>
    </Provider>
  </React.StrictMode>
);
