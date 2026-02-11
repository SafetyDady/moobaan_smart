import { useState, useEffect } from 'react';
import { expensesAPI, housesAPI, accountsAPI, vendorsAPI } from '../../api/client';

/**
 * Phase F.1: Expense Core (Cash Out)
 * 
 * Admin UI for managing village expenses.
 * Features:
 * - List with filters (date range, status, category, house)
 * - Create expense modal
 * - Edit expense modal  
 * - Mark as paid modal
 * - Cancel confirmation
 * - Summary cards (total paid, total pending)
 */

// Fallback categories (replaced by API-loaded expense_categories from DB)
const FALLBACK_EXPENSE_CATEGORIES = [
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'SECURITY', label: 'Security' },
  { value: 'CLEANING', label: 'Cleaning' },
  { value: 'UTILITIES', label: 'Utilities' },
  { value: 'ADMIN', label: 'Admin' },
  { value: 'OTHER', label: 'Other' },
];

const PAYMENT_METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'TRANSFER', label: 'Bank Transfer' },
  { value: 'CHECK', label: 'Check' },
  { value: 'OTHER', label: 'Other' },
];

export default function Expenses() {
  // Data state
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState({
    total_paid: 0,
    total_pending: 0,
    count_paid: 0,
    count_pending: 0,
    count_cancelled: 0,
  });
  const [houses, setHouses] = useState([]);
  const [expenseAccounts, setExpenseAccounts] = useState([]);  // COA accounts (EXPENSE type)
  const [vendors, setVendors] = useState([]);  // Phase H.1.1: Vendor master
  const [expenseCategories, setExpenseCategories] = useState([]);  // Phase H.1.1: DB categories
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [houseFilter, setHouseFilter] = useState('');

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMarkPaidModal, setShowMarkPaidModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  // Form state for create/edit
  const [formData, setFormData] = useState({
    house_id: '',
    category: 'MAINTENANCE',
    amount: '',
    description: '',
    expense_date: new Date().toISOString().split('T')[0],
    vendor_name: '',
    vendor_id: '',  // Phase H.1.1: Vendor from master
    payment_method: '',
    notes: '',
    account_id: '',  // Phase F.2: COA account link
  });

  // Mark paid form
  const [paidDate, setPaidDate] = useState(new Date().toISOString().split('T')[0]);
  const [paidPaymentMethod, setPaidPaymentMethod] = useState('TRANSFER');

  // Set default date range (current month)
  useEffect(() => {
    const today = new Date();
    const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    setFromDate(firstOfMonth.toISOString().split('T')[0]);
    setToDate(today.toISOString().split('T')[0]);
  }, []);

  // Load houses for dropdown
  useEffect(() => {
    housesAPI.list()
      .then(res => setHouses(res.data || []))
      .catch(err => console.error('Failed to load houses:', err));
  }, []);

  // Load expense accounts (EXPENSE type only)
  useEffect(() => {
    accountsAPI.list({ account_type: 'EXPENSE', active: true })
      .then(res => setExpenseAccounts(res.data.accounts || []))
      .catch(err => console.error('Failed to load expense accounts:', err));
  }, []);

  // Phase H.1.1: Load vendors (active only) for dropdown
  useEffect(() => {
    vendorsAPI.list({ active_only: true })
      .then(res => setVendors(res.data.vendors || []))
      .catch(err => console.error('Failed to load vendors:', err));
  }, []);

  // Phase H.1.1: Load expense categories from DB
  useEffect(() => {
    vendorsAPI.listExpenseCategories({ active_only: true })
      .then(res => {
        const cats = res.data.categories || [];
        if (cats.length > 0) {
          setExpenseCategories(cats.map(c => ({ value: c.name, label: c.name })));
        } else {
          setExpenseCategories(FALLBACK_EXPENSE_CATEGORIES);
        }
      })
      .catch(() => setExpenseCategories(FALLBACK_EXPENSE_CATEGORIES));
  }, []);

  // Load expenses when filters change
  useEffect(() => {
    if (fromDate && toDate) {
      loadExpenses();
    }
  }, [fromDate, toDate, statusFilter, categoryFilter, houseFilter]);

  const loadExpenses = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        from_date: fromDate,
        to_date: toDate,
      };
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (houseFilter) params.house_id = houseFilter;

      const response = await expensesAPI.list(params);
      setExpenses(response.data.expenses || []);
      setSummary(response.data.summary || {
        total_paid: 0,
        total_pending: 0,
        count_paid: 0,
        count_pending: 0,
        count_cancelled: 0,
      });
    } catch (err) {
      console.error('Failed to load expenses:', err);
      setError('Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  // Status badge styling
  const getStatusBadge = (status) => {
    const badges = {
      PENDING: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
      PAID: 'bg-green-500/20 text-green-400 border border-green-500/30',
      CANCELLED: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    };
    return badges[status] || 'bg-gray-500/20 text-gray-400';
  };

  const getCategoryLabel = (value) => {
    const cat = expenseCategories.find(c => c.value === value);
    return cat ? cat.label : value;
  };

  // Create expense
  const handleCreate = async () => {
    setModalLoading(true);
    setModalError('');
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        house_id: formData.house_id ? parseInt(formData.house_id) : null,
        account_id: formData.account_id ? parseInt(formData.account_id) : null,  // Phase F.2: COA
        vendor_id: formData.vendor_id ? parseInt(formData.vendor_id) : null,  // Phase H.1.1
      };
      await expensesAPI.create(data);
      setShowCreateModal(false);
      resetForm();
      loadExpenses();
    } catch (err) {
      console.error('Failed to create expense:', err);
      setModalError(err.response?.data?.detail || 'Failed to create expense');
    } finally {
      setModalLoading(false);
    }
  };

  // Update expense
  const handleUpdate = async () => {
    setModalLoading(true);
    setModalError('');
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        house_id: formData.house_id ? parseInt(formData.house_id) : 0, // 0 to clear
        account_id: formData.account_id ? parseInt(formData.account_id) : 0, // 0 to clear (Phase F.2)
        vendor_id: formData.vendor_id ? parseInt(formData.vendor_id) : 0, // 0 to clear (Phase H.1.1)
      };
      await expensesAPI.update(selectedExpense.id, data);
      setShowEditModal(false);
      setSelectedExpense(null);
      resetForm();
      loadExpenses();
    } catch (err) {
      console.error('Failed to update expense:', err);
      setModalError(err.response?.data?.detail || 'Failed to update expense');
    } finally {
      setModalLoading(false);
    }
  };

  // Mark as paid
  const handleMarkPaid = async () => {
    setModalLoading(true);
    setModalError('');
    try {
      await expensesAPI.markPaid(selectedExpense.id, {
        paid_date: paidDate,
        payment_method: paidPaymentMethod,
      });
      setShowMarkPaidModal(false);
      setSelectedExpense(null);
      loadExpenses();
    } catch (err) {
      console.error('Failed to mark as paid:', err);
      setModalError(err.response?.data?.detail || 'Failed to mark as paid');
    } finally {
      setModalLoading(false);
    }
  };

  // Cancel expense
  const handleCancel = async () => {
    setModalLoading(true);
    setModalError('');
    try {
      await expensesAPI.cancel(selectedExpense.id);
      setShowCancelModal(false);
      setSelectedExpense(null);
      loadExpenses();
    } catch (err) {
      console.error('Failed to cancel expense:', err);
      setModalError(err.response?.data?.detail || 'Failed to cancel expense');
    } finally {
      setModalLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      house_id: '',
      category: 'MAINTENANCE',
      amount: '',
      description: '',
      expense_date: new Date().toISOString().split('T')[0],
      vendor_name: '',
      vendor_id: '',  // Phase H.1.1
      payment_method: '',
      notes: '',
      account_id: '',  // Phase F.2: COA
    });
    setModalError('');
  };

  const openEditModal = (expense) => {
    setSelectedExpense(expense);
    setFormData({
      house_id: expense.house_id || '',
      category: expense.category || 'MAINTENANCE',
      amount: expense.amount || '',
      description: expense.description || '',
      expense_date: expense.expense_date || new Date().toISOString().split('T')[0],
      vendor_name: expense.vendor_name || '',
      vendor_id: expense.vendor_id || '',  // Phase H.1.1
      payment_method: expense.payment_method || '',
      notes: expense.notes || '',
      account_id: expense.account_id || '',  // Phase F.2: COA
    });
    setModalError('');
    setShowEditModal(true);
  };

  const openMarkPaidModal = (expense) => {
    setSelectedExpense(expense);
    setPaidDate(new Date().toISOString().split('T')[0]);
    setPaidPaymentMethod(expense.payment_method || 'TRANSFER');
    setModalError('');
    setShowMarkPaidModal(true);
  };

  const openCancelModal = (expense) => {
    setSelectedExpense(expense);
    setModalError('');
    setShowCancelModal(true);
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['ID', 'Date', 'Category', 'Description', 'Vendor', 'Amount', 'Status', 'Paid Date', 'House'];
    const rows = expenses.map(e => [
      e.id,
      e.expense_date,
      getCategoryLabel(e.category),
      e.description,
      e.vendor_name || '',
      e.amount,
      e.status,
      e.paid_date || '',
      e.house_code || '',
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `expenses_${fromDate}_${toDate}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">💸 Expenses Management</h1>
          <p className="text-gray-400">Track and manage village expenses (cash out)</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowCreateModal(true); }}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg flex items-center gap-2"
        >
          <span>➕</span> Create Expense
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Total Paid</div>
          <div className="text-2xl font-bold text-green-400">฿{summary.total_paid?.toLocaleString() || 0}</div>
          <div className="text-xs text-gray-500">{summary.count_paid || 0} expenses</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Total Pending</div>
          <div className="text-2xl font-bold text-yellow-400">฿{summary.total_pending?.toLocaleString() || 0}</div>
          <div className="text-xs text-gray-500">{summary.count_pending || 0} expenses</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Total (Paid + Pending)</div>
          <div className="text-2xl font-bold text-white">
            ฿{((summary.total_paid || 0) + (summary.total_pending || 0)).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">
            {(summary.count_paid || 0) + (summary.count_pending || 0)} expenses
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-sm">Cancelled</div>
          <div className="text-2xl font-bold text-gray-400">{summary.count_cancelled || 0}</div>
          <div className="text-xs text-gray-500">expenses</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-800 rounded-xl p-4 mb-6 border border-gray-700">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">From Date</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">To Date</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
            >
              <option value="">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="PAID">Paid</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
            >
              <option value="">All Categories</option>
              {expenseCategories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">House</label>
            <select
              value={houseFilter}
              onChange={(e) => setHouseFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
            >
              <option value="">All Houses</option>
              {houses.map(h => (
                <option key={h.id} value={h.id}>{h.house_code || h.house_number}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={exportToCSV}
              className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
            >
              📥 Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Expenses Table */}
      <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Category</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Description</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Vendor</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Amount</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Paid Date</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">House</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-400">
                    Loading...
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-400">
                    No expenses found for the selected period
                  </td>
                </tr>
              ) : (
                expenses.map((expense) => (
                  <tr key={expense.id} className="hover:bg-slate-700/50">
                    <td className="px-4 py-3 text-gray-300">
                      {expense.expense_date}
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      {getCategoryLabel(expense.category)}
                    </td>
                    <td className="px-4 py-3 text-white max-w-xs truncate">
                      {expense.description}
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      {expense.vendor_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-white">
                      ฿{expense.amount?.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(expense.status)}`}>
                        {expense.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      {expense.paid_date || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-300">
                      {expense.house_code || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        {expense.status === 'PENDING' && (
                          <>
                            <button
                              onClick={() => openEditModal(expense)}
                              className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
                              title="Edit"
                            >
                              ✏️
                            </button>
                            <button
                              onClick={() => openMarkPaidModal(expense)}
                              className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                              title="Mark Paid"
                            >
                              ✅
                            </button>
                            <button
                              onClick={() => openCancelModal(expense)}
                              className="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                              title="Cancel"
                            >
                              ❌
                            </button>
                          </>
                        )}
                        {expense.status === 'PAID' && (
                          <span className="text-xs text-gray-500">Paid</span>
                        )}
                        {expense.status === 'CANCELLED' && (
                          <span className="text-xs text-gray-500">Cancelled</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">➕ Create Expense</h2>
            
            {modalError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {modalError}
              </div>
            )}

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    {expenseCategories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Amount (฿) *</label>
                  <input
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="0.00"
                    min="0.01"
                    step="0.01"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Description *</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  placeholder="e.g., Monthly security guard salary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Expense Date *</label>
                  <input
                    type="date"
                    value={formData.expense_date}
                    onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Vendor *</label>
                  <select
                    value={formData.vendor_id}
                    onChange={(e) => {
                      const vid = e.target.value;
                      const v = vendors.find(v => v.id === parseInt(vid));
                      setFormData({ ...formData, vendor_id: vid, vendor_name: v ? v.name : '' });
                    }}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Select vendor...</option>
                    {vendors.map(v => (
                      <option key={v.id} value={v.id}>{v.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Related House</label>
                  <select
                    value={formData.house_id}
                    onChange={(e) => setFormData({ ...formData, house_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">None (Village-wide)</option>
                    {houses.map(h => (
                      <option key={h.id} value={h.id}>{h.house_code || h.house_number}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Account Code</label>
                  <select
                    value={formData.account_id}
                    onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Not assigned</option>
                    {expenseAccounts.map(acc => (
                      <option key={acc.id} value={acc.id}>{acc.account_code} - {acc.account_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Payment Method</label>
                  <select
                    value={formData.payment_method}
                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Not specified</option>
                    {PAYMENT_METHODS.map(pm => (
                      <option key={pm.value} value={pm.value}>{pm.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  rows="2"
                  placeholder="Additional notes..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowCreateModal(false); resetForm(); }}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
                disabled={modalLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
                disabled={modalLoading || !formData.amount || !formData.description || !formData.vendor_id}
              >
                {modalLoading ? 'Creating...' : 'Create Expense'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedExpense && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">✏️ Edit Expense #{selectedExpense.id}</h2>
            
            {modalError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {modalError}
              </div>
            )}

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    {expenseCategories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Amount (฿) *</label>
                  <input
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    min="0.01"
                    step="0.01"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Description *</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Expense Date *</label>
                  <input
                    type="date"
                    value={formData.expense_date}
                    onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Vendor *</label>
                  <select
                    value={formData.vendor_id}
                    onChange={(e) => {
                      const vid = e.target.value;
                      const v = vendors.find(v => v.id === parseInt(vid));
                      setFormData({ ...formData, vendor_id: vid, vendor_name: v ? v.name : '' });
                    }}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Select vendor...</option>
                    {vendors.map(v => (
                      <option key={v.id} value={v.id}>{v.name}</option>
                    ))}
                  </select>
                  {formData.vendor_name && !formData.vendor_id && (
                    <p className="text-xs text-yellow-400/70 mt-1">Legacy: {formData.vendor_name}</p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Related House</label>
                  <select
                    value={formData.house_id}
                    onChange={(e) => setFormData({ ...formData, house_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">None (Village-wide)</option>
                    {houses.map(h => (
                      <option key={h.id} value={h.id}>{h.house_code || h.house_number}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Account Code</label>
                  <select
                    value={formData.account_id}
                    onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Not assigned</option>
                    {expenseAccounts.map(acc => (
                      <option key={acc.id} value={acc.id}>{acc.account_code} - {acc.account_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Payment Method</label>
                  <select
                    value={formData.payment_method}
                    onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="">Not specified</option>
                    {PAYMENT_METHODS.map(pm => (
                      <option key={pm.value} value={pm.value}>{pm.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  rows="2"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowEditModal(false); setSelectedExpense(null); resetForm(); }}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
                disabled={modalLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleUpdate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                disabled={modalLoading || !formData.amount || !formData.description}
              >
                {modalLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mark Paid Modal */}
      {showMarkPaidModal && selectedExpense && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">✅ Mark as Paid</h2>
            
            {modalError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {modalError}
              </div>
            )}

            <div className="mb-4 p-4 bg-slate-700 rounded-lg">
              <p className="text-gray-300">
                <strong>Expense:</strong> {selectedExpense.description}
              </p>
              <p className="text-white text-lg font-bold mt-1">
                Amount: ฿{selectedExpense.amount?.toLocaleString()}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Paid Date *</label>
                <input
                  type="date"
                  value={paidDate}
                  onChange={(e) => setPaidDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  min={selectedExpense.expense_date}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Must be on or after expense date ({selectedExpense.expense_date})
                </p>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Payment Method</label>
                <select
                  value={paidPaymentMethod}
                  onChange={(e) => setPaidPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                >
                  {PAYMENT_METHODS.map(pm => (
                    <option key={pm.value} value={pm.value}>{pm.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowMarkPaidModal(false); setSelectedExpense(null); }}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
                disabled={modalLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleMarkPaid}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
                disabled={modalLoading || !paidDate}
              >
                {modalLoading ? 'Processing...' : 'Mark as Paid'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {showCancelModal && selectedExpense && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">❌ Cancel Expense</h2>
            
            {modalError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {modalError}
              </div>
            )}

            <div className="mb-4 p-4 bg-slate-700 rounded-lg">
              <p className="text-gray-300">
                <strong>Expense:</strong> {selectedExpense.description}
              </p>
              <p className="text-white text-lg font-bold mt-1">
                Amount: ฿{selectedExpense.amount?.toLocaleString()}
              </p>
            </div>

            <p className="text-gray-300 mb-6">
              Are you sure you want to cancel this expense? This action cannot be undone.
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowCancelModal(false); setSelectedExpense(null); }}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
                disabled={modalLoading}
              >
                No, Keep It
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg"
                disabled={modalLoading}
              >
                {modalLoading ? 'Cancelling...' : 'Yes, Cancel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
