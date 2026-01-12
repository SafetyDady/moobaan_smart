import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// Members API
export const membersAPI = {
  list: (params) => apiClient.get('/api/members', { params }),
  get: (id) => apiClient.get(`/api/members/${id}`),
  create: (data) => apiClient.post('/api/members', data),
  update: (id, data) => apiClient.put(`/api/members/${id}`, data),
  delete: (id) => apiClient.delete(`/api/members/${id}`),
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

export default apiClient;
