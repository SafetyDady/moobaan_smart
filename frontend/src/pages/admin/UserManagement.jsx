import { useState, useEffect } from 'react';
import { usersAPI } from '../../api/client';
import ConfirmModal from '../../components/ConfirmModal';

/**
 * User Management Dashboard — Super Admin Only
 * 
 * 2 tabs:
 * - Staff Users: list/create/deactivate/reactivate/reset-password (accounting, admin)
 * - Residents: list with search (read-only view, actions via Members page)
 */

export default function UserManagement() {
  const [activeTab, setActiveTab] = useState('staff');

  // Staff state
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirmDeactivate, setConfirmDeactivate] = useState({ open: false, user: null });

  // Create staff form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState('');
  const [staffForm, setStaffForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'accounting',
    phone: '',
  });

  // Reset password modal
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetTarget, setResetTarget] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  // Residents state
  const [residents, setResidents] = useState([]);
  const [residentsLoading, setResidentsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // ========== Load Data ==========
  useEffect(() => {
    if (activeTab === 'staff') loadStaff();
    else loadResidents();
  }, [activeTab]);

  const loadStaff = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await usersAPI.listStaff();
      setStaff(res.data.staff || []);
    } catch (err) {
      setError('Failed to load staff users');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadResidents = async () => {
    setResidentsLoading(true);
    try {
      const res = await usersAPI.listResidents({ q: searchQuery || undefined, limit: 200 });
      setResidents(res.data.residents || []);
    } catch (err) {
      console.error('Failed to load residents:', err);
    } finally {
      setResidentsLoading(false);
    }
  };

  const showMsg = (msg) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(''), 4000);
  };

  // ========== Staff CRUD ==========
  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError('');
    try {
      await usersAPI.createStaff(staffForm);
      showMsg(`Staff user '${staffForm.email}' created`);
      setShowCreateForm(false);
      setStaffForm({ email: '', password: '', full_name: '', role: 'accounting', phone: '' });
      loadStaff();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Failed to create');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeactivateStaff = async (user) => {
    setConfirmDeactivate({ open: false, user: null });
    try {
      await usersAPI.deactivateStaff(user.id);
      showMsg(`${user.email} deactivated`);
      loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to deactivate');
    }
  };

  const handleReactivateStaff = async (user) => {
    try {
      await usersAPI.reactivateStaff(user.id);
      showMsg(`${user.email} reactivated`);
      loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reactivate');
    }
  };

  const openResetPassword = (user) => {
    setResetTarget(user);
    setNewPassword('');
    setShowResetModal(true);
  };

  const handleResetPassword = async () => {
    if (newPassword.length < 8) {
      setFormError('Password must be at least 8 characters');
      return;
    }
    setResetLoading(true);
    try {
      await usersAPI.resetStaffPassword(resetTarget.id, { new_password: newPassword });
      showMsg(`Password reset for ${resetTarget.email}`);
      setShowResetModal(false);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setResetLoading(false);
    }
  };

  // ========== Render ==========
  const tabs = [
    { key: 'staff', label: `Staff Users (${staff.length})`, icon: '👤' },
    { key: 'residents', label: `Residents (${residents.length})`, icon: '🏠' },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          👥 User Management
        </h1>
        <p className="text-gray-400 mt-1">Manage staff accounts and view residents</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      {success && (
        <div className="mb-4 p-3 bg-green-900/50 border border-green-500 rounded-lg text-green-200">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded-lg text-red-200">
          {error}
          <button onClick={() => setError('')} className="ml-2 text-red-400 hover:text-red-200">×</button>
        </div>
      )}

      {/* ========== Staff Tab ========== */}
      {activeTab === 'staff' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Staff Accounts</h2>
            <button
              onClick={() => { setShowCreateForm(!showCreateForm); setFormError(''); }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm"
            >
              + Add Staff
            </button>
          </div>

          {/* Create Form */}
          {showCreateForm && (
            <div className="mb-6 p-4 bg-slate-800 border border-gray-700 rounded-xl">
              <h3 className="text-white font-medium mb-3">Create New Staff User</h3>
              {formError && (
                <div className="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
                  {formError}
                </div>
              )}
              <form onSubmit={handleCreateStaff} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    value={staffForm.email}
                    onChange={e => setStaffForm({ ...staffForm, email: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="user@moobaan.com"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Password * (min 8 chars)</label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={staffForm.password}
                    onChange={e => setStaffForm({ ...staffForm, password: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={staffForm.full_name}
                    onChange={e => setStaffForm({ ...staffForm, full_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Role *</label>
                  <select
                    value={staffForm.role}
                    onChange={e => setStaffForm({ ...staffForm, role: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="accounting">Accounting</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Phone</label>
                  <input
                    type="text"
                    value={staffForm.phone}
                    onChange={e => setStaffForm({ ...staffForm, phone: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder="02-xxx-xxxx"
                  />
                </div>
                <div className="flex items-end gap-2">
                  <button
                    type="submit"
                    disabled={formLoading}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm disabled:opacity-50"
                  >
                    {formLoading ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Staff Table */}
          <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Email</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Role</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Created</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {loading ? (
                  <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
                ) : staff.length === 0 ? (
                  <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">No staff users found</td></tr>
                ) : (
                  staff.map(u => (
                    <tr key={u.id} className="hover:bg-slate-700/50">
                      <td className="px-4 py-3 text-white font-medium">{u.full_name}</td>
                      <td className="px-4 py-3 text-gray-300">{u.email}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          u.role === 'super_admin'
                            ? 'bg-purple-900/50 text-purple-300 border border-purple-500'
                            : u.role === 'accounting'
                            ? 'bg-blue-900/50 text-blue-300 border border-blue-500'
                            : 'bg-gray-700 text-gray-300 border border-gray-500'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          u.is_active
                            ? 'bg-green-900/50 text-green-300'
                            : 'bg-red-900/50 text-red-300'
                        }`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-sm">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => openResetPassword(u)}
                            className="px-2 py-1 text-xs bg-yellow-600 hover:bg-yellow-700 text-white rounded"
                            title="Reset Password"
                          >
                            🔑
                          </button>
                          {u.role !== 'super_admin' && (
                            u.is_active ? (
                              <button
                                onClick={() => setConfirmDeactivate({ open: true, user: u })}
                                className="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                                title="Deactivate"
                              >
                                🚫
                              </button>
                            ) : (
                              <button
                                onClick={() => handleReactivateStaff(u)}
                                className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                                title="Reactivate"
                              >
                                ✅
                              </button>
                            )
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

      {/* ========== Residents Tab ========== */}
      {activeTab === 'residents' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Resident Users</h2>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loadResidents()}
                className="px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white text-sm"
                placeholder="Search by name or email..."
              />
              <button
                onClick={loadResidents}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
              >
                Search
              </button>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Email</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Phone</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">House</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Role</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {residentsLoading ? (
                  <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
                ) : residents.length === 0 ? (
                  <tr><td colSpan="6" className="px-4 py-8 text-center text-gray-400">No residents found</td></tr>
                ) : (
                  residents.map(r => (
                    <tr key={r.user_id || r.id} className="hover:bg-slate-700/50">
                      <td className="px-4 py-3 text-white">{r.full_name || r.user?.full_name || '-'}</td>
                      <td className="px-4 py-3 text-gray-300">{r.email || r.user?.email || '-'}</td>
                      <td className="px-4 py-3 text-gray-300">{r.phone || r.user?.phone || '-'}</td>
                      <td className="px-4 py-3 text-gray-300">{r.house_code || r.house?.house_code || '-'}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-1 text-xs rounded-full bg-cyan-900/50 text-cyan-300 border border-cyan-500">
                          {r.role || r.member_role || r.user?.role || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          (r.is_active !== undefined ? r.is_active : r.user?.is_active)
                            ? 'bg-green-900/50 text-green-300'
                            : 'bg-red-900/50 text-red-300'
                        }`}>
                          {(r.is_active !== undefined ? r.is_active : r.user?.is_active) ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <p className="text-gray-500 text-xs mt-2">
            * Resident accounts are managed via the Members page. This is a read-only overview.
          </p>
        </div>
      )}

      {/* ========== Reset Password Modal ========== */}
      {showResetModal && resetTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowResetModal(false)}>
          <div className="bg-slate-800 rounded-xl border border-gray-700 p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">
              🔑 Reset Password
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              Resetting password for: <span className="text-white font-medium">{resetTarget.email}</span>
            </p>
            {formError && (
              <div className="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
                {formError}
              </div>
            )}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">New Password (min 8 chars)</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => { setNewPassword(e.target.value); setFormError(''); }}
                className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                placeholder="Enter new password"
                minLength={8}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowResetModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleResetPassword}
                disabled={resetLoading || newPassword.length < 8}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm disabled:opacity-50"
              >
                {resetLoading ? 'Resetting...' : 'Reset Password'}
              </button>
            </div>
          </div>
        </div>
      )}
      <ConfirmModal
        open={confirmDeactivate.open}
        title="ระงับบัญชีผู้ใช้"
        message={`ต้องการระงับบัญชี "${confirmDeactivate.user?.email || ''}" ใช่หรือไม่? ผู้ใช้จะไม่สามารถเข้าสู่ระบบได้`}
        variant="danger"
        confirmText="ระงับ"
        onConfirm={() => handleDeactivateStaff(confirmDeactivate.user)}
        onCancel={() => setConfirmDeactivate({ open: false, user: null })}
      />
    </div>
  );
}
