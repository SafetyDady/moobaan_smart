import { useState, useEffect } from 'react';
import { usersAPI, housesAPI } from '../../api/client';
import { Link } from 'react-router-dom';

export default function Members() {
  const [residents, setResidents] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [houseFilter, setHouseFilter] = useState('');
  // NOTE: Reset Password removed - Residents are OTP-only
  
  // Error/Warning modal state
  const [messageModal, setMessageModal] = useState({
    show: false,
    type: 'warning', // 'warning' or 'error'
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

  const canReactivateResident = (resident) => {
    // Can reactivate if resident is inactive AND house has less than 3 active members
    if (resident.is_active) return true; // Already active, show deactivate
    if (!resident.house) return false; // No house mapping
    
    const activeCount = getMemberCount(resident.house.id);
    return activeCount < 3;
  };

  const getReactivateTooltip = (resident) => {
    if (resident.is_active) return null;
    if (!resident.house) return 'No house assigned';
    
    const activeCount = getMemberCount(resident.house.id);
    if (activeCount >= 3) {
      return {
        th: 'บ้านนี้มีสมาชิกใช้งานครบ 3 คนแล้ว',
        en: 'This house already has 3 active members'
      };
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
        setMessageModal({
          show: true,
          type: 'success',
          title: '✅ Success',
          message_th: 'ปิดใช้งานสมาชิกเรียบร้อยแล้ว',
          message_en: 'Resident deactivated successfully',
          showDetails: false,
          errorDetails: null
        });
      } else {
        await usersAPI.reactivateResident(resident.id);
        setMessageModal({
          show: true,
          type: 'success',
          title: '✅ Success',
          message_th: 'เปิดใช้งานสมาชิกเรียบร้อยแล้ว',
          message_en: 'Resident reactivated successfully',
          showDetails: false,
          errorDetails: null
        });
      }
      loadData(); // Refresh list
    } catch (error) {
      // CRITICAL: Handle 409 as warning (not error) - member limit reached
      if (error.response?.status === 409) {
        const detail = error.response.data?.detail;
        
        // Handle HOUSE_MEMBER_LIMIT_REACHED as warning
        if (detail?.code === 'HOUSE_MEMBER_LIMIT_REACHED') {
          // Show bilingual warning modal (not alert)
          setMessageModal({
            show: true,
            type: 'warning',
            title: '⚠️ Cannot Reactivate',
            message_th: detail.message_th || 'บ้านนี้มีสมาชิกใช้งานครบ 3 คนแล้ว',
            message_en: detail.message_en || 'This house already has 3 active members',
            showDetails: false,
            errorDetails: null
          });
          return; // Return early - no console.error
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

  // NOTE: handleResetPassword removed - Residents are OTP-only

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
                        {/* NOTE: Reset Password button removed - Residents are OTP-only */}
                        {resident.is_active ? (
                          <button
                            onClick={() => handleDeactivate(resident)}
                            className="text-orange-400 hover:text-orange-300 text-sm"
                          >
                            Deactivate
                          </button>
                        ) : (
                          <div className="relative group">
                            <button
                              onClick={() => canReactivateResident(resident) && handleDeactivate(resident)}
                              disabled={!canReactivateResident(resident)}
                              className={`text-sm ${
                                canReactivateResident(resident)
                                  ? "text-green-400 hover:text-green-300 cursor-pointer" 
                                  : "text-gray-500 cursor-not-allowed"
                              }`}
                            >
                              Reactivate
                            </button>
                            {!canReactivateResident(resident) && getReactivateTooltip(resident) && (
                              <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10 pointer-events-none">
                                <div>{getReactivateTooltip(resident).th}</div>
                                <div className="text-gray-300">{getReactivateTooltip(resident).en}</div>
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

      {/* NOTE: Reset Password Modal removed - Residents are OTP-only */}

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

      {/* Message Modal (Success/Warning/Error) */}
      {messageModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`rounded-lg p-6 w-full max-w-md ${
            messageModal.type === 'success' ? 'bg-green-800' :
            messageModal.type === 'warning' ? 'bg-yellow-800' : 
            'bg-red-800'
          }`}>
            <div className="mb-4">
              <h3 className="text-xl font-bold text-white mb-2">{messageModal.title}</h3>
              <div className="space-y-2">
                <p className="text-gray-100">{messageModal.message_th}</p>
                <p className="text-gray-300 text-sm">{messageModal.message_en}</p>
              </div>
            </div>

            {messageModal.showDetails && messageModal.errorDetails && (
              <div className="mb-4">
                <button
                  onClick={() => setMessageModal(prev => ({ ...prev, showDetails: !prev.showDetails }))}
                  className="text-sm text-gray-300 hover:text-white mb-2"
                >
                  🔍 Show Technical Details
                </button>
                {messageModal.showDetails && (
                  <div className="bg-gray-900 p-3 rounded text-xs text-gray-300 max-h-32 overflow-y-auto">
                    <div>Status: {messageModal.errorDetails.status}</div>
                    <div>Message: {messageModal.errorDetails.message}</div>
                    {messageModal.errorDetails.detail && (
                      <div>Detail: {messageModal.errorDetails.detail}</div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-3">
              <button 
                onClick={() => setMessageModal({ show: false, type: 'warning', title: '', message_th: '', message_en: '', showDetails: false, errorDetails: null })}
                className="btn-primary flex-1"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
