import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { housesAPI } from '../../api/client';

export default function Houses() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [downloadingStatements, setDownloadingStatements] = useState(new Set());

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
                        <span className="text-gray-500 text-sm cursor-not-allowed">Edit</span>
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
    </div>
  );
}