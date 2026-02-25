import { useState, useEffect } from 'react';
import { User, Home, Users, Key, Ban, CheckCircle } from 'lucide-react';
import { usersAPI } from '../../api/client';
import ConfirmModal from '../../components/ConfirmModal';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function UserManagement() {
  const [activeTab, setActiveTab] = useState('staff');

  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirmDeactivate, setConfirmDeactivate] = useState({ open: false, user: null });

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

  const [showResetModal, setShowResetModal] = useState(false);
  const [resetTarget, setResetTarget] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);

  const [residents, setResidents] = useState([]);
  const [residentsLoading, setResidentsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Pagination for staff and residents
  const { sortConfig: staffSortConfig, requestSort: staffRequestSort, sortedData: sortedStaff } = useSort(staff);
  const staffPaged = usePagination(sortedStaff);
  const { sortConfig: resSortConfig, requestSort: resRequestSort, sortedData: sortedResidents } = useSort(residents);
  const residentsPaged = usePagination(sortedResidents);

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
      setError(t('userManagement.loadStaffFailed'));
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

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    setFormError('');
    try {
      await usersAPI.createStaff(staffForm);
      showMsg(`${t('userManagement.createStaffSuccess')} '${staffForm.email}'`);
      setShowCreateForm(false);
      setStaffForm({ email: '', password: '', full_name: '', role: 'accounting', phone: '' });
      loadStaff();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(typeof detail === 'string' ? detail : JSON.stringify(detail) || t('userManagement.createStaffFailed'));
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeactivateStaff = async (user) => {
    setConfirmDeactivate({ open: false, user: null });
    try {
      await usersAPI.deactivateStaff(user.id);
      showMsg(`${t('userManagement.suspendSuccess')} ${user.email}`);
      loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || t('userManagement.suspendFailed'));
    }
  };

  const handleReactivateStaff = async (user) => {
    try {
      await usersAPI.reactivateStaff(user.id);
      showMsg(`${t('userManagement.createStaffSuccess')} - ${user.email}`);
      loadStaff();
    } catch (err) {
      setError(err.response?.data?.detail || t('members.cannotActivate'));
    }
  };

  const openResetPassword = (user) => {
    setResetTarget(user);
    setNewPassword('');
    setShowResetModal(true);
  };

  const handleResetPassword = async () => {
    if (newPassword.length < 8) {
      setFormError(t('userManagement.passwordMinLength'));
      return;
    }
    setResetLoading(true);
    try {
      await usersAPI.resetStaffPassword(resetTarget.id, { new_password: newPassword });
      showMsg(`${t('userManagement.resetPassword')} ${resetTarget.email} ${t('common.success')}`);
      setShowResetModal(false);
    } catch (err) {
      setFormError(err.response?.data?.detail || t('common.error'));
    } finally {
      setResetLoading(false);
    }
  };

  const getRoleLabel = (role) => {
    return t(`roles.${role}`, role);
  };

  const tabs = [
    { key: 'staff', label: `${t('userManagement.staffTab')} (${staff.length})`, icon: <User size={16} /> },
    { key: 'residents', label: `${t('userManagement.residentsTab')} (${residents.length})`, icon: <Home size={16} /> },
  ];

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2">
          {t('userManagement.title')}
        </h1>
        <p className="text-gray-400 mt-1">{t('userManagement.subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
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
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold text-white">{t('userManagement.staffAccounts')}</h2>
            <button
              onClick={() => { setShowCreateForm(!showCreateForm); setFormError(''); }}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm whitespace-nowrap"
            >
              + {t('userManagement.addStaff')}
            </button>
          </div>

          {/* Create Form */}
          {showCreateForm && (
            <div className="mb-6 p-4 bg-slate-800 border border-gray-700 rounded-xl">
              <h3 className="text-white font-medium mb-3">{t('userManagement.createStaff')}</h3>
              {formError && (
                <div className="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
                  {formError}
                </div>
              )}
              <form onSubmit={handleCreateStaff} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('common.email')} *</label>
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
                  <label className="block text-sm text-gray-400 mb-1">{t('userManagement.newPassword')} *</label>
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
                  <label className="block text-sm text-gray-400 mb-1">{t('common.name')} *</label>
                  <input
                    type="text"
                    required
                    value={staffForm.full_name}
                    onChange={e => setStaffForm({ ...staffForm, full_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                    placeholder={t('common.name')}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('common.role')} *</label>
                  <select
                    value={staffForm.role}
                    onChange={e => setStaffForm({ ...staffForm, role: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="accounting">{t('roles.accounting')}</option>
                    <option value="admin">{t('roles.admin')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('common.phone')}</label>
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
                    {formLoading ? t('common.creating') : t('common.create')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm"
                  >
                    {t('common.cancel')}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Staff Table */}
          <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="table-container">
              <table className="w-full">
                <thead className="bg-slate-700">
                  <tr>
                    <SortableHeader label={t('common.name')} sortKey="full_name" sortConfig={staffSortConfig} onSort={staffRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <SortableHeader label={t('common.email')} sortKey="email" sortConfig={staffSortConfig} onSort={staffRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.role')}</th>
                    <SortableHeader label={t('common.status')} sortKey="is_active" sortConfig={staffSortConfig} onSort={staffRequestSort} className="px-4 py-3 text-center text-sm font-medium text-gray-300" />
                    <SortableHeader label={t('common.createdAt')} sortKey="created_at" sortConfig={staffSortConfig} onSort={staffRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {loading ? (
                    <SkeletonTable rows={5} cols={6} />
                  ) : staff.length === 0 ? (
                    <EmptyState icon={<User size={32} />} colSpan={6} />
                  ) : (
                    staffPaged.currentItems.map(u => (
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
                            {getRoleLabel(u.role)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            u.is_active
                              ? 'bg-green-900/50 text-green-300'
                              : 'bg-red-900/50 text-red-300'
                          }`}>
                            {u.is_active ? t('common.active') : t('common.inactive')}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-sm">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString('th-TH') : '-'}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-center gap-2">
                            <button
                              onClick={() => openResetPassword(u)}
                              className="px-2 py-1 text-xs bg-yellow-600 hover:bg-yellow-700 text-white rounded"
                              title={t('userManagement.resetPassword')}
                            >
                              <Key size={14} />
                            </button>
                            {u.role !== 'super_admin' && (
                              u.is_active ? (
                                <button
                                  onClick={() => setConfirmDeactivate({ open: true, user: u })}
                                  className="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded"
                                  title={t('userManagement.suspend')}
                                >
                                  <Ban size={14} />
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleReactivateStaff(u)}
                                  className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded"
                                  title={t('members.reactivate')}
                                >
                                  <CheckCircle size={14} />
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
          {/* Staff Pagination */}
          {!loading && staff.length > 0 && <Pagination {...staffPaged} />}
        </div>
      )}

      {/* ========== Residents Tab ========== */}
      {activeTab === 'residents' && (
        <div>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold text-white">{t('userManagement.residentUsers')}</h2>
            <div className="flex gap-2 w-full sm:w-auto">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && loadResidents()}
                className="flex-1 sm:flex-initial px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white text-sm"
                placeholder={t('userManagement.searchPlaceholder')}
              />
              <button
                onClick={loadResidents}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm whitespace-nowrap"
              >
                {t('common.search')}
              </button>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="table-container">
              <table className="w-full">
                <thead className="bg-slate-700">
                  <tr>
                    <SortableHeader label={t('common.name')} sortKey="full_name" sortConfig={resSortConfig} onSort={resRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <SortableHeader label={t('common.email')} sortKey="email" sortConfig={resSortConfig} onSort={resRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">{t('common.phone')}</th>
                    <SortableHeader label={t('members.house')} sortKey="house_code" sortConfig={resSortConfig} onSort={resRequestSort} className="px-4 py-3 text-left text-sm font-medium text-gray-300" />
                    <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">{t('common.role')}</th>
                    <SortableHeader label={t('common.status')} sortKey="is_active" sortConfig={resSortConfig} onSort={resRequestSort} className="px-4 py-3 text-center text-sm font-medium text-gray-300" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {residentsLoading ? (
                    <SkeletonTable rows={5} cols={6} />
                  ) : residents.length === 0 ? (
                    <EmptyState icon={<Users size={32} />} colSpan={6} isFiltered={!!searchQuery} onClearFilters={() => setSearchQuery('')} />
                  ) : (
                    residentsPaged.currentItems.map(r => (
                      <tr key={r.user_id || r.id} className="hover:bg-slate-700/50">
                        <td className="px-4 py-3 text-white">{r.full_name || r.user?.full_name || '-'}</td>
                        <td className="px-4 py-3 text-gray-300">{r.email || r.user?.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-300">{r.phone || r.user?.phone || '-'}</td>
                        <td className="px-4 py-3 text-gray-300">{r.house_code || r.house?.house_code || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="px-2 py-1 text-xs rounded-full bg-cyan-900/50 text-cyan-300 border border-cyan-500">
                            {getRoleLabel(r.role || r.member_role || r.user?.role || '-')}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            (r.is_active !== undefined ? r.is_active : r.user?.is_active)
                              ? 'bg-green-900/50 text-green-300'
                              : 'bg-red-900/50 text-red-300'
                          }`}>
                            {(r.is_active !== undefined ? r.is_active : r.user?.is_active) ? t('common.active') : t('common.inactive')}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
          {/* Residents Pagination */}
          {!residentsLoading && residents.length > 0 && <Pagination {...residentsPaged} />}
          <p className="text-gray-500 text-xs mt-2">
            * {t('userManagement.residentReadOnly')}
          </p>
        </div>
      )}

      {/* ========== Reset Password Modal ========== */}
      {showResetModal && resetTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowResetModal(false)}>
          <div className="bg-slate-800 rounded-xl border border-gray-700 p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">
              <Key size={16} className="inline mr-1" />{t('userManagement.resetPassword')}
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              {t('userManagement.resetPassword')}: <span className="text-white font-medium">{resetTarget.email}</span>
            </p>
            {formError && (
              <div className="mb-3 p-2 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
                {formError}
              </div>
            )}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">{t('userManagement.newPassword')}</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => { setNewPassword(e.target.value); setFormError(''); }}
                className="w-full px-3 py-2 bg-slate-700 border border-gray-600 rounded-lg text-white"
                placeholder={t('userManagement.newPassword')}
                minLength={8}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowResetModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleResetPassword}
                disabled={resetLoading || newPassword.length < 8}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm disabled:opacity-50"
              >
                {resetLoading ? t('userManagement.resettingPassword') : t('userManagement.resetPassword')}
              </button>
            </div>
          </div>
        </div>
      )}
      <ConfirmModal
        open={confirmDeactivate.open}
        title={t('userManagement.suspendAccount')}
        message={t('userManagement.suspendConfirm')}
        variant="danger"
        confirmText={t('userManagement.suspend')}
        onConfirm={() => handleDeactivateStaff(confirmDeactivate.user)}
        onCancel={() => setConfirmDeactivate({ open: false, user: null })}
      />
    </div>
    </AdminPageWrapper>
  );
}
