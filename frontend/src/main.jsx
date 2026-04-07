import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { ConfigProvider, App as AntApp, theme } from 'antd';
import { store, persistor } from './store';
import App from './App';
import { ThemeProvider } from './contexts/ThemeContext';
import './index.css';

function AntdConfig({ children }) {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#F97316',
          colorBgBase: '#1C1917',
          colorBgContainer: '#292524',
          colorBgElevated: '#292524',
          colorBorder: '#44403C',
          colorText: '#F5F5F4',
          colorTextSecondary: '#A8A29E',
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
