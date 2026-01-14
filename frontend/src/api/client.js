import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling authentication errors and business rule warnings
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 authentication errors
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/auth/login';
      return Promise.reject(error);
    }
    
    // Handle 409 business rule warnings (don't log to console)
    if (error.response?.status === 409) {
      const detail = error.response.data?.detail;
      
      // Silent reject for expected business rule violations
      if (detail?.code === 'HOUSE_MEMBER_LIMIT_REACHED') {
        // Don't console.error for this expected business logic case
        return Promise.reject(error);
      }
      
      // Other 409 cases might be unexpected, so we can log them
      console.warn('Conflict error (409):', error.response.data);
      return Promise.reject(error);
    }
    
    // Log all other errors normally (500, network, etc.)
    if (error.response?.status >= 500) {
      console.error('Server error:', error.response.status, error.response.data);
    } else if (!error.response) {
      console.error('Network error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Dashboard API
export const dashboardAPI = {
  getSummary: () => apiClient.get('/api/dashboard/summary'),
};

// Houses API
export const housesAPI = {
  list: (params) => apiClient.get('/api/houses', { params }),
  get: (id) => apiClient.get(`/api/houses/${id}`),
  create: (data) => apiClient.post('/api/houses', data),
  update: (id, data) => apiClient.put(`/api/houses/${id}`, data),
  delete: (id) => apiClient.delete(`/api/houses/${id}`),
};

// Invoices API
export const invoicesAPI = {
  list: (params) => apiClient.get('/api/invoices', { params }),
  get: (id) => apiClient.get(`/api/invoices/${id}`),
  create: (data) => apiClient.post('/api/invoices', data),
  update: (id, data) => apiClient.put(`/api/invoices/${id}`, data),
  delete: (id) => apiClient.delete(`/api/invoices/${id}`),
  generateMonthly: () => apiClient.post('/api/invoices/generate-monthly'),
};

// Pay-in Reports API
export const payinsAPI = {
  list: (params) => apiClient.get('/api/payin-reports', { params }),
  get: (id) => apiClient.get(`/api/payin-reports/${id}`),
  create: (data) => apiClient.post('/api/payin-reports', data),
  update: (id, data) => apiClient.put(`/api/payin-reports/${id}`, data),
  delete: (id) => apiClient.delete(`/api/payin-reports/${id}`),
  reject: (id, reason) => apiClient.post(`/api/payin-reports/${id}/reject`, { reason }),
  match: (id, statementRowId) => apiClient.post(`/api/payin-reports/${id}/match`, null, {
    params: { statement_row_id: statementRowId }
  }),
  accept: (id) => apiClient.post(`/api/payin-reports/${id}/accept`),
};

// Expenses API
export const expensesAPI = {
  list: (params) => apiClient.get('/api/expenses', { params }),
  get: (id) => apiClient.get(`/api/expenses/${id}`),
  create: (data) => apiClient.post('/api/expenses', data),
  update: (id, data) => apiClient.put(`/api/expenses/${id}`, data),
  delete: (id) => apiClient.delete(`/api/expenses/${id}`),
};

// Bank Statements API
export const bankStatementsAPI = {
  list: () => apiClient.get('/api/bank-statements'),
  get: (id) => apiClient.get(`/api/bank-statements/${id}`),
  getRows: (id) => apiClient.get(`/api/bank-statements/${id}/rows`),
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/bank-statements/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  matchRow: (statementId, rowId, payinId) => 
    apiClient.post(`/api/bank-statements/${statementId}/rows/${rowId}/match`, null, {
      params: { payin_id: payinId }
    }),
  delete: (id) => apiClient.delete(`/api/bank-statements/${id}`),
};

// Users API
export const usersAPI = {
  createResident: (data) => apiClient.post('/api/users/residents', data),
  listResidents: (params) => apiClient.get('/api/users/residents', { params }),
  getHouseMemberCount: (houseId) => apiClient.get(`/api/users/houses/${houseId}/member-count`),
  updateResident: (id, data) => apiClient.patch(`/api/users/${id}`, data),
  resetPassword: (id) => apiClient.post(`/api/users/${id}/reset-password`),
  deactivateResident: (id) => apiClient.post(`/api/users/${id}/deactivate`),
  reactivateResident: (id) => apiClient.post(`/api/users/${id}/reactivate`),
};

// Members API (DEPRECATED - use usersAPI instead)
export const membersAPI = {
  list: (params) => apiClient.get('/api/members', { params }),
  // create: DEPRECATED - use usersAPI.createResident instead
  update: (id, data) => apiClient.put(`/api/members/${id}`, data),
  delete: (id) => apiClient.delete(`/api/members/${id}`),
};

export default apiClient;

// Export alias for AuthContext compatibility
export const api = apiClient;
