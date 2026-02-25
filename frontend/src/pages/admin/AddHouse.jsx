import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { housesAPI } from '../../api/client';
import { useToast } from '../../components/Toast';

export default function AddHouse() {
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [formData, setFormData] = useState({
    house_code: '',
    owner_name: '',
    house_status: 'ACTIVE',
    floor_area: '',
    land_area: '',
    zone: '',
    notes: ''
  });

  const houseStatuses = [
    { value: 'ACTIVE', label: 'Active / ใช้งานอยู่' },
    { value: 'VACANT', label: 'Vacant / ว่าง' },
    { value: 'BANK_OWNED', label: 'Bank Owned / ธนาคารเจ้าของ' },
    { value: 'SUSPENDED', label: 'Suspended / ระงับการใช้งาน' },
    { value: 'ARCHIVED', label: 'Archived / เก็บถาวร' }
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!formData.house_code.trim()) {
      newErrors.house_code = 'House code is required / รหัสบ้านจำเป็นต้องระบุ';
    } else if (!/^28\/[1-9][0-9]*$/.test(formData.house_code.trim())) {
      newErrors.house_code = 'House code must be in format 28/[number] (e.g., 28/1, 28/15) / รหัสบ้านต้องอยู่ในรูปแบบ 28/[หมายเลข]';
    }

    if (!formData.owner_name.trim()) {
      newErrors.owner_name = 'Owner name is required / ชื่อเจ้าของจำเป็นต้องระบุ';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e, saveAndAddAnother = false) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await housesAPI.create(formData);
      
      if (response.data.success) {
        toast.success(`สร้างข้อมูลบ้านเรียบร้อย! House Code: ${formData.house_code} / Owner: ${formData.owner_name}`);
        
        if (saveAndAddAnother) {
          // Reset form for another entry
          setFormData({
            house_code: '',
            owner_name: '',
            house_status: 'ACTIVE',
            floor_area: '',
            land_area: '',
            zone: '',
            notes: ''
          });
          setErrors({});
        } else {
          // Navigate back to houses list
          navigate('/admin/houses');
        }
      }
    } catch (error) {
      console.error('Failed to create house:', error);
      const errorDetail = error.response?.data?.detail || error.response?.data || error.message;
      
      if (typeof errorDetail === 'object' && errorDetail.error_en) {
        toast.error(`${errorDetail.error_th || errorDetail.error_en}`);
      } else {
        toast.error(`ไม่สามารถสร้างบ้านได้: ${typeof errorDetail === 'string' ? errorDetail : 'Unknown error'}`);
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
  };

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
        <h1 className="text-3xl font-bold text-white mb-2">Add New House</h1>
        <p className="text-gray-400">เพิ่มข้อมูลบ้านใหม่ / Create a new house record</p>
      </div>

      <div className="card max-w-2xl">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">House Information / ข้อมูลบ้าน</h2>
        </div>

        <form className="p-6 space-y-6">
          {/* House Code */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              House Code / รหัสบ้าน *
            </label>
            <input
              type="text"
              value={formData.house_code}
              onChange={(e) => handleInputChange('house_code', e.target.value)}
              placeholder="e.g., 28/1, 28/15, 28/158"
              className={`input ${errors.house_code ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.house_code && (
              <p className="text-red-400 text-sm mt-1">{errors.house_code}</p>
            )}
            <p className="text-gray-500 text-sm mt-1">
              Format: 28/[number] เช่น 28/1, 28/15, 28/158
            </p>
          </div>

          {/* Owner Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Owner Name / ชื่อเจ้าของ *
            </label>
            <input
              type="text"
              value={formData.owner_name}
              onChange={(e) => handleInputChange('owner_name', e.target.value)}
              placeholder="Full name of the house owner"
              className={`input ${errors.owner_name ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.owner_name && (
              <p className="text-red-400 text-sm mt-1">{errors.owner_name}</p>
            )}
          </div>

          {/* House Status */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              House Status / สถานะบ้าน
            </label>
            <select
              value={formData.house_status}
              onChange={(e) => handleInputChange('house_status', e.target.value)}
              className="input"
              disabled={loading}
            >
              {houseStatuses.map(status => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>

          {/* Optional Fields */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Floor Area / พื้นที่ใช้สอย
              </label>
              <input
                type="text"
                value={formData.floor_area}
                onChange={(e) => handleInputChange('floor_area', e.target.value)}
                placeholder="e.g., 120 ตร.ม."
                className="input"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Land Area / พื้นที่ดิน
              </label>
              <input
                type="text"
                value={formData.land_area}
                onChange={(e) => handleInputChange('land_area', e.target.value)}
                placeholder="e.g., 80 ตรว."
                className="input"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Zone / โซน
              </label>
              <input
                type="text"
                value={formData.zone}
                onChange={(e) => handleInputChange('zone', e.target.value)}
                placeholder="e.g., A, B, C"
                className="input"
                disabled={loading}
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes / หมายเหตุ
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              placeholder="Additional notes or comments"
              rows="3"
              className="input"
              disabled={loading}
            />
          </div>

          {/* Form Actions */}
          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={(e) => handleSubmit(e, false)}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Creating... / กำลังสร้าง...' : '💾 Save / บันทึก'}
            </button>
            <button
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              disabled={loading}
              className="btn-secondary"
            >
              {loading ? 'Creating... / กำลังสร้าง...' : '💾 Save & Add Another / บันทึกและเพิ่มต่อ'}
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
  );
}