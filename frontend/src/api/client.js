import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // CRITICAL: Send/receive httpOnly cookies
});

// Helper to get CSRF token from cookie
function getCsrfToken() {
  const match = document.cookie.match(/(^|;)\s*csrf_token=([^;]+)/);
  return match ? match[2] : null;
}

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
let refreshPromise = null;

// Request interceptor to add CSRF token (auth via httpOnly cookie automatically)
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests
    if (config.method !== 'get') {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }
    
    // Auth token is sent via httpOnly cookie automatically (withCredentials: true)
    // No need for Authorization header
    
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
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 authentication errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const requestUrl = originalRequest?.url || '';
      
      // Don't retry for login, logout, or refresh endpoints
      if (requestUrl.includes('/api/auth/login') || 
          requestUrl.includes('/api/auth/logout') ||
          requestUrl.includes('/api/auth/refresh')) {
        return Promise.reject(error);
      }
      
      // Auth check failures (/api/auth/me) are handled gracefully by AuthContext
      if (requestUrl.includes('/api/auth/me')) {
        return Promise.reject(error);
      }
      
      // Try to refresh token
      originalRequest._retry = true;
      
      try {
        // Prevent multiple concurrent refresh attempts
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = apiClient.post('/api/auth/refresh');
        }
        
        await refreshPromise;
        isRefreshing = false;
        refreshPromise = null;
        
        // Retry the original request with new cookie
        return apiClient(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshPromise = null;
        
        // Refresh failed - redirect to login (cookies cleared by server)
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
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
  refresh: () => apiClient.post('/api/auth/refresh'),
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
  getDetail: (id) => apiClient.get(`/api/invoices/${id}/detail`),
  create: (data) => apiClient.post('/api/invoices', data),
  createManual: (data) => apiClient.post('/api/invoices/manual', data),
  update: (id, data) => apiClient.put(`/api/invoices/${id}`, data),
  delete: (id) => apiClient.delete(`/api/invoices/${id}`),
  generateMonthly: () => apiClient.post('/api/invoices/generate-monthly'),
  // Apply Payment APIs (Phase 3)
  getAllocatableLedgers: (houseId) => 
    apiClient.get('/api/invoices/allocatable-ledgers', { params: houseId ? { house_id: houseId } : {} }),
  applyPayment: (invoiceId, data) => 
    apiClient.post(`/api/invoices/${invoiceId}/apply-payment`, data),
  getPayments: (invoiceId) => 
    apiClient.get(`/api/invoices/${invoiceId}/payments`),
};

// Credit Notes API (Phase D.2)
export const creditNotesAPI = {
  list: (invoiceId) => apiClient.get('/api/credit-notes', { params: invoiceId ? { invoice_id: invoiceId } : {} }),
  get: (id) => apiClient.get(`/api/credit-notes/${id}`),
  create: (data) => apiClient.post('/api/credit-notes', data),
  // NOTE: No update/delete - Credit notes are IMMUTABLE
};

// Promotions API (Phase D.4)
export const promotionsAPI = {
  list: (params) => apiClient.get('/api/promotions', { params }),
  get: (id) => apiClient.get(`/api/promotions/${id}`),
  create: (data) => apiClient.post('/api/promotions', data),
  // CORE: Evaluate promotions for a pay-in (READ-ONLY, no side effects)
  evaluate: (payinId) => apiClient.get('/api/promotions/evaluate', { params: { payin_id: payinId } }),
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
  // Phase D.3: FIFO Allocation
  applyFifo: (id) => apiClient.post(`/api/payin-reports/${id}/apply-fifo`),
};

// Expenses API (Phase F.1: Expense Core)
export const expensesAPI = {
  list: (params) => apiClient.get('/api/expenses', { params }),
  get: (id) => apiClient.get(`/api/expenses/${id}`),
  create: (data) => apiClient.post('/api/expenses', data),
  update: (id, data) => apiClient.put(`/api/expenses/${id}`, data),
  markPaid: (id, data) => apiClient.post(`/api/expenses/${id}/mark-paid`, data),
  cancel: (id) => apiClient.post(`/api/expenses/${id}/cancel`),
  getCategories: () => apiClient.get('/api/expenses/meta/categories'),
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

// Reports API (Phase E.1, E.2)
export const reportsAPI = {
  // Invoice Aging Report - READ-ONLY
  invoiceAging: (params) => apiClient.get('/api/reports/invoice-aging', { params }),
  // Cash Flow vs AR Report - READ-ONLY
  cashflowVsAr: (params) => apiClient.get('/api/reports/cashflow-vs-ar', { params }),
};

// Chart of Accounts API (Phase F.2: COA Lite)
export const accountsAPI = {
  // List all accounts with optional filters
  list: (params) => apiClient.get('/api/accounts', { params }),
  // Get single account
  get: (id) => apiClient.get(`/api/accounts/${id}`),
  // Create new account
  create: (data) => apiClient.post('/api/accounts', data),
  // Update account (name, active only - code is immutable)
  update: (id, data) => apiClient.put(`/api/accounts/${id}`, data),
  // Soft delete account (super_admin only)
  delete: (id) => apiClient.delete(`/api/accounts/${id}`),
  // Export to CSV
  exportCsv: () => apiClient.get('/api/accounts/export/csv', { responseType: 'blob' }),
  // Get available account types
  getTypes: () => apiClient.get('/api/accounts/meta/types'),
};

export default apiClient;

// Export alias for AuthContext compatibility
export const api = apiClient;
