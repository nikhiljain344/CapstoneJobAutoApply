import axios from 'axios';

const API_BASE_URL = 'http://localhost:5002/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('🚀 Request Config:', {
      url: config.url,
      method: config.method,
      headers: config.headers,
    });
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Token added:', config.headers.Authorization);
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', {
      url: response.config.url,
      status: response.status,
      data: response.data,
    });
    return response.data;
  },
  (error) => {
    console.error('❌ Response Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      headers: error.config?.headers,
    });
    if (error.response) {
      // Handle 401 Unauthorized
      if (error.response.status === 401) {
        console.log('🔒 Unauthorized - Clearing token');
        localStorage.removeItem('token');
      }
      return Promise.reject(error.response.data);
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    console.log('📝 Login attempt:', { email });
    return api.post('/auth/login', { email, password });
  },
  register: async (userData) => {
    console.log('📝 Register attempt:', { email: userData.email });
    return api.post('/auth/register', userData);
  },
  getCurrentUser: async () => {
    console.log('👤 Getting current user');
    return api.get('/auth/me');
  },
  changePassword: async (currentPassword, newPassword) => {
    console.log('🔑 Changing password');
    return api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};

// Profile API
export const profileAPI = {
  updateProfile: async (profileData) => {
    return api.put('/profile/basic', profileData);
  },
};

// Jobs API
export const jobsAPI = {
  getJobs: async (params) => {
    return api.get('/jobs', { params });
  },
  getJob: async (jobId) => {
    return api.get(`/jobs/${jobId}`);
  },
};

// Applications API
export const applicationsAPI = {
  getApplications: async () => {
    return api.get('/applications');
  },
  apply: async (jobId) => {
    return api.post(`/applications/${jobId}`);
  },
};

export default api; 