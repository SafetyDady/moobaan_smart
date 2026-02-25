import { useState, useEffect } from 'react';
import { vendorsAPI } from '../../api/client';
import ConfirmModal from '../../components/ConfirmModal';
import { SkeletonPage } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';

/**
 * Phase H.1.1: Vendor & Category Management
 * 
 * 3 tabs:
 * - Vendors: CRUD with deactivate/reactivate, name is immutable
 * - Vendor Categories: Create + deactivate only
 * - Expense Categories: Create + deactivate only
 */

export default function Vendors() {
  const [activeTab, setActiveTab] = useState('vendors');

  // ========== Vendors State ==========
  const [vendors, setVendors] = useState([]);
  const [vendorCategories, setVendorCategories] = useState([]);
  const [expenseCategories, setExpenseCategories] = useState([]);
  const [showInactive, setShowInactive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirmDeactivate, setConfirmDeactivate] = useState({ open: false, vendor: null });

  // Vendor Form
  const [showVendorForm, setShowVendorForm] = useState(false);
  const [editingVendor, setEditingVendor] = useState(null);
  const [vendorForm, setVendorForm] = useState({
    name: '',
    vendor_category_id: '',
    phone: '',
    bank_account: '',
  });
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');

  // Category Form
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newExpenseCategoryName, setNewExpenseCategoryName] = useState('');

  // ========== Load Data ==========
  useEffect(() => {
    loadAll();
  }, [showInactive]);

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [vendorRes, catRes, expCatRes] = await Promise.all([
        vendorsAPI.list({ active_only: !showInactive }),
        vendorsAPI.listCategories({ active_only: !showInactive }),
        vendorsAPI.listExpenseCategories({ active_only: !showInactive }),
      ]);
      setVendors(vendorRes.data.vendors || []);
      setVendorCategories(catRes.data.categories || []);
      setExpenseCategories(expCatRes.data.categories || []);
    } catch (err) {
      console.error('Failed to load vendor data:', err);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (msg) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(''), 3000);
  };

  // ========== Vendor CRUD ==========
  const resetVendorForm = () => {
    setVendorForm({ name: '', vendor_category_id: '', phone: '', bank_account: '' });
    setEditingVendor(null);
    setFormError('');
  };

  const openCreateVendor = () => {
    resetVendorForm();
    setShowVendorForm(true);
  };

  const openEditVendor = (vendor) => {
    setEditingVendor(vendor);
    setVendorForm({
      name: vendor.name,
      vendor_category_id: vendor.vendor_category_id || '',
      phone: vendor.phone || '',
      bank_account: vendor.bank_account || '',
    });
    setFormError('');
    setShowVendorForm(true);
  };

  const handleVendorSubmit = async () => {
    setFormLoading(true);
    setFormError('');
    try {
      if (editingVendor) {
        // Update (name excluded — immutable)
        await vendorsAPI.update(editingVendor.id, {
          vendor_category_id: vendorForm.vendor_category_id ? parseInt(vendorForm.vendor_category_id) : null,
          phone: vendorForm.phone || null,
          bank_account: vendorForm.bank_account || null,
        });
        showMessage(`Vendor "${editingVendor.name}" updated`);
      } else {
        // Create
        await vendorsAPI.create({
          name: vendorForm.name,
          vendor_category_id: vendorForm.vendor_category_id ? parseInt(vendorForm.vendor_category_id) : null,
          phone: vendorForm.phone || null,
          bank_account: vendorForm.bank_account || null,
        });
        showMessage(`Vendor "${vendorForm.name}" created`);
      }
      setShowVendorForm(false);
      resetVendorForm();
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'VENDOR_NAME_ALREADY_EXISTS') {
        setFormError(detail.message);
      } else {
        setFormError(typeof detail === 'string' ? detail : 'Operation failed');
      }
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeactivateVendor = async (vendor) => {
    setConfirmDeactivate({ open: false, vendor: null });
    try {
      await vendorsAPI.deactivate(vendor.id);
      showMessage(`Vendor "${vendor.name}" deactivated`);
      loadAll();
    } catch (err) {
      setError('Failed to deactivate vendor');
    }
  };

  const handleReactivateVendor = async (vendor) => {
    try {
      await vendorsAPI.reactivate(vendor.id);
      showMessage(`Vendor "${vendor.name}" reactivated`);
      loadAll();
    } catch (err) {
      setError('Failed to reactivate vendor');
    }
  };

  // ========== Vendor Category CRUD ==========
  const handleCreateVendorCategory = async () => {
    if (!newCategoryName.trim()) return;
    try {
      await vendorsAPI.createCategory({ name: newCategoryName.trim() });
      setNewCategoryName('');
      showMessage('Vendor category created');
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'CATEGORY_NAME_ALREADY_EXISTS') {
        setError(detail.message);
      } else {
        setError('Failed to create vendor category');
      }
    }
  };

  const handleToggleVendorCategory = async (cat) => {
    try {
      if (cat.is_active) {
        await vendorsAPI.deactivateCategory(cat.id);
        showMessage(`Category "${cat.name}" deactivated`);
      } else {
        await vendorsAPI.reactivateCategory(cat.id);
        showMessage(`Category "${cat.name}" reactivated`);
      }
      loadAll();
    } catch (err) {
      setError('Failed to toggle category');
    }
  };

  // ========== Expense Category CRUD ==========
  const handleCreateExpenseCategory = async () => {
    if (!newExpenseCategoryName.trim()) return;
    try {
      await vendorsAPI.createExpenseCategory({ name: newExpenseCategoryName.trim() });
      setNewExpenseCategoryName('');
      showMessage('Expense category created');
      loadAll();
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail?.code === 'CATEGORY_NAME_ALREADY_EXISTS') {
        setError(detail.message);
      } else {
        setError('Failed to create expense category');
      }
    }
  };

  const handleToggleExpenseCategory = async (cat) => {
    try {
      if (cat.is_active) {
        await vendorsAPI.deactivateExpenseCategory(cat.id);
        showMessage(`Expense category "${cat.name}" deactivated`);
      } else {
        await vendorsAPI.reactivateExpenseCategory(cat.id);
        showMessage(`Expense category "${cat.name}" reactivated`);
      }
      loadAll();
    } catch (err) {
      setError('Failed to toggle expense category');
    }
  };

  // ========== Active vendor categories for dropdown ==========
  const activeVendorCategories = vendorCategories.filter(c => c.is_active !== false);

  const tabs = [
    { id: 'vendors', label: '🏢 Vendors', count: vendors.length },
    { id: 'vendor-categories', label: '📂 Vendor Categories', count: vendorCategories.length },
    { id: 'expense-categories', label: '💰 Expense Categories', count: expenseCategories.length },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">🏢 Vendor & Category Management</h1>
        <p className="text-gray-400">{t('vendors.subtitle')}</p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400">
          ✅ {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400">
          ❌ {error}
          <button onClick={() => setError('')} className="ml-2 text-red-300 hover:text-red-200">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-slate-800 p-1 rounded-lg border border-gray-700 w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-primary-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Show Inactive Toggle */}
      <div className="mb-4 flex items-center gap-2">
        <label className="text-sm text-gray-400 flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="rounded border-gray-600 bg-slate-700 text-primary-600"
          />
          Show inactive items
        </label>
      </div>

      {loading ? (
        <SkeletonPage />
      ) : (
        <>
          {/* ========== VENDORS TAB ========== */}
          {activeTab === 'vendors' && (
            <div>
              <div className="mb-4 flex justify-between items-center">
                <h2 className="text-lg font-semibold text-white">ผู้รับเงิน ({vendors.length})</h2>
                <button
                  onClick={openCreateVendor}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg flex items-center gap-2"
                >
                  ➕ Add Vendor
                </button>
              </div>

              <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.name')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.category')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.phone')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('vendors.bankAccount')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.status')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.actions')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {vendors.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-4 py-8 text-center text-gray-400">
                          No vendors yet. Click "Add Vendor" to create one.
                        </td>
                      </tr>
                    ) : (
                      vendors.map(vendor => (
                        <tr key={vendor.id} className={`hover:bg-slate-700/50 ${!vendor.is_active ? 'opacity-50' : ''}`}>
                          <td className="px-4 py-3 text-white font-medium">{vendor.name}</td>
                          <td className="px-4 py-3 text-gray-300">{vendor.category_name || '-'}</td>
                          <td className="px-4 py-3 text-gray-300">{vendor.phone || '-'}</td>
                          <td className="px-4 py-3 text-gray-300">{vendor.bank_account || '-'}</td>
                          <td className="px-4 py-3 text-center">
                            {vendor.is_active ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">{t('common.active')}</span>
                            ) : (
                              <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">{t('common.inactive')}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex justify-center gap-2">
                              {vendor.is_active ? (
                                <>
                                  <button
                                    onClick={() => openEditVendor(vendor)}
                                    className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
                                    title="Edit (name is immutable)"
                                  >
                                    ✏️ Edit
                                  </button>
                                  <button
                                    onClick={() => setConfirmDeactivate({ open: true, vendor })}
                                    className="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                                    title="Deactivate"
                                  >
                                    🚫
                                  </button>
                                </>
                              ) : (
                                <button
                                  onClick={() => handleReactivateVendor(vendor)}
                                  className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                                >
                                  ♻️ Reactivate
                                </button>
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
          )}

          {/* ========== VENDOR CATEGORIES TAB ========== */}
          {activeTab === 'vendor-categories' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">{t('vendors.vendorCategories')}</h2>

              {/* Add Form */}
              <div className="mb-4 flex gap-2">
                <input
                  type="text"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateVendorCategory()}
                  className="flex-1 max-w-md px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  placeholder="New vendor category name..."
                />
                <button
                  onClick={handleCreateVendorCategory}
                  disabled={!newCategoryName.trim()}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg"
                >
                  ➕ Add
                </button>
              </div>

              <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.name')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.status')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.actions')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {vendorCategories.length === 0 ? (
                      <tr>
                        <td colSpan="3" className="px-4 py-8 text-center text-gray-400">{t('vendors.noVendorCategories')}</td>
                      </tr>
                    ) : (
                      vendorCategories.map(cat => (
                        <tr key={cat.id} className={`hover:bg-slate-700/50 ${!cat.is_active ? 'opacity-50' : ''}`}>
                          <td className="px-4 py-3 text-white">{cat.name}</td>
                          <td className="px-4 py-3 text-center">
                            {cat.is_active ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">{t('common.active')}</span>
                            ) : (
                              <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">{t('common.inactive')}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleToggleVendorCategory(cat)}
                              className={`px-2 py-1 text-xs rounded ${
                                cat.is_active
                                  ? 'bg-red-600 hover:bg-red-700 text-white'
                                  : 'bg-green-600 hover:bg-green-700 text-white'
                              }`}
                            >
                              {cat.is_active ? '🚫 Deactivate' : '♻️ Reactivate'}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ========== EXPENSE CATEGORIES TAB ========== */}
          {activeTab === 'expense-categories' && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">{t('vendors.expenseCategories')}</h2>
              <p className="text-sm text-gray-400 mb-4">
                These categories replace the hardcoded list. Used in expense creation dropdown.
              </p>

              {/* Add Form */}
              <div className="mb-4 flex gap-2">
                <input
                  type="text"
                  value={newExpenseCategoryName}
                  onChange={(e) => setNewExpenseCategoryName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateExpenseCategory()}
                  className="flex-1 max-w-md px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  placeholder="New expense category name..."
                />
                <button
                  onClick={handleCreateExpenseCategory}
                  disabled={!newExpenseCategoryName.trim()}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg"
                >
                  ➕ Add
                </button>
              </div>

              <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.name')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.status')}</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.actions')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {expenseCategories.length === 0 ? (
                      <tr>
                        <td colSpan="3" className="px-4 py-8 text-center text-gray-400">{t('vendors.noExpenseCategories')}</td>
                      </tr>
                    ) : (
                      expenseCategories.map(cat => (
                        <tr key={cat.id} className={`hover:bg-slate-700/50 ${!cat.is_active ? 'opacity-50' : ''}`}>
                          <td className="px-4 py-3 text-white">{cat.name}</td>
                          <td className="px-4 py-3 text-center">
                            {cat.is_active ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">{t('common.active')}</span>
                            ) : (
                              <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">{t('common.inactive')}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => handleToggleExpenseCategory(cat)}
                              className={`px-2 py-1 text-xs rounded ${
                                cat.is_active
                                  ? 'bg-red-600 hover:bg-red-700 text-white'
                                  : 'bg-green-600 hover:bg-green-700 text-white'
                              }`}
                            >
                              {cat.is_active ? '🚫 Deactivate' : '♻️ Reactivate'}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ========== VENDOR CREATE/EDIT MODAL ========== */}
      {showVendorForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">
              {editingVendor ? `✏️ Edit Vendor: ${editingVendor.name}` : '➕ Create Vendor'}
            </h2>

            {formError && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Vendor Name * {editingVendor && <span className="text-yellow-400">(immutable)</span>}
                </label>
                <input
                  type="text"
                  value={vendorForm.name}
                  onChange={(e) => setVendorForm({ ...vendorForm, name: e.target.value })}
                  className={`w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white ${
                    editingVendor ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                  placeholder="e.g., ABC Security Co."
                  disabled={!!editingVendor}
                />
                {editingVendor && (
                  <p className="text-xs text-yellow-400/70 mt-1">ไม่สามารถเปลี่ยนชื่อได้หลังสร้าง</p>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('vendors.vendorCategory')}</label>
                <select
                  value={vendorForm.vendor_category_id}
                  onChange={(e) => setVendorForm({ ...vendorForm, vendor_category_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                >
                  <option value="">ไม่มีหมวดหมู่</option>
                  {activeVendorCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('common.phone')}</label>
                  <input
                    type="text"
                    value={vendorForm.phone}
                    onChange={(e) => setVendorForm({ ...vendorForm, phone: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="e.g., 02-123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('vendors.bankAccount')}</label>
                  <input
                    type="text"
                    value={vendorForm.bank_account}
                    onChange={(e) => setVendorForm({ ...vendorForm, bank_account: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="e.g., KBank 123-4-56789-0"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowVendorForm(false); resetVendorForm(); }}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg"
                disabled={formLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleVendorSubmit}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg"
                disabled={formLoading || (!editingVendor && !vendorForm.name.trim())}
              >
                {formLoading ? 'Saving...' : (editingVendor ? 'Save Changes' : 'Create Vendor')}
              </button>
            </div>
          </div>
        </div>
      )}
      <ConfirmModal
        open={confirmDeactivate.open}
        title="ระงับ Vendor"
        message={`ต้องการระงับ "${confirmDeactivate.vendor?.name || ''}" ใช่หรือไม่? Vendor จะถูกซ่อนจาก dropdown แต่รายการค่าใช้จ่ายเดิมยังคงอยู่`}
        variant="warning"
        confirmText="ระงับ"
        onConfirm={() => handleDeactivateVendor(confirmDeactivate.vendor)}
        onCancel={() => setConfirmDeactivate({ open: false, vendor: null })}
      />
    </div>
  );
}
