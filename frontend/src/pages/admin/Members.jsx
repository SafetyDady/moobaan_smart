import { useState, useEffect } from 'react';
import { membersAPI, housesAPI } from '../../api/client';

export default function Members() {
  const [members, setMembers] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [houseFilter, setHouseFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingMember, setEditingMember] = useState(null);
  const [formData, setFormData] = useState({
    house_id: '',
    name: '',
    phone: '',
    email: '',
    role: 'family',
  });

  useEffect(() => {
    loadData();
  }, [houseFilter]);

  const loadData = async () => {
    try {
      const [membersRes, housesRes] = await Promise.all([
        membersAPI.list(houseFilter ? { house_id: houseFilter } : {}),
        housesAPI.list(),
      ]);
      setMembers(membersRes.data);
      setHouses(housesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMemberCount = (houseId) => {
    return members.filter(m => m.house_id === houseId).length;
  };

  const canAddMember = (houseId) => {
    return getMemberCount(houseId) < 3;
  };

  const handleCreate = () => {
    setEditingMember(null);
    setFormData({
      house_id: '',
      name: '',
      phone: '',
      email: '',
      role: 'family',
    });
    setShowModal(true);
  };

  const handleEdit = (member) => {
    setEditingMember(member);
    setFormData({
      house_id: member.house_id,
      name: member.name,
      phone: member.phone,
      email: member.email || '',
      role: member.role,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate 3-member limit
    if (!editingMember && !canAddMember(parseInt(formData.house_id))) {
      alert('This house already has 3 members (maximum limit)');
      return;
    }

    try {
      const submitData = {
        ...formData,
        house_id: parseInt(formData.house_id),
        email: formData.email || null,
      };

      if (editingMember) {
        await membersAPI.update(editingMember.id, submitData);
      } else {
        await membersAPI.create(submitData);
      }
      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to save member:', error);
      alert(error.response?.data?.detail || 'Failed to save member');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this member?')) return;
    
    try {
      await membersAPI.delete(id);
      loadData();
    } catch (error) {
      console.error('Failed to delete member:', error);
      alert('Failed to delete member');
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Members Management</h1>
        <p className="text-gray-400">Manage house members (max 3 per house)</p>
      </div>

      {/* Filters */}
      <div className="card p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Filter by House</label>
            <select
              value={houseFilter}
              onChange={(e) => setHouseFilter(e.target.value)}
              className="input w-full"
            >
              <option value="">All Houses</option>
              {houses.map((house) => (
                <option key={house.id} value={house.id}>
                  {house.house_number} ({house.member_count}/3 members)
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={handleCreate} className="btn-primary w-full">
              + Add Member
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
                <th>Name</th>
                <th>House</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Role</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-8">
                    Loading...
                  </td>
                </tr>
              ) : members.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-gray-400">
                    No members found
                  </td>
                </tr>
              ) : (
                members.map((member) => (
                  <tr key={member.id}>
                    <td className="font-medium text-white">{member.name}</td>
                    <td className="text-gray-300">{member.house_number}</td>
                    <td className="text-gray-300">{member.phone}</td>
                    <td className="text-gray-300">{member.email || '-'}</td>
                    <td>
                      <span className={`badge ${member.role === 'owner' ? 'badge-info' : 'badge-gray'}`}>
                        {member.role}
                      </span>
                    </td>
                    <td className="text-gray-400">
                      {new Date(member.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(member)}
                          className="text-primary-400 hover:text-primary-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(member.id)}
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
          <div className="card p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">
              {editingMember ? 'Edit Member' : 'Add New Member'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  House *
                </label>
                <select
                  required
                  value={formData.house_id}
                  onChange={(e) => setFormData({ ...formData, house_id: e.target.value })}
                  className="input w-full"
                  disabled={editingMember}
                >
                  <option value="">Select House</option>
                  {houses.map((house) => {
                    const count = getMemberCount(house.id);
                    const canAdd = count < 3 || (editingMember && editingMember.house_id === house.id);
                    return (
                      <option 
                        key={house.id} 
                        value={house.id}
                        disabled={!canAdd}
                      >
                        {house.house_number} ({count}/3 members) {!canAdd && '- FULL'}
                      </option>
                    );
                  })}
                </select>
                {formData.house_id && !editingMember && (
                  <p className="text-xs text-gray-400 mt-1">
                    {getMemberCount(parseInt(formData.house_id))}/3 members in this house
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="Full name"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Phone *
                </label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input w-full"
                  placeholder="081-234-5678"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input w-full"
                  placeholder="email@example.com"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Role *
                </label>
                <select
                  required
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="input w-full"
                >
                  <option value="owner">Owner</option>
                  <option value="family">Family</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="submit" className="btn-primary flex-1">
                  {editingMember ? 'Update' : 'Create'}
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
