import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { usersAPI, housesAPI } from '../../api/client';

export default function AddResident() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [houses, setHouses] = useState([]);
  const [selectedHouseInfo, setSelectedHouseInfo] = useState(null);
  const [errors, setErrors] = useState({});
  const [creationSuccess, setCreationSuccess] = useState(null);  // OTP-only success message
  const [formData, setFormData] = useState({
    house_id: location.state?.house_id || '',
    full_name: '',
    email: '',
    phone: '',
    member_role: 'resident'
  });

  const memberRoles = [
    { value: 'owner', label: 'Owner / เจ้าของ' },
    { value: 'resident', label: 'Resident / ผู้อาศัย' },
    { value: 'tenant', label: 'Tenant / ผู้เช่า' }
  ];

  useEffect(() => {
    loadHouses();
  }, []);

  useEffect(() => {
    if (formData.house_id) {
      loadHouseInfo(formData.house_id);
    } else {
      setSelectedHouseInfo(null);
    }
  }, [formData.house_id]);

  const loadHouses = async () => {
    try {
      const response = await housesAPI.list();
      setHouses(response.data || []);
    } catch (error) {
      console.error('Failed to load houses:', error);
    }
  };

  const loadHouseInfo = async (houseId) => {
    try {
      const response = await usersAPI.getHouseMemberCount(houseId);
      setSelectedHouseInfo(response.data);
    } catch (error) {
      console.error('Failed to load house info:', error);
      setSelectedHouseInfo(null);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.house_id) {
      newErrors.house_id = 'House selection is required / จำเป็นต้องเลือกบ้าน';
    }

    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required / ชื่อ-นามสกุลจำเป็นต้องระบุ';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone is required / เบอร์โทรจำเป็นต้องระบุ (ใช้เป็น key ในการอ้างอิงข้ามบ้าน)';
    }

    if (formData.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Invalid email format / รูปแบบอีเมลไม่ถูกต้อง';
    }

    // Check member limit
    if (selectedHouseInfo && selectedHouseInfo.available_slots <= 0) {
      newErrors.house_id = `House member limit reached (${selectedHouseInfo.current_member_count}/${selectedHouseInfo.max_member_count}) / จำนวนสมาชิกในบ้านครบแล้ว`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await usersAPI.createResident(formData);
      
      if (response.data.success) {
        const isExisting = response.data.existing_user;
        const userData = response.data.user;
        
        setCreationSuccess({
          name: userData.full_name || formData.full_name,
          email: userData.email || formData.email,
          phone: userData.phone || formData.phone,
          existing_user: isExisting,
          active_houses_count: userData.active_houses_count,
          message_th: response.data.message_th,
          message_en: response.data.message
        });
        
        // Auto redirect after 4 seconds
        setTimeout(() => {
          navigate('/admin/members', { 
            state: { 
              created: true, 
              newResident: { 
                name: userData.full_name || formData.full_name, 
                phone: userData.phone || formData.phone 
              } 
            } 
          });
        }, 4000);
      }
    } catch (error) {
      console.error('Failed to create resident:', error);
      const errorDetail = error.response?.data?.detail || error.response?.data || error.message;
      
      if (typeof errorDetail === 'object' && errorDetail.error_en) {
        alert(`Error: ${errorDetail.error_en}\\nข้อผิดพลาด: ${errorDetail.error_th || errorDetail.error_en}`);
      } else {
        alert(`Failed to create resident: ${typeof errorDetail === 'string' ? errorDetail : 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    
    // Clear success message when form changes
    if (creationSuccess) {
      setCreationSuccess(null);
    }
  };

  // NOTE: copyToClipboard removed - no password credentials to copy (OTP-only)

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <button 
            onClick={() => navigate('/admin/houses')}
            className="text-primary-400 hover:text-primary-300"
          >
            ← Back to Houses
          </button>
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">Add New Resident</h1>
        <p className="text-gray-400">เพิ่มผู้อาศัยใหม่ / Create a new resident user</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">Resident Information / ข้อมูลผู้อาศัย</h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* House Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  House / บ้าน *
                </label>
                <select
                  value={formData.house_id}
                  onChange={(e) => handleInputChange('house_id', e.target.value)}
                  className={`input ${errors.house_id ? 'border-red-500' : ''}`}
                  disabled={loading}
                >
                  <option value="">Select house / เลือกบ้าน</option>
                  {houses.map(house => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} - {house.owner_name} ({house.house_status})
                    </option>
                  ))}
                </select>
                {errors.house_id && (
                  <p className="text-red-400 text-sm mt-1">{errors.house_id}</p>
                )}
              </div>

              {/* Full Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Full Name / ชื่อ-นามสกุล *
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => handleInputChange('full_name', e.target.value)}
                  placeholder="Enter full name"
                  className={`input ${errors.full_name ? 'border-red-500' : ''}`}
                  disabled={loading}
                />
                {errors.full_name && (
                  <p className="text-red-400 text-sm mt-1">{errors.full_name}</p>
                )}
              </div>

              {/* Phone (Primary Key) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Phone / เบอร์โทรศัพท์ *
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="08X-XXX-XXXX"
                  className={`input ${errors.phone ? 'border-red-500' : ''}`}
                  disabled={loading}
                />
                {errors.phone && (
                  <p className="text-red-400 text-sm mt-1">{errors.phone}</p>
                )}
                <p className="text-gray-500 text-sm mt-1">
                  📌 ใช้เป็นตัวอ้างอิงผู้ใช้ — ถ้าเบอร์ซ้ำกับคนที่มีแล้ว จะเพิ่มบ้านให้คนเดิมอัตโนมัติ
                </p>
              </div>

              {/* Email (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Email / อีเมล
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="Enter email address (optional)"
                  className={`input ${errors.email ? 'border-red-500' : ''}`}
                  disabled={loading}
                />
                {errors.email && (
                  <p className="text-red-400 text-sm mt-1">{errors.email}</p>
                )}
              </div>

              {/* Member Role */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Member Role / บทบาทสมาชิก
                </label>
                <select
                  value={formData.member_role}
                  onChange={(e) => handleInputChange('member_role', e.target.value)}
                  className="input"
                  disabled={loading}
                >
                  {memberRoles.map(role => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Form Actions */}
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  disabled={loading || (selectedHouseInfo && selectedHouseInfo.available_slots <= 0)}
                  className="btn-primary"
                >
                  {loading ? 'Creating... / กำลังสร้าง...' : '👤 Create Resident / สร้างผู้อาศัย'}
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/admin/houses')}
                  disabled={loading}
                  className="btn-outline"
                >
                  Cancel / ยกเลิก
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Side Panel - House Info & Credentials */}
        <div className="space-y-6">
          {/* House Information */}
          {selectedHouseInfo && (
            <div className="card">
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-bold text-white">House Info / ข้อมูลบ้าน</h3>
              </div>
              <div className="p-4 space-y-3">
                <div>
                  <span className="text-gray-400">House Code: </span>
                  <span className="text-white font-medium">{selectedHouseInfo.house_code}</span>
                </div>
                <div>
                  <span className="text-gray-400">Members: </span>
                  <span className={`font-medium ${selectedHouseInfo.available_slots > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedHouseInfo.current_member_count}/{selectedHouseInfo.max_member_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Available Slots: </span>
                  <span className={`font-medium ${selectedHouseInfo.available_slots > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedHouseInfo.available_slots}
                  </span>
                </div>
                {selectedHouseInfo.available_slots <= 0 && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-red-400 text-sm">
                    ⚠️ Member limit reached! Cannot add more residents to this house.
                    <br />
                    ไม่สามารถเพิ่มผู้อาศัยได้แล้ว จำนวนสมาชิกครบ 3 คนแล้ว
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Success Display */}
          {creationSuccess && (
            <div className="card">
              <div className={`p-4 border-b ${creationSuccess.existing_user ? 'border-blue-700 bg-blue-900/20' : 'border-gray-700'}`}>
                <h3 className="font-bold text-white">
                  {creationSuccess.existing_user 
                    ? '🔗 เพิ่มบ้านให้ผู้ใช้เดิมสำเร็จ' 
                    : '✅ สร้างผู้อาศัยสำเร็จ'}
                </h3>
              </div>
              <div className="p-4 space-y-4">
                <div className={`rounded p-3 ${
                  creationSuccess.existing_user 
                    ? 'bg-blue-500/10 border border-blue-500/20' 
                    : 'bg-green-500/10 border border-green-500/20'
                }`}>
                  <p className={`font-medium mb-2 ${creationSuccess.existing_user ? 'text-blue-400' : 'text-green-400'}`}>
                    {creationSuccess.existing_user ? '🔗' : '✅'} {creationSuccess.name}
                  </p>
                  <p className="text-gray-300 text-sm mb-1">
                    📱 {creationSuccess.phone}
                  </p>
                  {creationSuccess.email && (
                    <p className="text-gray-300 text-sm mb-1">
                      📧 {creationSuccess.email}
                    </p>
                  )}
                  {creationSuccess.active_houses_count > 1 && (
                    <p className="text-yellow-400 text-sm mt-2">
                      🏠 ผู้ใช้คนนี้มี {creationSuccess.active_houses_count} บ้าน — สลับบ้านได้ในหน้า Profile
                    </p>
                  )}
                </div>
                
                <div className="bg-primary-500/10 border border-primary-500/20 rounded p-3">
                  <p className="text-primary-300 text-sm font-medium">
                    {creationSuccess.message_th}
                  </p>
                </div>
                
                <div className="bg-gray-700/50 border border-gray-600 rounded p-3 text-gray-300 text-sm">
                  📲 ผู้ใช้เข้าสู่ระบบผ่าน LINE — หลังเชื่อมต่อ LINE แล้วระบบจะจับคู่ด้วยเบอร์โทร
                </div>
                
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => navigate('/admin/members')}
                    className="btn-primary flex-1"
                  >
                    ไปหน้ารายชื่อผู้อาศัย
                  </button>
                  <button
                    onClick={() => setCreationSuccess(null)}
                    className="btn-secondary"
                  >
                    เพิ่มอีก
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}