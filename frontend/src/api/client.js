import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Log API base URL on startup
console.log('🌐 API_BASE_URL =', API_BASE_URL);

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
    
    // Auto-detect FormData and set correct Content-Type
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']; // Let browser set it with boundary
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

// Auth API
export const authAPI = {
  login: (credentials) => apiClient.post('/api/auth/login', credentials),
  logout: () => apiClient.post('/api/auth/logout'),
  getMe: () => apiClient.get('/api/auth/me'),
  changePassword: (data) => apiClient.post('/api/auth/change-password', data),
};

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
  downloadStatement: async (houseId, year, month, format) => {
    const response = await apiClient.get(
      `/api/accounting/statement/${houseId}`,
      { 
        params: { year, month, format },
        responseType: 'blob'
      }
    );
    return response.data;
  },
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
  createFormData: (formData) => apiClient.post('/api/payin-reports', formData),
  update: (id, data) => apiClient.put(`/api/payin-reports/${id}`, data),
  delete: (id) => apiClient.delete(`/api/payin-reports/${id}`),
  reject: (id, reason) => apiClient.post(`/api/payin-reports/${id}/reject`, { reason }),
  accept: (id) => apiClient.post(`/api/payin-reports/${id}/accept`),
  cancel: (id, reason) => apiClient.post(`/api/payin-reports/${id}/cancel`, { reason }),
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
  listBatches: () => apiClient.get('/api/bank-statements/batches'),
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
  getBatchTransactions: (batchId) => apiClient.get(`/api/bank-statements/batches/${batchId}/transactions`),
  uploadPreview: (file, bankAccountId, year, month) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank_account_id', bankAccountId);
    formData.append('year', year);
    formData.append('month', month);
    return apiClient.post('/api/bank-statements/upload-preview', formData, {
      params: { bank_account_id: bankAccountId, year, month },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  confirmImport: (file, bankAccountId, year, month) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank_account_id', bankAccountId);
    formData.append('year', year);
    formData.append('month', month);
    return apiClient.post('/api/bank-statements/confirm-import', formData, {
      params: { bank_account_id: bankAccountId, year, month },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  matchRow: (statementId, rowId, payinId) => 
    apiClient.post(`/api/bank-statements/${statementId}/rows/${rowId}/match`, null, {
      params: { payin_id: payinId }
    }),
  delete: (id) => apiClient.delete(`/api/bank-statements/${id}`),
};

// Bank Accounts API
export const bankAccountsAPI = {
  list: () => apiClient.get('/api/bank-accounts'),
  create: (data) => apiClient.post('/api/bank-accounts', data),
  update: (id, data) => apiClient.put(`/api/bank-accounts/${id}`, data),
  delete: (id) => apiClient.delete(`/api/bank-accounts/${id}`),
};

// Bank Reconciliation API
export const bankReconciliationAPI = {
  listUnmatchedTransactions: (batchId) => 
    apiClient.get('/api/bank-statements/transactions/unmatched', { 
      params: batchId ? { batch_id: batchId } : {} 
    }),
  getCandidatesForPayin: (payinId) =>
    apiClient.get(`/api/bank-statements/candidates/payin/${payinId}`),
  matchTransaction: (txnId, payinId) => 
    apiClient.post(`/api/bank-statements/transactions/${txnId}/match`, { payin_id: payinId }),
  unmatchTransaction: (txnId) => 
    apiClient.post(`/api/bank-statements/transactions/${txnId}/unmatch`),
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
