import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { housesAPI } from '../../api/client';

const HOUSE_STATUSES = [
  { value: 'ACTIVE', label: 'Active / ใช้งานอยู่', color: 'badge-success' },
  { value: 'VACANT', label: 'Vacant / ว่าง', color: 'badge-gray' },
  { value: 'BANK_OWNED', label: 'Bank Owned / ธนาคารเจ้าของ', color: 'badge-gray' },
  { value: 'SUSPENDED', label: 'Suspended / ระงับ', color: 'badge-gray' },
  { value: 'ARCHIVED', label: 'Archived / เก็บถาวร', color: 'badge-gray' },
];

export default function Houses() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [downloadingStatements, setDownloadingStatements] = useState(new Set());

  // Edit modal state
  const [editingHouse, setEditingHouse] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editLoading, setEditLoading] = useState(false);
  const [editError, setEditError] = useState('');

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
    if (!confirm('Are you sure you want to delete this house?')) return;
    
    try {
      await housesAPI.delete(id);
      loadHouses();
    } catch (error) {
      console.error('Failed to delete house:', error);
      alert('Failed to delete house');
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
      setEditError('ชื่อเจ้าของจำเป็นต้องระบุ');
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
      setEditError(typeof detail === 'string' ? detail : 'ไม่สามารถอัปเดตข้อมูลบ้านได้');
    } finally {
      setEditLoading(false);
    }
  };

  const downloadStatement = async (houseId, format = 'pdf') => {
    setDownloadingStatements(prev => new Set([...prev, `${houseId}-${format}`]));
    try {
      // Get current month/year
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;

      // Use apiClient to get correct baseURL
      const response = await housesAPI.downloadStatement(houseId, year, month, format);

      // Create blob and download
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
      alert(`Download failed: ${error.message}`);
    } finally {
      setDownloadingStatements(prev => {
        const newSet = new Set(prev);
        newSet.delete(`${houseId}-${format}`);
        return newSet;
      });
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Houses Management</h1>
            <p className="text-gray-400">Manage village houses and their status</p>
          </div>
          <div className="flex gap-3">
            <Link to="/admin/add-house" className="btn-primary">
              🏠 Add House / เพิ่มบ้าน
            </Link>
            <Link to="/admin/add-resident" className="btn-secondary">
              👤 Add Resident / เพิ่มผู้อาศัย
            </Link>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Search</label>
            <input
              type="text"
              placeholder="House code or owner name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="VACANT">Vacant</option>
              <option value="BANK_OWNED">Bank Owned</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="ARCHIVED">Archived</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={loadHouses} className="btn-secondary w-full">
              🔄 Refresh
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
                <th>House Code</th>
                <th>Owner Name</th>
                <th>Status</th>
                <th>Zone</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-8">
                    Loading...
                  </td>
                </tr>
              ) : houses.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-gray-400">
                    No houses found
                  </td>
                </tr>
              ) : (
                houses.map((house) => (
                  <tr key={house.id}>
                    <td className="font-medium text-white">{house.house_code}</td>
                    <td className="text-gray-300">{house.owner_name}</td>
                    <td>
                      <span className={`badge ${house.house_status === 'ACTIVE' ? 'badge-success' : 'badge-gray'}`}>
                        {house.house_status}
                      </span>
                    </td>
                    <td className="text-gray-300">{house.zone || '-'}</td>
                    <td className="text-gray-400">
                      {new Date(house.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={() => openEdit(house)}
                          className="text-yellow-400 hover:text-yellow-300 text-sm"
                        >
                          ✏️ Edit
                        </button>
                        <Link
                          to="/admin/add-resident"
                          state={{ house_id: house.id }}
                          className="text-purple-400 hover:text-purple-300 text-sm"
                        >
                          +Resident
                        </Link>
                        <button
                          onClick={() => downloadStatement(house.id, 'pdf')}
                          disabled={downloadingStatements.has(`${house.id}-pdf`)}
                          className="text-green-400 hover:text-green-300 text-sm"
                        >
                          {downloadingStatements.has(`${house.id}-pdf`) ? '📄...' : '📄 PDF'}
                        </button>
                        <button
                          onClick={() => downloadStatement(house.id, 'xlsx')}
                          disabled={downloadingStatements.has(`${house.id}-xlsx`)}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          {downloadingStatements.has(`${house.id}-xlsx`) ? '📊...' : '📊 Excel'}
                        </button>
                        <button
                          onClick={() => handleDelete(house.id)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Delete
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
                <h2 className="text-xl font-bold text-white">แก้ไขข้อมูลบ้าน</h2>
                <p className="text-gray-400 text-sm mt-1">บ้านเลขที่ {editingHouse.house_code}</p>
              </div>
              <button onClick={closeEdit} className="text-gray-400 hover:text-white text-2xl">✕</button>
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
                <label className="block text-sm font-medium text-gray-300 mb-1">ชื่อเจ้าของ *</label>
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
                <label className="block text-sm font-medium text-gray-300 mb-1">สถานะบ้าน</label>
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
                  <label className="block text-sm text-gray-400 mb-1">พื้นที่ใช้สอย</label>
                  <input
                    type="text"
                    value={editForm.floor_area}
                    onChange={(e) => handleEditChange('floor_area', e.target.value)}
                    placeholder="120 ตร.ม."
                    className="input w-full"
                    disabled={editLoading}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">พื้นที่ดิน</label>
                  <input
                    type="text"
                    value={editForm.land_area}
                    onChange={(e) => handleEditChange('land_area', e.target.value)}
                    placeholder="80 ตรว."
                    className="input w-full"
                    disabled={editLoading}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">โซน</label>
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
                <label className="block text-sm text-gray-400 mb-1">หมายเหตุ</label>
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
                ยกเลิก
              </button>
              <button
                onClick={handleEditSave}
                disabled={editLoading}
                className="px-6 py-2 rounded-lg bg-yellow-500 text-black font-semibold hover:bg-yellow-400 disabled:opacity-50"
              >
                {editLoading ? 'กำลังบันทึก...' : '💾 บันทึก'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}