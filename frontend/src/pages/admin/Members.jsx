import { useState, useEffect } from 'react';
import { usersAPI, housesAPI } from '../../api/client';
import { Link } from 'react-router-dom';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function Members() {
  const [residents, setResidents] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [houseFilter, setHouseFilter] = useState('');
  const [confirmDeactivate, setConfirmDeactivate] = useState({ open: false, resident: null });
  const toast = useToast();

  // Sorting & Pagination
  const { sortConfig, requestSort, sortedData } = useSort(residents);
  const paged = usePagination(sortedData);
  
  // Error/Warning modal state
  const [messageModal, setMessageModal] = useState({
    show: false,
    type: 'warning',
    title: '',
    message_th: '',
    message_en: '',
    showDetails: false,
    errorDetails: null
  });
  
  // Edit modal state
  const [editModal, setEditModal] = useState({
    show: false,
    resident: null,
    formData: {}
  });

  // Phase D.2: Force Logout confirmation modal
  const [forceLogoutModal, setForceLogoutModal] = useState({
    show: false,
    resident: null,
    loading: false
  });

  // Remove from house confirmation modal
  const [removeHouseModal, setRemoveHouseModal] = useState({
    show: false,
    resident: null,
    loading: false
  });

  useEffect(() => {
    loadData();
  }, [houseFilter]);

  const loadData = async () => {
    try {
      const [residentsRes, housesRes] = await Promise.all([
        usersAPI.listResidents(houseFilter ? { house_id: houseFilter } : {}),
        housesAPI.list(),
      ]);
      setResidents(residentsRes.data.residents || []);
      setHouses(housesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMemberCount = (houseId) => {
    return residents.filter(r => r.house && r.house.id === houseId && r.is_active).length;
  };

  const canReactivateResident = (resident) => {
    if (resident.is_active) return true;
    if (!resident.house) return false;
    const activeCount = getMemberCount(resident.house.id);
    return activeCount < 3;
  };

  const getReactivateTooltip = (resident) => {
    if (resident.is_active) return null;
    if (!resident.house) return t('members.noHouseAssigned');
    const activeCount = getMemberCount(resident.house.id);
    if (activeCount >= 3) {
      return t('members.houseFull');
    }
    return null;
  };

  const handleEdit = (resident) => {
    setEditModal({
      show: true,
      resident,
      formData: {
        full_name: resident.full_name || '',
        email: resident.email || '',
        phone: resident.phone || '',
        role: resident.role || 'resident',
        house_id: resident.house?.id || ''
      }
    });
  };

  const updateResident = async (id, data) => {
    try {
      const response = await usersAPI.updateResident(id, data);
      loadData();
      if (response.data.success) {
        toast.success(t('members.updateSuccess'));
      }
    } catch (error) {
      console.error('Failed to update resident:', error);
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'object') {
          toast.error(detail.error_en || detail.error_th || t('members.updateFailed'));
        } else {
          toast.error(detail);
        }
      } else {
        toast.error(t('members.updateFailed'));
      }
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const { resident, formData } = editModal;
    
    if (!formData.full_name.trim()) {
      toast.warning(t('members.nameRequired'));
      return;
    }
    if (!formData.email.trim()) {
      toast.warning(t('members.emailRequired'));
      return;
    }

    await updateResident(resident.id, formData);
    setEditModal({ show: false, resident: null, formData: {} });
    loadData();
  };

  const handleDeactivate = async (resident) => {
    const action = resident.is_active ? 'deactivate' : 'reactivate';
    
    try {
      if (resident.is_active) {
        await usersAPI.deactivateResident(resident.id);
        setMessageModal({
          show: true,
          type: 'success',
          title: t('common.success'),
          message_th: t('members.deactivateSuccess'),
          message_en: '',
          showDetails: false,
          errorDetails: null
        });
      } else {
        await usersAPI.reactivateResident(resident.id);
        setMessageModal({
          show: true,
          type: 'success',
          title: `✅ ${t('common.success')}`,
          message_th: t('members.reactivateSuccess'),
          message_en: '',
          showDetails: false,
          errorDetails: null
        });
      }
      loadData();
    } catch (error) {
      if (error.response?.status === 409) {
        const detail = error.response.data?.detail;
        
        if (detail?.code === 'HOUSE_MEMBER_LIMIT_REACHED') {
          setMessageModal({
            show: true,
            type: 'warning',
            title: t('members.cannotActivate'),
            message_th: detail.message_th || t('members.houseFull'),
            message_en: '',
            showDetails: false,
            errorDetails: null
          });
          return;
        }
        
        if (detail?.error_th || detail?.error_en) {
          toast.error(detail.error_th || detail.error_en);
          return;
        }
        
        if (typeof detail === 'string') {
          toast.error(detail);
          return;
        }
        
        toast.error(t('members.cannotChangeStatus'));
        return;
      }
      
      console.error(`Failed to ${action} resident:`, error);
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        
        if (typeof detail === 'object' && detail.code && detail.code !== 'HOUSE_MEMBER_LIMIT_REACHED') {
          if (detail.message_th) {
            toast.error(detail.message_th);
            return;
          }
        }
        
        if (detail.error_th) {
          toast.error(detail.error_th);
          return;
        }
        
        if (typeof detail === 'string') {
          toast.error(detail);
          return;
        }
      }
      
      toast.error(t('members.toggleFailed'));
    }
  };

  // Handle Remove from House
  const handleRemoveFromHouse = (resident) => {
    if (!resident.house) return;
    setRemoveHouseModal({
      show: true,
      resident,
      loading: false
    });
  };

  const confirmRemoveFromHouse = async () => {
    const { resident } = removeHouseModal;
    if (!resident || !resident.house) return;

    setRemoveHouseModal(prev => ({ ...prev, loading: true }));

    try {
      const response = await usersAPI.removeFromHouse(resident.id, resident.house.id);
      setRemoveHouseModal({ show: false, resident: null, loading: false });

      setMessageModal({
        show: true,
        type: 'success',
        title: `✅ ${t('members.removeSuccess')}`,
        message_th: response.data.message_th || `${t('members.removeFromHouse')} ${resident.full_name} - ${resident.house.house_code}  ${t('common.success')}`,
        message_en: '',
        showDetails: false,
        errorDetails: null
      });

      if (response.data.user_deactivated) {
        setMessageModal(prev => ({
          ...prev,
          message_th: prev.message_th + `\n⚠️ ${t('members.noHouseAssigned')} — auto deactivated`,
        }));
      }

      loadData();
    } catch (error) {
      console.error('Failed to remove from house:', error);
      setRemoveHouseModal({ show: false, resident: null, loading: false });
      const detail = error.response?.data?.detail;
      setMessageModal({
        show: true,
        type: 'error',
        title: `❌ ${t('members.removeFailed')}`,
        message_th: typeof detail === 'object' ? (detail.error_th || t('common.error')) : (detail || t('common.error')),
        message_en: '',
        showDetails: false,
        errorDetails: null
      });
    }
  };

  // Phase D.2: Handle Force Logout
  const handleForceLogout = (resident) => {
    setForceLogoutModal({
      show: true,
      resident,
      loading: false
    });
  };

  const confirmForceLogout = async () => {
    const { resident } = forceLogoutModal;
    if (!resident) return;

    setForceLogoutModal(prev => ({ ...prev, loading: true }));

    try {
      await usersAPI.revokeResidentSession(resident.id);
      
      setForceLogoutModal({ show: false, resident: null, loading: false });
      
      setMessageModal({
        show: true,
        type: 'success',
        title: `✅ ${t('members.forceLogoutSuccess')}`,
        message_th: `${t('members.forceLogout')} ${resident.full_name} ${t('common.success')}\n${t('members.forceLogoutEffect2')}`,
        message_en: '',
        showDetails: false,
        errorDetails: null
      });
    } catch (error) {
      console.error('Failed to force logout:', error);
      setForceLogoutModal({ show: false, resident: null, loading: false });
      
      const detail = error.response?.data?.detail;
      setMessageModal({
        show: true,
        type: 'error',
        title: `❌ ${t('members.forceLogoutFailed')}`,
        message_th: detail?.message_th || t('members.forceLogoutFailed'),
        message_en: '',
        showDetails: false,
        errorDetails: null
      });
    }
  };

  const getRoleLabel = (role) => {
    return t(`roles.${role}`, role);
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('members.title')}</h1>
          <p className="text-gray-400">{t('members.subtitle')}</p>
        </div>
        <Link
          to="/admin/add-resident"
          className="btn-primary flex items-center gap-2 whitespace-nowrap self-start"
        >
          <span className="text-lg">+</span> {t('members.addResident')}
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4 sm:p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">{t('members.filterByHouse')}</label>
            <select
              value={houseFilter}
              onChange={(e) => setHouseFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">{t('members.allHouses')}</option>
              {houses.map((house) => (
                <option key={house.id} value={house.id}>
                  {house.house_code} ({getMemberCount(house.id)}/3 {t('members.members')})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <SortableHeader label={t('common.name')} sortKey="full_name" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('members.house')} sortKey="house.house_code" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.phone')} sortKey="phone" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.email')} sortKey="email" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('common.role')}</th>
                <SortableHeader label={t('common.status')} sortKey="is_active" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.createdAt')} sortKey="created_at" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={8} />
              ) : residents.length === 0 ? (
                <EmptyState
                  icon="👥"
                  colSpan={8}
                  isFiltered={!!houseFilter}
                  onClearFilters={() => setHouseFilter('')}
                />
              ) : (
                paged.currentItems.map((resident) => (
                  <tr key={resident.id} className={!resident.is_active ? "opacity-60" : ""}>
                    <td className="font-medium text-white">{resident.full_name}</td>
                    <td className="text-gray-300">{resident.house?.house_code || '-'}</td>
                    <td className="text-gray-300">{resident.phone || '-'}</td>
                    <td className="text-gray-300">{resident.email || '-'}</td>
                    <td>
                      <span className={`badge ${resident.role === 'owner' ? 'badge-info' : 'badge-gray'}`}>
                        {getRoleLabel(resident.role)}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${resident.is_active ? 'badge-success' : 'badge-warning'}`}>
                        {resident.is_active ? t('common.active') : t('common.inactive')}
                      </span>
                    </td>
                    <td className="text-gray-400">
                      {new Date(resident.created_at).toLocaleDateString('th-TH')}
                    </td>
                    <td>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={() => handleEdit(resident)}
                          className="text-primary-400 hover:text-primary-300 text-sm"
                        >
                          {t('common.edit')}
                        </button>
                        {resident.is_active && (
                          <button
                            onClick={() => handleForceLogout(resident)}
                            className="text-red-400 hover:text-red-300 text-sm"
                            title={t('members.forceLogout')}
                          >
                            {t('members.forceLogout')}
                          </button>
                        )}
                        {resident.is_active && resident.house && (
                          <button
                            onClick={() => handleRemoveFromHouse(resident)}
                            className="text-purple-400 hover:text-purple-300 text-sm"
                            title={t('members.removeFromHouse')}
                          >
                            {t('members.removeFromHouse')}
                          </button>
                        )}
                        {resident.is_active ? (
                          <button
                            onClick={() => setConfirmDeactivate({ open: true, resident })}
                            className="text-orange-400 hover:text-orange-300 text-sm"
                          >
                            {t('members.deactivate')}
                          </button>
                        ) : (
                          <div className="relative group">
                            <button
                              onClick={() => canReactivateResident(resident) && setConfirmDeactivate({ open: true, resident })}
                              disabled={!canReactivateResident(resident)}
                              className={`text-sm ${
                                canReactivateResident(resident)
                                  ? "text-green-400 hover:text-green-300 cursor-pointer" 
                                  : "text-gray-500 cursor-not-allowed"
                              }`}
                            >
                              {t('members.reactivate')}
                            </button>
                            {!canReactivateResident(resident) && getReactivateTooltip(resident) && (
                              <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10 pointer-events-none">
                                <div>{getReactivateTooltip(resident)}</div>
                              </div>
                            )}
                          </div>
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

      {/* Pagination */}
      {!loading && residents.length > 0 && <Pagination {...paged} />}

      {/* Remove from House Confirmation Modal */}
      {removeHouseModal.show && removeHouseModal.resident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">⚠️ {t('members.removeFromHouse')}</h3>

            <div className="space-y-3 mb-6">
              <p className="text-gray-300">
                {t('members.confirmRemoveHouse')}
              </p>
              <div className="bg-gray-700 p-3 rounded">
                <p className="text-white font-medium">{removeHouseModal.resident.full_name}</p>
                <p className="text-gray-400 text-sm">
                  🏠 {t('members.house')}: {removeHouseModal.resident.house?.house_code || '-'}
                </p>
                <p className="text-gray-400 text-sm">
                  📱 {t('common.phone')}: {removeHouseModal.resident.phone || '-'}
                </p>
              </div>
              <div className="text-yellow-400 text-sm">
                <p>⚠️ {t('members.forceLogoutWarning')}</p>
                <ul className="list-disc list-inside ml-2 mt-1 text-gray-300">
                  <li>{t('members.removeEffect1')} {removeHouseModal.resident.house?.house_code}</li>
                  <li>{t('members.removeEffect2')}</li>
                  <li>{t('members.removeEffect3')}</li>
                </ul>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setRemoveHouseModal({ show: false, resident: null, loading: false })}
                disabled={removeHouseModal.loading}
                className="btn-outline flex-1"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={confirmRemoveFromHouse}
                disabled={removeHouseModal.loading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded flex-1 disabled:opacity-50"
              >
                {removeHouseModal.loading ? t('common.processing') : t('members.removeFromHouse')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Phase D.2: Force Logout Confirmation Modal */}
      {forceLogoutModal.show && forceLogoutModal.resident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">⚠️ {t('members.confirmForceLogout')}</h3>
            
            <div className="space-y-3 mb-6">
              <p className="text-gray-300">
                {t('members.forceLogoutDesc')}
              </p>
              <div className="bg-gray-700 p-3 rounded">
                <p className="text-white font-medium">{forceLogoutModal.resident.full_name}</p>
                <p className="text-gray-400 text-sm">
                  {t('members.house')}: {forceLogoutModal.resident.house?.house_code || '-'}
                </p>
                <p className="text-gray-400 text-sm">
                  {t('common.phone')}: {forceLogoutModal.resident.phone || '-'}
                </p>
              </div>
              <div className="text-yellow-400 text-sm">
                <p>⚠️ {t('members.forceLogoutWarning')}</p>
                <ul className="list-disc list-inside ml-2 mt-1 text-gray-300">
                  <li>{t('members.forceLogoutEffect1')}</li>
                  <li>{t('members.forceLogoutEffect2')}</li>
                </ul>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setForceLogoutModal({ show: false, resident: null, loading: false })}
                disabled={forceLogoutModal.loading}
                className="btn-outline flex-1"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={confirmForceLogout}
                disabled={forceLogoutModal.loading}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex-1 disabled:opacity-50"
              >
                {forceLogoutModal.loading ? t('common.processing') : t('members.forceLogout')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Resident Modal */}
      {editModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">{t('members.editResident')}</h3>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">{t('members.fullName')} *</label>
                <input
                  type="text"
                  value={editModal.formData.full_name}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, full_name: e.target.value }
                  }))}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">{t('common.email')} *</label>
                <input
                  type="email"
                  value={editModal.formData.email}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, email: e.target.value }
                  }))}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">{t('common.phone')}</label>
                <input
                  type="tel"
                  value={editModal.formData.phone}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, phone: e.target.value }
                  }))}
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">{t('common.role')} *</label>
                <select
                  value={editModal.formData.role}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, role: e.target.value }
                  }))}
                  className="input w-full"
                  required
                >
                  <option value="owner">{t('roles.owner')}</option>
                  <option value="resident">{t('roles.resident')}</option>
                  <option value="tenant">{t('roles.tenant')}</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">{t('members.house')}</label>
                <select
                  value={editModal.formData.house_id}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, house_id: e.target.value }
                  }))}
                  className="input w-full"
                >
                  <option value="">{t('members.selectHouse')}</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} ({getMemberCount(house.id)}/3 {t('members.activeMembers')})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setEditModal({ show: false, resident: null, formData: {} })}
                  className="btn-outline flex-1"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                >
                  {t('members.saveChanges')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Message Modal (Success/Warning/Error) */}
      {messageModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`rounded-lg p-6 w-full max-w-md ${
            messageModal.type === 'success' ? 'bg-green-800' :
            messageModal.type === 'warning' ? 'bg-yellow-800' : 
            'bg-red-800'
          }`}>
            <div className="mb-4">
              <h3 className="text-xl font-bold text-white mb-2">{messageModal.title}</h3>
              <div className="space-y-2">
                <p className="text-gray-100 whitespace-pre-line">{messageModal.message_th}</p>
                {messageModal.message_en && (
                  <p className="text-gray-300 text-sm">{messageModal.message_en}</p>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <button 
                onClick={() => setMessageModal({ show: false, type: 'warning', title: '', message_th: '', message_en: '', showDetails: false, errorDetails: null })}
                className="btn-primary flex-1"
              >
                {t('common.ok')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deactivate/Reactivate Confirm Modal */}
      <ConfirmModal
        open={confirmDeactivate.open}
        title={confirmDeactivate.resident?.is_active ? t('members.confirmDeactivate') : t('members.confirmReactivate')}
        message={confirmDeactivate.resident ? `${confirmDeactivate.resident.is_active ? t('members.confirmDeactivate') : t('members.confirmReactivate')} ${confirmDeactivate.resident.full_name}?` : ''}
        variant={confirmDeactivate.resident?.is_active ? 'warning' : 'info'}
        confirmText={confirmDeactivate.resident?.is_active ? t('members.deactivate') : t('members.reactivate')}
        onConfirm={() => { if (confirmDeactivate.resident) handleDeactivate(confirmDeactivate.resident); }}
        onCancel={() => setConfirmDeactivate({ open: false, resident: null })}
      />
    </div>
    </AdminPageWrapper>
  );
}
