import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { housesAPI } from '../../api/client';
import { useToast } from '../../components/Toast';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


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
    { value: 'ACTIVE', label: t('houses.statusActive') },
    { value: 'VACANT', label: t('houses.statusVacant') },
    { value: 'BANK_OWNED', label: t('houses.statusBankOwned') },
    { value: 'SUSPENDED', label: t('houses.statusSuspended') },
    { value: 'ARCHIVED', label: t('houses.statusArchived') },
  ];

  const validateForm = () => {
    const newErrors = {};

    if (!formData.house_code.trim()) {
      newErrors.house_code = t('addHouse.houseCodeRequired');
    } else if (!/^28\/[1-9][0-9]*$/.test(formData.house_code.trim())) {
      newErrors.house_code = t('addHouse.houseCodeFormat');
    }

    if (!formData.owner_name.trim()) {
      newErrors.owner_name = t('addHouse.ownerRequired');
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
        toast.success(`${t('addHouse.createSuccess')} ${t('addHouse.houseCode')}: ${formData.house_code} / ${t('addHouse.ownerName')}: ${formData.owner_name}`);
        
        if (saveAndAddAnother) {
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
          navigate('/admin/houses');
        }
      }
    } catch (error) {
      console.error('Failed to create house:', error);
      const errorDetail = error.response?.data?.detail || error.response?.data || error.message;
      
      if (typeof errorDetail === 'object' && errorDetail.error_th) {
        toast.error(errorDetail.error_th);
      } else {
        toast.error(`${t('addHouse.createFailed')}: ${typeof errorDetail === 'string' ? errorDetail : t('common.error')}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <button 
            onClick={() => navigate('/admin/houses')}
            className="text-primary-400 hover:text-primary-300"
          >
            ← {t('common.back')}
          </button>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('addHouse.title')}</h1>
        <p className="text-gray-400">{t('addHouse.subtitle')}</p>
      </div>

      <div className="card max-w-2xl">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">{t('addHouse.houseInfo')}</h2>
        </div>

        <form className="p-6 space-y-6">
          {/* House Code */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('houses.houseCode')} *
            </label>
            <input
              type="text"
              value={formData.house_code}
              onChange={(e) => handleInputChange('house_code', e.target.value)}
              placeholder={t('addHouse.houseCodePlaceholder')}
              className={`input w-full ${errors.house_code ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.house_code && (
              <p className="text-red-400 text-sm mt-1">{errors.house_code}</p>
            )}
            <p className="text-gray-500 text-sm mt-1">
              {t('addHouse.houseCodeFormat')}
            </p>
          </div>

          {/* Owner Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('houses.ownerName')} *
            </label>
            <input
              type="text"
              value={formData.owner_name}
              onChange={(e) => handleInputChange('owner_name', e.target.value)}
              placeholder={t('addHouse.ownerNamePlaceholder')}
              className={`input w-full ${errors.owner_name ? 'border-red-500' : ''}`}
              disabled={loading}
            />
            {errors.owner_name && (
              <p className="text-red-400 text-sm mt-1">{errors.owner_name}</p>
            )}
          </div>

          {/* House Status */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('houses.houseStatus')}
            </label>
            <select
              value={formData.house_status}
              onChange={(e) => handleInputChange('house_status', e.target.value)}
              className="input w-full"
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
                {t('houses.floorArea')}
              </label>
              <input
                type="text"
                value={formData.floor_area}
                onChange={(e) => handleInputChange('floor_area', e.target.value)}
                placeholder={t('houses.areaPlaceholder')}
                className="input w-full"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('houses.landArea')}
              </label>
              <input
                type="text"
                value={formData.land_area}
                onChange={(e) => handleInputChange('land_area', e.target.value)}
                placeholder={t('houses.landPlaceholder')}
                className="input w-full"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {t('houses.zone')}
              </label>
              <input
                type="text"
                value={formData.zone}
                onChange={(e) => handleInputChange('zone', e.target.value)}
                placeholder={t('addHouse.zonePlaceholder')}
                className="input w-full"
                disabled={loading}
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              {t('common.notes')}
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              placeholder={t('common.notesPlaceholder')}
              rows="3"
              className="input w-full"
              disabled={loading}
            />
          </div>

          {/* Form Actions */}
          <div className="flex flex-wrap gap-4 pt-4">
            <button
              type="button"
              onClick={(e) => handleSubmit(e, false)}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? t('common.saving') : `💾 ${t('common.save')}`}
            </button>
            <button
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              disabled={loading}
              className="btn-secondary"
            >
              {loading ? t('common.saving') : `💾 ${t('addHouse.saveAndAdd')}`}
            </button>
            <button
              type="button"
              onClick={() => navigate('/admin/houses')}
              disabled={loading}
              className="btn-outline"
            >
              {t('common.cancel')}
            </button>
          </div>
        </form>
      </div>
    </div>
    </AdminPageWrapper>
  );
}
