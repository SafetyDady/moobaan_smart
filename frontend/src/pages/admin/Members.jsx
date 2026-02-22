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
        title: '✅ ถอดออกจากบ้านสำเร็จ',
        message_th: response.data.message_th || `ถอด ${resident.full_name} ออกจากบ้าน ${resident.house.house_code} แล้ว`,
        message_en: response.data.message || 'Removed from house successfully',
        showDetails: false,
        errorDetails: null
      });

      if (response.data.user_deactivated) {
        setMessageModal(prev => ({
          ...prev,
          message_th: prev.message_th + '\n⚠️ ผู้ใช้ไม่มีบ้านเหลือ — ถูก deactivate อัตโนมัติ',
          message_en: prev.message_en + '\nUser had no remaining houses and was deactivated.'
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
        title: '❌ ไม่สำเร็จ',
        message_th: typeof detail === 'object' ? (detail.error_th || 'เกิดข้อผิดพลาด') : (detail || 'เกิดข้อผิดพลาด'),
        message_en: typeof detail === 'object' ? (detail.error_en || 'Failed') : (detail || 'Failed to remove from house'),
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
        title: '✅ Force Logout Successful',
        message_th: `บังคับออกจากระบบ ${resident.full_name} สำเร็จ\nลูกบ้านจะต้อง login ด้วย OTP ใหม่`,
        message_en: `Successfully forced logout for ${resident.full_name}\nResident will need to login again with OTP`,
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
        title: '❌ Force Logout Failed',
        message_th: detail?.message_th || 'ไม่สามารถบังคับออกจากระบบได้',
        message_en: detail?.message_en || detail || 'Failed to force logout',
        showDetails: false,
        errorDetails: null
      });
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Residents Directory</h1>
          <p className="text-gray-400">จัดการลูกบ้านทั้งหมด (สูงสุด 3 คนต่อบ้าน)</p>
        </div>
        <Link
          to="/admin/add-resident"
          className="btn-primary flex items-center gap-2"
        >
          <span className="text-lg">+</span> เพิ่มลูกบ้าน
        </Link>
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
                        {/* Phase D.2: Force Logout button (only for active residents) */}
                        {resident.is_active && (
                          <button
                            onClick={() => handleForceLogout(resident)}
                            className="text-red-400 hover:text-red-300 text-sm"
                            title="Force logout all devices"
                          >
                            Force Logout
                          </button>
                        )}
                        {/* Remove from House */}
                        {resident.is_active && resident.house && (
                          <button
                            onClick={() => handleRemoveFromHouse(resident)}
                            className="text-purple-400 hover:text-purple-300 text-sm"
                            title="Remove from this house"
                          >
                            ถอดบ้าน
                          </button>
                        )}
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

      {/* Remove from House Confirmation Modal */}
      {removeHouseModal.show && removeHouseModal.resident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">⚠️ ถอดออกจากบ้าน</h3>

            <div className="space-y-3 mb-6">
              <p className="text-gray-300">
                ต้องการถอดสมาชิกออกจากบ้านนี้?
              </p>
              <div className="bg-gray-700 p-3 rounded">
                <p className="text-white font-medium">{removeHouseModal.resident.full_name}</p>
                <p className="text-gray-400 text-sm">
                  🏠 บ้าน: {removeHouseModal.resident.house?.house_code || '-'}
                </p>
                <p className="text-gray-400 text-sm">
                  📱 โทร: {removeHouseModal.resident.phone || '-'}
                </p>
              </div>
              <div className="text-yellow-400 text-sm">
                <p>⚠️ การดำเนินการนี้จะ:</p>
                <ul className="list-disc list-inside ml-2 mt-1 text-gray-300">
                  <li>ถอดสมาชิกออกจากบ้าน {removeHouseModal.resident.house?.house_code}</li>
                  <li>Membership จะเปลี่ยนเป็น INACTIVE</li>
                  <li>ถ้าไม่มีบ้านเหลือ จะ deactivate user อัตโนมัติ</li>
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
                ยกเลิก
              </button>
              <button
                type="button"
                onClick={confirmRemoveFromHouse}
                disabled={removeHouseModal.loading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded flex-1 disabled:opacity-50"
              >
                {removeHouseModal.loading ? 'กำลังดำเนินการ...' : 'ถอดออกจากบ้าน'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Phase D.2: Force Logout Confirmation Modal */}
      {forceLogoutModal.show && forceLogoutModal.resident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">⚠️ Confirm Force Logout</h3>
            
            <div className="space-y-3 mb-6">
              <p className="text-gray-300">
                คุณต้องการบังคับออกจากระบบสำหรับ:
              </p>
              <div className="bg-gray-700 p-3 rounded">
                <p className="text-white font-medium">{forceLogoutModal.resident.full_name}</p>
                <p className="text-gray-400 text-sm">
                  บ้าน: {forceLogoutModal.resident.house?.house_code || '-'}
                </p>
                <p className="text-gray-400 text-sm">
                  โทร: {forceLogoutModal.resident.phone || '-'}
                </p>
              </div>
              <div className="text-yellow-400 text-sm">
                <p>⚠️ การดำเนินการนี้จะ:</p>
                <ul className="list-disc list-inside ml-2 mt-1 text-gray-300">
                  <li>ทำให้ session ทุกอุปกรณ์หมดอายุทันที</li>
                  <li>ลูกบ้านต้อง login ใหม่ด้วย OTP</li>
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
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmForceLogout}
                disabled={forceLogoutModal.loading}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex-1 disabled:opacity-50"
              >
                {forceLogoutModal.loading ? 'Processing...' : 'Force Logout'}
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
