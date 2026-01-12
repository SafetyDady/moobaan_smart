import { useState, useEffect } from 'react';
import { housesAPI } from '../../api/client';

export default function Houses() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingHouse, setEditingHouse] = useState(null);
  const [formData, setFormData] = useState({
    house_number: '',
    address: '',
    status: 'active',
  });

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

  const handleCreate = () => {
    setEditingHouse(null);
    setFormData({ house_number: '', address: '', status: 'active' });
    setShowModal(true);
  };

  const handleEdit = (house) => {
    setEditingHouse(house);
    setFormData({
      house_number: house.house_number,
      address: house.address || '',
      status: house.status,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingHouse) {
        await housesAPI.update(editingHouse.id, formData);
      } else {
        await housesAPI.create(formData);
      }
      setShowModal(false);
      loadHouses();
    } catch (error) {
      console.error('Failed to save house:', error);
      alert('Failed to save house');
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

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Houses Management</h1>
        <p className="text-gray-400">Manage village houses and their status</p>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Search</label>
            <input
              type="text"
              placeholder="House number or address..."
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
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={handleCreate} className="btn-primary w-full">
              + Add House
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
                <th>House Number</th>
                <th>Address</th>
                <th>Status</th>
                <th>Members</th>
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
                    <td className="font-medium text-white">{house.house_number}</td>
                    <td className="text-gray-300">{house.address || '-'}</td>
                    <td>
                      <span className={`badge ${house.status === 'active' ? 'badge-success' : 'badge-gray'}`}>
                        {house.status}
                      </span>
                    </td>
                    <td className="text-gray-300">{house.member_count}/3</td>
                    <td className="text-gray-400">
                      {new Date(house.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(house)}
                          className="text-primary-400 hover:text-primary-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(house.id)}
                          className="text-red-400 hover:text-red-300"
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

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">
              {editingHouse ? 'Edit House' : 'Add New House'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  House Number *
                </label>
                <input
                  type="text"
                  required
                  value={formData.house_number}
                  onChange={(e) => setFormData({ ...formData, house_number: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., A-101"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Address
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., 123 Village Road"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Status *
                </label>
                <select
                  required
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="input w-full"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="btn-primary flex-1">
                  {editingHouse ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
