import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Home, UserPlus, RefreshCw, Edit3, FileText, FileSpreadsheet, Save, X as XIcon } from 'lucide-react';
import { housesAPI } from '../../api/client';
import { SkeletonTable } from '../../components/Skeleton';
import ConfirmModal from '../../components/ConfirmModal';
import { useToast } from '../../components/Toast';
import { t } from '../../hooks/useLocale';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';
import AdminPageWrapper from '../../components/AdminPageWrapper';


const HOUSE_STATUSES = [
  { value: 'ACTIVE', label: t('houses.statusActive') },
  { value: 'VACANT', label: t('houses.statusVacant') },
  { value: 'BANK_OWNED', label: t('houses.statusBankOwned') },
  { value: 'SUSPENDED', label: t('houses.statusSuspended') },
  { value: 'ARCHIVED', label: t('houses.statusArchived') },
];

export default function Houses() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [downloadingStatements, setDownloadingStatements] = useState(new Set());
  const toast = useToast();

  // Sorting & Pagination
  const { sortConfig, requestSort, sortedData } = useSort(houses);
  const paged = usePagination(sortedData);

  // Edit modal state
  const [editingHouse, setEditingHouse] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');

  // Confirm modal state
  const [confirmState, setConfirmState] = useState({ open: false, houseId: null });

  useEffect(() => {
    loadHouses();
  }, [search, statusFilter]);

  const loadHouses = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      
      const response = await housesAPI.list(params);
      setHouses(response.data);
    } catch (error) {
      console.error('Failed to load houses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await housesAPI.delete(id);
      toast.success(t('houses.deleteSuccess'));
      loadHouses();
    } catch (error) {
      console.error('Failed to delete house:', error);
      toast.error(t('houses.deleteFailed'));
    }
  };

  // ── Edit House ──────────────────────────────────────────
  const openEdit = (house) => {
    setEditForm({
      owner_name: house.owner_name || '',
      house_status: house.house_status || 'ACTIVE',
      floor_area: house.floor_area || '',
      land_area: house.land_area || '',
      zone: house.zone || '',
      notes: house.notes || '',
    });
    setEditError('');
    setEditingHouse(house);
  };

  const closeEdit = () => {
    setEditingHouse(null);
    setEditForm({});
    setEditError('');
  };

  const handleEditChange = (field, value) => {
    setEditForm(prev => ({ ...prev, [field]: value }));
  };

  const handleEditSave = async () => {
    if (!editForm.owner_name?.trim()) {
      setEditError(t('houses.ownerRequired'));
      return;
    }
    setEditLoading(true);
    setEditError('');
    try {
      await housesAPI.update(editingHouse.id, editForm);
      closeEdit();
      loadHouses();
    } catch (error) {
      console.error('Failed to update house:', error);
      const detail = error.response?.data?.detail;
      setEditError(typeof detail === 'string' ? detail : t('houses.updateFailed'));
    } finally {
      setEditLoading(false);
    }
  };

  const downloadStatement = async (houseId, format = 'pdf') => {
    setDownloadingStatements(prev => new Set([...prev, `${houseId}-${format}`]));
    try {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;

      const response = await housesAPI.downloadStatement(houseId, year, month, format);

      const url = window.URL.createObjectURL(response);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `statement_house${houseId}_${year}_${month}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Download failed:', error);
      toast.error(`${t('houses.downloadFailed')}: ${error.message}`);
    } finally {
      setDownloadingStatements(prev => {
        const newSet = new Set(prev);
        newSet.delete(`${houseId}-${format}`);
        return newSet;
      });
    }
  };

  const getStatusLabel = (status) => {
    const found = HOUSE_STATUSES.find(s => s.value === status);
    return found ? found.label : status;
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('houses.title')}</h1>
            <p className="text-gray-400">{t('houses.subtitle')}</p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <Link to="/admin/add-house" className="btn-primary whitespace-nowrap">
              <Home size={16} className="inline mr-1" />{t('houses.addHouse')}
            </Link>
            <Link to="/admin/add-resident" className="btn-secondary whitespace-nowrap">
              <UserPlus size={16} className="inline mr-1" />{t('houses.addResident')}
            </Link>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 sm:p-6 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">{t('common.search')}</label>
            <input
              type="text"
              placeholder={t('houses.searchPlaceholder')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">{t('common.status')}</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">{t('houses.allStatuses')}</option>
              {HOUSE_STATUSES.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadHouses} className="btn-secondary w-full">
              <RefreshCw size={16} className="inline mr-1" />{t('common.refresh')}
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <SortableHeader label={t('houses.houseCode')} sortKey="house_code" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('houses.ownerName')} sortKey="owner_name" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.status')} sortKey="house_status" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('houses.zone')} sortKey="zone" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.createdAt')} sortKey="created_at" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={6} />
              ) : houses.length === 0 ? (
                <EmptyState
                  icon={<Home size={32} />}
                  colSpan={6}
                  isFiltered={!!(search || statusFilter)}
                  onClearFilters={() => { setSearch(''); setStatusFilter(''); }}
                />
              ) : (
                paged.currentItems.map((house) => (
                  <tr key={house.id}>
                    <td className="font-medium text-white">{house.house_code}</td>
                    <td className="text-gray-300">{house.owner_name}</td>
                    <td>
                      <span className={`badge ${house.house_status === 'ACTIVE' ? 'badge-success' : 'badge-gray'}`}>
                        {getStatusLabel(house.house_status)}
                      </span>
                    </td>
                    <td className="text-gray-300">{house.zone || '-'}</td>
                    <td className="text-gray-400">
                      {new Date(house.created_at).toLocaleDateString('th-TH')}
                    </td>
                    <td>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={() => openEdit(house)}
                          className="text-yellow-400 hover:text-yellow-300 text-sm"
                        >
                          <Edit3 size={14} className="inline mr-1" />{t('common.edit')}
                        </button>
                        <Link
                          to="/admin/add-resident"
                          state={{ house_id: house.id }}
                          className="text-purple-400 hover:text-purple-300 text-sm"
                        >
                          +{t('houses.addResident')}
                        </Link>
                        <button
                          onClick={() => downloadStatement(house.id, 'pdf')}
                          disabled={downloadingStatements.has(`${house.id}-pdf`)}
                          className="text-green-400 hover:text-green-300 text-sm"
                        >
                          {downloadingStatements.has(`${house.id}-pdf`) ? <><FileText size={14} className="inline mr-1" />...</> : <><FileText size={14} className="inline mr-1" />PDF</>}
                        </button>
                        <button
                          onClick={() => downloadStatement(house.id, 'xlsx')}
                          disabled={downloadingStatements.has(`${house.id}-xlsx`)}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          {downloadingStatements.has(`${house.id}-xlsx`) ? <><FileSpreadsheet size={14} className="inline mr-1" />...</> : <><FileSpreadsheet size={14} className="inline mr-1" />Excel</>}
                        </button>
                        <button
                          onClick={() => setConfirmState({ open: true, houseId: house.id })}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          {t('common.delete')}
                        </button>
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
      {!loading && houses.length > 0 && <Pagination {...paged} />}

      {/* ── Edit House Modal ─────────────────────────────────── */}
      {editingHouse && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
          onClick={(e) => { if (e.target === e.currentTarget && !editLoading) closeEdit(); }}
        >
          <div className="bg-gray-800 rounded-xl w-full max-w-lg shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <div>
                <h2 className="text-xl font-bold text-white">{t('houses.editHouse')}</h2>
                <p className="text-gray-400 text-sm mt-1">{t('houses.houseNumber')} {editingHouse.house_code}</p>
              </div>
              <button onClick={closeEdit} className="text-gray-400 hover:text-white text-2xl"><XIcon size={24} /></button>
            </div>

            {/* Form */}
            <div className="p-6 space-y-4">
              {editError && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm">
                  {editError}
                </div>
              )}

              {/* Owner Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">{t('houses.ownerName')} *</label>
                <input
                  type="text"
                  value={editForm.owner_name}
                  onChange={(e) => handleEditChange('owner_name', e.target.value)}
                  className="input w-full"
                  disabled={editLoading}
                />
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">{t('houses.houseStatus')}</label>
                <select
                  value={editForm.house_status}
                  onChange={(e) => handleEditChange('house_status', e.target.value)}
                  className="input w-full"
                  disabled={editLoading}
                >
                  {HOUSE_STATUSES.map(s => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              {/* Optional: floor_area, land_area, zone */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('houses.floorArea')}</label>
                  <input
                    type="text"
                    value={editForm.floor_area}
                    onChange={(e) => handleEditChange('floor_area', e.target.value)}
                    placeholder={t('houses.areaPlaceholder')}
                    className="input w-full"
                    disabled={editLoading}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('houses.landArea')}</label>
                  <input
                    type="text"
                    value={editForm.land_area}
                    onChange={(e) => handleEditChange('land_area', e.target.value)}
                    placeholder={t('houses.landPlaceholder')}
                    className="input w-full"
                    disabled={editLoading}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">{t('houses.zone')}</label>
                  <input
                    type="text"
                    value={editForm.zone}
                    onChange={(e) => handleEditChange('zone', e.target.value)}
                    placeholder="A"
                    className="input w-full"
                    disabled={editLoading}
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('common.notes')}</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => handleEditChange('notes', e.target.value)}
                  rows={2}
                  className="input w-full"
                  disabled={editLoading}
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-700">
              <button
                onClick={closeEdit}
                disabled={editLoading}
                className="px-4 py-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleEditSave}
                disabled={editLoading}
                className="px-6 py-2 rounded-lg bg-yellow-500 text-black font-semibold hover:bg-yellow-400 disabled:opacity-50"
              >
                {editLoading ? t('common.saving') : <><Save size={16} className="inline mr-1" />{t('common.save')}</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirm Modal */}
      <ConfirmModal
        open={confirmState.open}
        title={t('houses.confirmDelete')}
        message={t('houses.confirmDeleteMsg')}
        variant="danger"
        confirmText={t('common.delete')}
        onConfirm={() => handleDelete(confirmState.houseId)}
        onCancel={() => setConfirmState({ open: false, houseId: null })}
      />
    </div>
    </AdminPageWrapper>
  );
}
