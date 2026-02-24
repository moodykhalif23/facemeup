import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('persist:auth');
    if (token) {
      try {
        const authData = JSON.parse(token);
        const accessToken = JSON.parse(authData.token);
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
      } catch (e) {
        console.error('Error parsing token:', e);
      }
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

export default api;
