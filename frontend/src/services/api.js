import axios from 'axios';
import { store } from '../store';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    try {
      const state = store.getState();
      const token = state.auth?.token;
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.error('Error getting token:', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth
export const login = (email, password) =>
  api.post('/auth/login', { email, password });

export const register = (email, password, fullName) =>
  api.post('/auth/signup', { email, password, full_name: fullName });

export const getMe = () => api.get('/auth/me');

// Analysis
export const analyzeImage = (imageBase64, questionnaire) =>
  api.post('/analyze', { image_base64: imageBase64, questionnaire });

// Recommendations
export const getRecommendations = (skinType, conditions) =>
  api.post('/recommend', { skin_type: skinType, conditions });

// Profile
export const getProfile = (userId) => api.get(`/profile/${userId}`);

// Products
export const getProducts = () => api.get('/products');

export const getProduct = (id) => api.get(`/products/${id}`);

// Orders
export const createOrder = (orderData) => api.post('/orders', orderData);

export const getOrders = () => api.get('/orders');

export const getOrder = (id) => api.get(`/orders/${id}`);

// Loyalty
export const getLoyalty = (userId) => api.get(`/loyalty/${userId}`);
export const getLoyaltyBalance = () => api.get('/loyalty');
export const awardPoints = (userId, points, reason) =>
  api.post('/loyalty/earn', null, { params: { user_id: userId, points, reason } });

// Admin 
export const adminGetStats = () => api.get('/admin/stats');
export const adminGetUsers = () => api.get('/admin/users');
export const adminUpdateUserRole = (userId, role) =>
  api.put(`/admin/users/${userId}/role`, { role });
export const adminDeleteUser = (userId) => api.delete(`/admin/users/${userId}`);
export const adminGetOrders = () => api.get('/admin/orders');
export const adminUpdateOrderStatus = (orderId, status) =>
  api.put(`/admin/orders/${orderId}/status`, { status });
export const adminCreateProduct = (data) => api.post('/products/admin/create', data);
export const adminUpdateProduct = (sku, data) => api.put(`/products/admin/${sku}`, data);
export const adminDeleteProduct = (sku) => api.delete(`/products/admin/${sku}`);
export const adminSeedProducts = () => api.post('/products/admin/seed');
export const adminBulkDeleteProducts = () => api.delete('/products/admin/bulk');
export const adminSyncWooCommerce = () => api.post('/sync/woocommerce');
export const adminClearCache = () => api.post('/admin/cache/clear');

export default api;
