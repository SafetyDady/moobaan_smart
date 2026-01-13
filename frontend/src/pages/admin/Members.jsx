import { useState, useEffect } from 'react';
import { usersAPI, housesAPI } from '../../api/client';
import { Link } from 'react-router-dom';

export default function Members() {
  const [residents, setResidents] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [houseFilter, setHouseFilter] = useState('');
  const [resetPasswordModal, setResetPasswordModal] = useState({
    show: false,
    residentName: '',
    email: '',
    temporaryPassword: ''
  });
  
  // Edit modal state
  const [editModal, setEditModal] = useState({
    show: false,
    resident: null,
    formData: {}
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
    // Count only active members
    return residents.filter(r => r.house && r.house.id === houseId && r.is_active).length;
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
      loadData(); // Refresh list
      
      if (response.data.success) {
        alert('Resident updated successfully');
      }
    } catch (error) {
      console.error('Failed to update resident:', error);
      
      // Handle error messages from backend
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'object') {
          alert(detail.error_en || detail.error_th || 'Failed to update resident');
        } else {
          alert(detail);
        }
      } else {
        alert('Failed to update resident');
      }
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    const { resident, formData } = editModal;
    
    // Basic validation
    if (!formData.full_name.trim()) {
      alert('Full name is required');
      return;
    }
    if (!formData.email.trim()) {
      alert('Email is required');
      return;
    }

    await updateResident(resident.id, formData);
    setEditModal({ show: false, resident: null, formData: {} });
    // Refresh data to show updated counts
    loadData();
  };

  const handleDeactivate = async (resident) => {
    const action = resident.is_active ? 'deactivate' : 'reactivate';
    const actionText = resident.is_active ? 'deactivate (soft delete)' : 'reactivate';
    
    if (!confirm(`Are you sure you want to ${actionText} ${resident.full_name}?`)) return;
    
    try {
      if (resident.is_active) {
        await usersAPI.deactivateResident(resident.id);
        alert('Resident deactivated successfully');
      } else {
        await usersAPI.reactivateResident(resident.id);
        alert('Resident reactivated successfully');
      }
      loadData(); // Refresh list
    } catch (error) {
      // CRITICAL: Handle 409 as warning (not error) - member limit reached
      if (error.response?.status === 409) {
        const detail = error.response.data?.detail;
        
        // Handle HOUSE_MEMBER_LIMIT_REACHED as warning
        if (detail?.code === 'HOUSE_MEMBER_LIMIT_REACHED') {
          // Show bilingual warning message (Thai + English)
          const message = `${detail.message_th}\n\n${detail.message_en}`;
          alert(message);
          return; // Return early - DO NOT console.error, DO NOT show "Failed to reactivate"
        }
        
        // Handle other 409 cases
        if (detail?.error_th || detail?.error_en) {
          const message = `${detail.error_th || detail.error_en}\n\n${detail.error_en || detail.error_th}`;
          alert(message);
          return;
        }
        
        if (typeof detail === 'string') {
          alert(detail);
          return;
        }
        
        // Fallback for unhandled 409
        alert('Operation cannot be completed due to current state');
        return;
      }
      
      // Handle all other errors (500, network, etc.) normally with console.error
      console.error(`Failed to ${action} resident:`, error);
      
      // Handle error messages from backend for non-409 errors
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        
        // Handle other structured error responses
        if (typeof detail === 'object' && detail.code && detail.code !== 'HOUSE_MEMBER_LIMIT_REACHED') {
          if (detail.message_th && detail.message_en) {
            const message = `${detail.message_th}\n\n${detail.message_en}`;
            alert(message);
            return;
          }
        }
        
        // Legacy error format handling
        if (detail.error_en || detail.error_th) {
          alert(`${detail.error_th || detail.error_en}\n\n${detail.error_en || detail.error_th}`);
          return;
        }
        
        // String error message
        if (typeof detail === 'string') {
          alert(detail);
          return;
        }
      }
      
      // Generic error message for unexpected errors
      alert(`Failed to ${action} resident. Please try again.`);
    }
  };

  const handleResetPassword = async (resident) => {
    if (!confirm(`Generate new temporary password for ${resident.full_name}? Old password will stop working.`)) {
      return;
    }

    try {
      const response = await usersAPI.resetPassword(resident.id);
      const { temporary_password } = response.data;
      
      // Show temp password in modal
      setResetPasswordModal({
        show: true,
        residentName: resident.full_name,
        email: resident.email,
        temporaryPassword: temporary_password
      });
      
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('Failed to reset password');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Password copied to clipboard!');
    });
  };

  const closeResetPasswordModal = () => {
    setResetPasswordModal({
      show: false,
      residentName: '',
      email: '',
      temporaryPassword: ''
    });
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Residents Directory</h1>
        <p className="text-gray-400">View all residents (max 3 per house)</p>
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
                  {house.house_code} ({getMemberCount(house.id)}/3 members)
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
                <th>Name</th>
                <th>House</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" className="text-center py-8">
                    Loading...
                  </td>
                </tr>
              ) : residents.length === 0 ? (
                <tr>
                  <td colSpan="8" className="text-center py-8 text-gray-400">
                    No residents found
                  </td>
                </tr>
              ) : (
                residents.map((resident) => (
                  <tr key={resident.id} className={!resident.is_active ? "opacity-60" : ""}>
                    <td className="font-medium text-white">{resident.full_name}</td>
                    <td className="text-gray-300">{resident.house?.house_code || '-'}</td>
                    <td className="text-gray-300">{resident.phone || '-'}</td>
                    <td className="text-gray-300">{resident.email || '-'}</td>
                    <td>
                      <span className={`badge ${resident.role === 'owner' ? 'badge-info' : 'badge-gray'}`}>
                        {resident.role}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${resident.is_active ? 'badge-success' : 'badge-warning'}`}>
                        {resident.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="text-gray-400">
                      {new Date(resident.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(resident)}
                          className="text-primary-400 hover:text-primary-300 text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleResetPassword(resident)}
                          className="text-yellow-400 hover:text-yellow-300 text-sm"
                        >
                          Reset Password
                        </button>
                        <button
                          onClick={() => handleDeactivate(resident)}
                          className={`text-sm ${
                            resident.is_active 
                              ? "text-orange-400 hover:text-orange-300" 
                              : "text-green-400 hover:text-green-300"
                          }`}
                        >
                          {resident.is_active ? 'Deactivate' : 'Reactivate'}
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

      {/* Reset Password Modal */}
      {resetPasswordModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <div className="mb-4">
              <h3 className="text-xl font-bold text-white mb-2">🔑 Password Reset Successful</h3>
              <p className="text-gray-300">
                New temporary password for <span className="font-medium text-white">{resetPasswordModal.residentName}</span>:
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">Email:</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={resetPasswordModal.email} 
                  readOnly 
                  className="input flex-1 text-sm"
                />
                <button 
                  onClick={() => copyToClipboard(resetPasswordModal.email)}
                  className="btn-outline px-3 text-sm"
                >
                  📋
                </button>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-2">Temporary Password:</label>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={resetPasswordModal.temporaryPassword} 
                  readOnly 
                  className="input flex-1 text-sm font-mono bg-yellow-500/10 border-yellow-500/30 text-yellow-200"
                />
                <button 
                  onClick={() => copyToClipboard(resetPasswordModal.temporaryPassword)}
                  className="btn-outline px-3 text-sm border-yellow-500/30 text-yellow-200 hover:bg-yellow-500/10"
                >
                  📋
                </button>
              </div>
            </div>

            <div className="bg-red-500/10 border border-red-500/20 rounded p-4 mb-6">
              <div className="flex items-start gap-3">
                <span className="text-red-400 text-xl">⚠️</span>
                <div className="text-red-300 text-sm">
                  <p className="font-medium mb-1">Important Security Notice:</p>
                  <ul className="list-disc list-inside space-y-1 text-red-200">
                    <li>This password will NOT be shown again</li>
                    <li>Save it securely and provide to the resident</li>
                    <li>User must change password on first login</li>
                    <li>Do not store this password anywhere permanent</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={closeResetPasswordModal}
                className="btn-primary flex-1"
              >
                I've Saved It Securely
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Resident Modal */}
      {editModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Edit Resident</h3>
            
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Full Name *</label>
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
                <label className="block text-sm text-gray-400 mb-2">Email *</label>
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
                <label className="block text-sm text-gray-400 mb-2">Phone</label>
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
                <label className="block text-sm text-gray-400 mb-2">Role *</label>
                <select
                  value={editModal.formData.role}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, role: e.target.value }
                  }))}
                  className="input w-full"
                  required
                >
                  <option value="owner">Owner</option>
                  <option value="resident">Resident</option>
                  <option value="tenant">Tenant</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">House</label>
                <select
                  value={editModal.formData.house_id}
                  onChange={(e) => setEditModal(prev => ({
                    ...prev,
                    formData: { ...prev.formData, house_id: e.target.value }
                  }))}
                  className="input w-full"
                >
                  <option value="">Select House</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} ({getMemberCount(house.id)}/3 active members)
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
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
