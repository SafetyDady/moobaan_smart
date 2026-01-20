/**
 * Phase F.2: Chart of Accounts (COA Lite) Management Page
 * 
 * Features:
 * - List all accounts with type filtering
 * - Create new account
 * - Edit account (name only, code is immutable)
 * - Toggle active/inactive
 * - Export to CSV
 * - Usage counts (expenses/invoices using each account)
 * 
 * IMPORTANT: This is COA LITE - no GL, no posting, no balances
 * Purpose: Classification, Reporting, Excel Export only
 */
import { useState, useEffect, useMemo } from 'react';
import { accountsAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

// Account type badge colors
const TYPE_COLORS = {
  ASSET: 'bg-blue-100 text-blue-800',
  LIABILITY: 'bg-red-100 text-red-800',
  REVENUE: 'bg-green-100 text-green-800',
  EXPENSE: 'bg-orange-100 text-orange-800',
};

// Account type descriptions
const TYPE_DESCRIPTIONS = {
  ASSET: '1xxx - Assets (Cash, Bank, AR)',
  LIABILITY: '2xxx - Liabilities (AP, Accrued)',
  REVENUE: '4xxx - Revenue (Fees, Income)',
  EXPENSE: '5xxx - Expenses (Operating costs)',
};

export default function ChartOfAccounts() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  
  // Form state for create/edit
  const [formData, setFormData] = useState({
    account_code: '',
    account_name: '',
    account_type: 'EXPENSE',
    active: true,
  });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  // Check if user can edit (admin or super_admin)
  const canEdit = user?.role === 'admin' || user?.role === 'super_admin';
  const canDelete = user?.role === 'super_admin';

  // Fetch accounts
  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const params = {};
      if (typeFilter) params.account_type = typeFilter;
      if (!showInactive) params.active = true;
      
      const response = await accountsAPI.list(params);
      setAccounts(response.data.accounts || []);
    } catch (err) {
      setError('Failed to load accounts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [typeFilter, showInactive]);

  // Group accounts by type for display
  const groupedAccounts = useMemo(() => {
    const groups = {
      ASSET: [],
      LIABILITY: [],
      REVENUE: [],
      EXPENSE: [],
    };
    
    accounts.forEach(acc => {
      if (groups[acc.account_type]) {
        groups[acc.account_type].push(acc);
      }
    });
    
    return groups;
  }, [accounts]);

  // Handle create account
  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError('');
    setSaving(true);
    
    try {
      await accountsAPI.create({
        account_code: formData.account_code,
        account_name: formData.account_name,
        account_type: formData.account_type,
      });
      
      setSuccess('Account created successfully');
      setShowCreateModal(false);
      resetForm();
      fetchAccounts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create account');
    } finally {
      setSaving(false);
    }
  };

  // Handle update account
  const handleUpdate = async (e) => {
    e.preventDefault();
    setFormError('');
    setSaving(true);
    
    try {
      await accountsAPI.update(editingAccount.id, {
        account_name: formData.account_name,
        active: formData.active,
      });
      
      setSuccess('Account updated successfully');
      setEditingAccount(null);
      resetForm();
      fetchAccounts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to update account');
    } finally {
      setSaving(false);
    }
  };

  // Handle soft delete
  const handleDelete = async (account) => {
    if (!window.confirm(`Disable account "${account.account_code} - ${account.account_name}"?`)) {
      return;
    }
    
    try {
      await accountsAPI.delete(account.id);
      setSuccess(`Account "${account.account_code}" disabled`);
      fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disable account');
    }
  };

  // Handle CSV export
  const handleExport = async () => {
    try {
      const response = await accountsAPI.exportCsv();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `chart_of_accounts_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSuccess('Export downloaded');
    } catch (err) {
      setError('Failed to export CSV');
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      account_code: '',
      account_name: '',
      account_type: 'EXPENSE',
      active: true,
    });
    setFormError('');
  };

  // Open edit modal
  const openEditModal = (account) => {
    setEditingAccount(account);
    setFormData({
      account_code: account.account_code,
      account_name: account.account_name,
      account_type: account.account_type,
      active: account.active,
    });
    setFormError('');
  };

  // Clear messages after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Chart of Accounts</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage account codes for classification and reporting
          </p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
          
          {canEdit && (
            <button
              onClick={() => {
                resetForm();
                setShowCreateModal(true);
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Account
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-800 rounded-lg">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            >
              <option value="">All Types</option>
              <option value="ASSET">Asset (1xxx)</option>
              <option value="LIABILITY">Liability (2xxx)</option>
              <option value="REVENUE">Revenue (4xxx)</option>
              <option value="EXPENSE">Expense (5xxx)</option>
            </select>
          </div>
          
          <div className="flex items-center">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
              />
              <span className="text-sm text-gray-700">Show Inactive</span>
            </label>
          </div>
          
          <div className="ml-auto text-sm text-gray-500">
            {accounts.length} account{accounts.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Accounts List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading accounts...</p>
        </div>
      ) : accounts.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-500">No accounts found</p>
          {canEdit && (
            <button
              onClick={() => {
                resetForm();
                setShowCreateModal(true);
              }}
              className="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Create First Account
            </button>
          )}
        </div>
      ) : typeFilter ? (
        // Single type view
        <AccountTypeSection
          title={typeFilter}
          accounts={groupedAccounts[typeFilter] || []}
          canEdit={canEdit}
          canDelete={canDelete}
          onEdit={openEditModal}
          onDelete={handleDelete}
        />
      ) : (
        // All types grouped view
        <div className="space-y-6">
          {['ASSET', 'LIABILITY', 'REVENUE', 'EXPENSE'].map(type => (
            <AccountTypeSection
              key={type}
              title={type}
              accounts={groupedAccounts[type]}
              canEdit={canEdit}
              canDelete={canDelete}
              onEdit={openEditModal}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <AccountModal
          title="Create Account"
          formData={formData}
          setFormData={setFormData}
          formError={formError}
          saving={saving}
          onSubmit={handleCreate}
          onCancel={() => {
            setShowCreateModal(false);
            resetForm();
          }}
          isCreate={true}
        />
      )}

      {/* Edit Modal */}
      {editingAccount && (
        <AccountModal
          title={`Edit Account: ${editingAccount.account_code}`}
          formData={formData}
          setFormData={setFormData}
          formError={formError}
          saving={saving}
          onSubmit={handleUpdate}
          onCancel={() => {
            setEditingAccount(null);
            resetForm();
          }}
          isCreate={false}
        />
      )}
    </div>
  );
}

// Account type section component
function AccountTypeSection({ title, accounts, canEdit, canDelete, onEdit, onDelete }) {
  if (!accounts || accounts.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className={`px-4 py-3 ${TYPE_COLORS[title]} border-b`}>
        <h2 className="font-semibold">
          {title} <span className="font-normal text-sm ml-2">({TYPE_DESCRIPTIONS[title]})</span>
        </h2>
      </div>
      
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Usage</th>
            {canEdit && (
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {accounts.map((account) => (
            <tr key={account.id} className={!account.active ? 'bg-gray-50 opacity-60' : ''}>
              <td className="px-4 py-3 font-mono text-sm text-gray-900">
                {account.account_code}
              </td>
              <td className="px-4 py-3 text-sm text-gray-900">
                {account.account_name}
              </td>
              <td className="px-4 py-3 text-center">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  account.active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {account.active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-4 py-3 text-center text-sm text-gray-500">
                {account.expense_count > 0 && (
                  <span className="text-orange-600 mr-2">{account.expense_count} exp</span>
                )}
                {account.invoice_count > 0 && (
                  <span className="text-green-600">{account.invoice_count} inv</span>
                )}
                {account.expense_count === 0 && account.invoice_count === 0 && (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              {canEdit && (
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onEdit(account)}
                    className="text-blue-600 hover:text-blue-800 text-sm mr-3"
                  >
                    Edit
                  </button>
                  {canDelete && account.expense_count === 0 && account.invoice_count === 0 && account.active && (
                    <button
                      onClick={() => onDelete(account)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Disable
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Modal component for create/edit
function AccountModal({ title, formData, setFormData, formError, saving, onSubmit, onCancel, isCreate }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={onSubmit} className="p-6">
          {formError && (
            <div className="mb-4 p-3 bg-red-100 text-red-800 rounded-lg text-sm">
              {formError}
            </div>
          )}
          
          {/* Account Code (only for create) */}
          {isCreate && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Code <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.account_code}
                onChange={(e) => setFormData({ ...formData, account_code: e.target.value })}
                placeholder="e.g., 5101"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono"
                required
                maxLength={20}
              />
              <p className="text-xs text-gray-500 mt-1">
                Convention: 1xxx=Asset, 2xxx=Liability, 4xxx=Revenue, 5xxx=Expense
              </p>
            </div>
          )}
          
          {/* Account Code (read-only for edit) */}
          {!isCreate && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Code
              </label>
              <input
                type="text"
                value={formData.account_code}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 font-mono text-gray-600"
              />
              <p className="text-xs text-gray-500 mt-1">
                Account code cannot be changed
              </p>
            </div>
          )}
          
          {/* Account Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.account_name}
              onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
              placeholder="e.g., Office Supplies"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
              maxLength={255}
            />
          </div>
          
          {/* Account Type (only for create) */}
          {isCreate && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.account_type}
                onChange={(e) => setFormData({ ...formData, account_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                required
              >
                <option value="EXPENSE">Expense (5xxx)</option>
                <option value="REVENUE">Revenue (4xxx)</option>
                <option value="ASSET">Asset (1xxx)</option>
                <option value="LIABILITY">Liability (2xxx)</option>
              </select>
            </div>
          )}
          
          {/* Account Type (read-only for edit) */}
          {!isCreate && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Type
              </label>
              <input
                type="text"
                value={formData.account_type}
                disabled
                className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-600"
              />
              <p className="text-xs text-gray-500 mt-1">
                Account type cannot be changed
              </p>
            </div>
          )}
          
          {/* Active toggle (only for edit) */}
          {!isCreate && (
            <div className="mb-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                  className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <span className="text-sm text-gray-700">Active</span>
              </label>
            </div>
          )}
          
          {/* Buttons */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : isCreate ? 'Create' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
