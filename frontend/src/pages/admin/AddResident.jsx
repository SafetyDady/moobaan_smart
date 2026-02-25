import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { usersAPI, housesAPI } from '../../api/client';
import { useToast } from '../../components/Toast';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function AddResident() {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();
  const preselectedHouseId = location.state?.house_id || '';

  // ── Phone search state ──
  const [phone, setPhone] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null); // null=not searched, {found, user}

  // ── Form state ──
  const [houses, setHouses] = useState([]);
  const [selectedHouseInfo, setSelectedHouseInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [creationSuccess, setCreationSuccess] = useState(null);
  const [formData, setFormData] = useState({
    house_id: preselectedHouseId,
    full_name: '',
    email: '',
    member_role: 'resident'
  });

  const memberRoles = [
    { value: 'owner', label: t('roles.owner') },
    { value: 'resident', label: t('roles.resident') },
    { value: 'tenant', label: t('roles.tenant') }
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

  // ── Phone Search ──
  const handlePhoneSearch = async () => {
    const normalized = phone.trim().replace(/-/g, '').replace(/ /g, '');
    if (!normalized) {
      setErrors({ phone: t('addResident.phoneRequired') });
      return;
    }

    setSearching(true);
    setErrors({});
    setCreationSuccess(null);
    try {
      const response = await usersAPI.searchByPhone(normalized);
      setSearchResult(response.data);

      // If user found, pre-fill name
      if (response.data.found && response.data.user) {
        setFormData(prev => ({
          ...prev,
          full_name: response.data.user.full_name || '',
          email: response.data.user.email || ''
        }));
      } else {
        setFormData(prev => ({ ...prev, full_name: '', email: '' }));
      }
    } catch (error) {
      console.error('Phone search failed:', error);
      setSearchResult(null);
      setErrors({ phone: t('addResident.searchFailed') });
    } finally {
      setSearching(false);
    }
  };

  const handlePhoneKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handlePhoneSearch();
    }
  };

  const resetSearch = () => {
    setPhone('');
    setSearchResult(null);
    setCreationSuccess(null);
    setFormData({ house_id: '', full_name: '', email: '', member_role: 'resident' });
    setErrors({});
  };

  // ── Filter houses: exclude houses the existing user already has ──
  const getAvailableHouses = () => {
    if (!searchResult?.found || !searchResult.user?.memberships) return houses;
    const existingActiveHouseIds = searchResult.user.memberships
      .filter(m => m.status === 'ACTIVE')
      .map(m => m.house_id);
    return houses.filter(h => !existingActiveHouseIds.includes(h.id));
  };

  // ── Submit ──
  const validateForm = () => {
    const newErrors = {};

    if (!formData.house_id) {
      newErrors.house_id = t('addResident.houseRequired');
    }

    // If new user, name is required
    if (!searchResult?.found && !formData.full_name.trim()) {
      newErrors.full_name = t('addResident.nameRequired');
    }

    if (formData.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = t('addResident.emailInvalid');
    }

    if (selectedHouseInfo && selectedHouseInfo.available_slots <= 0) {
      newErrors.house_id = `${t('addResident.houseFull')} (${selectedHouseInfo.max_member_count})`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    const normalized = phone.trim().replace(/-/g, '').replace(/ /g, '');

    setLoading(true);
    try {
      const payload = {
        house_id: parseInt(formData.house_id),
        full_name: searchResult?.found ? searchResult.user.full_name : formData.full_name,
        phone: normalized,
        email: formData.email || undefined,
        member_role: formData.member_role
      };

      const response = await usersAPI.createResident(payload);

      if (response.data.success) {
        const isExisting = response.data.existing_user;
        const userData = response.data.user;

        setCreationSuccess({
          name: userData.full_name,
          phone: userData.phone,
          email: userData.email,
          existing_user: isExisting,
          active_houses_count: userData.active_houses_count,
          message_th: response.data.message_th,
          message_en: response.data.message
        });
      }
    } catch (error) {
      console.error('Failed to create/assign resident:', error);
      const detail = error.response?.data?.detail || error.message;
      if (typeof detail === 'object' && detail.error_th) {
        toast.error(detail.error_th || detail.error_en || t('common.error'));
      } else {
        toast.error(`${t('addResident.failed')}: ${typeof detail === 'string' ? detail : 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const isExistingUser = searchResult?.found === true;
  const isNewUser = searchResult?.found === false;
  const hasSearched = searchResult !== null;

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <button onClick={() => navigate('/admin/members')} className="text-primary-400 hover:text-primary-300">
            ← {t('common.back')}
          </button>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('addResident.title')}</h1>
        <p className="text-gray-400">{t('addResident.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          {/* ── Step 1: Phone Search ── */}
          <div className="card mb-6">
            <div className="p-6 border-b border-gray-700">
              <h2 className="text-xl font-bold text-white">{t('addResident.step1Title')}</h2>
              <p className="text-gray-400 text-sm mt-1">{t('addResident.step1Desc')}</p>
            </div>
            <div className="p-6">
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    {t('addResident.phoneLabel')} *
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => {
                      setPhone(e.target.value);
                      if (hasSearched) {
                        setSearchResult(null);
                        setCreationSuccess(null);
                      }
                    }}
                    onKeyDown={handlePhoneKeyDown}
                    placeholder="08X-XXX-XXXX"
                    className={`input w-full ${errors.phone ? 'border-red-500' : ''}`}
                    disabled={loading}
                  />
                  {errors.phone && <p className="text-red-400 text-sm mt-1">{errors.phone}</p>}
                </div>
                <div className="flex items-end">
                  <button
                    type="button"
                    onClick={handlePhoneSearch}
                    disabled={searching || loading}
                    className="btn-primary whitespace-nowrap"
                  >
                    {searching ? t('addResident.searching') : t('addResident.searchBtn')}
                  </button>
                </div>
              </div>

              {/* Search Result: User Found */}
              {isExistingUser && searchResult.user && (
                <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-blue-400 font-bold text-lg">{t('addResident.foundUser')}</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-gray-400">{t('addResident.userName')}</span>
                      <span className="text-white font-medium">{searchResult.user.full_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-gray-400">📱 LINE:</span>
                      <span className={searchResult.user.line_linked ? 'text-green-400' : 'text-yellow-400'}>
                        {searchResult.user.line_linked ? t('addResident.lineLinked') : t('addResident.lineNotLinked')}
                      </span>
                    </div>
                    {searchResult.user.email && (
                      <div className="flex items-center gap-3">
                        <span className="text-gray-400">{t('addResident.userEmail')}</span>
                        <span className="text-gray-300">{searchResult.user.email}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-400">{t('addResident.currentHouses')}</span>
                      {searchResult.user.memberships.length > 0 ? (
                        <div className="mt-1 space-y-1 ml-6">
                          {searchResult.user.memberships.map((m, i) => (
                            <div key={i} className={`text-sm ${m.status === 'ACTIVE' ? 'text-green-300' : 'text-gray-500'}`}>
                              • {m.house_code} ({m.role}, {m.status === 'ACTIVE' ? t('addResident.active') : t('addResident.inactive')})
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-yellow-400 ml-2">{t('addResident.noHouse')}</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Search Result: Not Found */}
              {isNewUser && (
                <div className="mt-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <span className="text-yellow-400 font-bold">{t('addResident.notFoundUser')}</span>
                </div>
              )}
            </div>
          </div>

          {/* ── Step 2: House Assignment (shown after search) ── */}
          {hasSearched && !creationSuccess && (
            <div className="card">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-xl font-bold text-white">
                  {t('addResident.step2')}: {isExistingUser ? t('addResident.selectHouse') : t('addResident.fillAndSelectHouse')}
                </h2>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-6">
                {/* Name & Email — only for NEW users */}
                {isNewUser && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        {t('addResident.fullNameLabel')} *
                      </label>
                      <input
                        type="text"
                        value={formData.full_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                        placeholder={t("addResident.fullNamePlaceholder")}
                        className={`input w-full ${errors.full_name ? 'border-red-500' : ''}`}
                        disabled={loading}
                      />
                      {errors.full_name && <p className="text-red-400 text-sm mt-1">{errors.full_name}</p>}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        {t('addResident.emailLabel')}
                      </label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                        placeholder="email@example.com"
                        className={`input w-full ${errors.email ? 'border-red-500' : ''}`}
                        disabled={loading}
                      />
                      {errors.email && <p className="text-red-400 text-sm mt-1">{errors.email}</p>}
                    </div>
                  </>
                )}

                {/* House Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    {t('addResident.selectHouseLabel')} *
                  </label>
                  <select
                    value={formData.house_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, house_id: e.target.value }))}
                    className={`input w-full ${errors.house_id ? 'border-red-500' : ''}`}
                    disabled={loading}
                  >
                    <option value="">{t('addResident.selectHousePlaceholder')}</option>
                    {getAvailableHouses().map(house => (
                      <option key={house.id} value={house.id}>
                        {house.house_code} - {house.owner_name} ({house.house_status})
                      </option>
                    ))}
                  </select>
                  {errors.house_id && <p className="text-red-400 text-sm mt-1">{errors.house_id}</p>}
                  {isExistingUser && getAvailableHouses().length === 0 && (
                    <p className="text-yellow-400 text-sm mt-2">
                      {t('addResident.allHousesAssigned')}
                    </p>
                  )}
                </div>

                {/* Member Role */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    {t('addResident.roleLabel')}
                  </label>
                  <select
                    value={formData.member_role}
                    onChange={(e) => setFormData(prev => ({ ...prev, member_role: e.target.value }))}
                    className="input w-full"
                    disabled={loading}
                  >
                    {memberRoles.map(role => (
                      <option key={role.value} value={role.value}>
                        {role.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Submit */}
                <div className="flex gap-4 pt-4">
                  <button
                    type="submit"
                    disabled={loading || (selectedHouseInfo && selectedHouseInfo.available_slots <= 0)}
                    className="btn-primary"
                  >
                    {loading ? t('common.loading') : isExistingUser 
                      ? t('addResident.addToHouseBtn') 
                      : t('addResident.createAndAddBtn')}
                  </button>
                  <button
                    type="button"
                    onClick={resetSearch}
                    disabled={loading}
                    className="btn-outline"
                  >
                    {t('addResident.resetBtn')}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* ── Side Panel ── */}
        <div className="space-y-6">
          {/* House Info */}
          {selectedHouseInfo && (
            <div className="card">
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-bold text-white">{t('addResident.houseInfo')}</h3>
              </div>
              <div className="p-4 space-y-3">
                <div>
                  <span className="text-gray-400">{t('addResident.houseCode')}: </span>
                  <span className="text-white font-medium">{selectedHouseInfo.house_code}</span>
                </div>
                <div>
                  <span className="text-gray-400">{t('addResident.members')}: </span>
                  <span className={`font-medium ${selectedHouseInfo.available_slots > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedHouseInfo.current_member_count}/{selectedHouseInfo.max_member_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">{t('addResident.available')}: </span>
                  <span className={`font-medium ${selectedHouseInfo.available_slots > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedHouseInfo.available_slots} {t('addResident.slots')}
                  </span>
                </div>
                {selectedHouseInfo.available_slots <= 0 && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded p-3 text-red-400 text-sm">
                    {t('addResident.houseFull')}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Success Panel */}
          {creationSuccess && (
            <div className="card">
              <div className={`p-4 border-b ${creationSuccess.existing_user ? 'border-blue-700 bg-blue-900/20' : 'border-green-700 bg-green-900/20'}`}>
                <h3 className="font-bold text-white">
                  {creationSuccess.existing_user 
                    ? t('addResident.addHouseSuccess') 
                    : t('addResident.createSuccess')}
                </h3>
              </div>
              <div className="p-4 space-y-4">
                <div className={`rounded p-3 ${
                  creationSuccess.existing_user 
                    ? 'bg-blue-500/10 border border-blue-500/20' 
                    : 'bg-green-500/10 border border-green-500/20'
                }`}>
                  <p className={`font-medium mb-2 ${creationSuccess.existing_user ? 'text-blue-400' : 'text-green-400'}`}>
                    👤 {creationSuccess.name}
                  </p>
                  <p className="text-gray-300 text-sm">📱 {creationSuccess.phone}</p>
                  {creationSuccess.email && (
                    <p className="text-gray-300 text-sm">📧 {creationSuccess.email}</p>
                  )}
                  {creationSuccess.active_houses_count > 1 && (
                    <p className="text-yellow-400 text-sm mt-2">
                      {t('addResident.multiHouseInfo')} {creationSuccess.active_houses_count} {t('addResident.houses')}
                    </p>
                  )}
                </div>

                <div className="bg-primary-500/10 border border-primary-500/20 rounded p-3">
                  <p className="text-primary-300 text-sm font-medium">{creationSuccess.message_th}</p>
                </div>

                <div className="flex gap-3 pt-2">
                  <button onClick={() => navigate('/admin/members')} className="btn-primary flex-1">
                    {t('addResident.goToList')}
                  </button>
                  <button onClick={resetSearch} className="btn-outline flex-1">
                    {t('addResident.addAnother')}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* How it works guide */}
          {!hasSearched && (
            <div className="card">
              <div className="p-4 border-b border-gray-700">
                <h3 className="font-bold text-white">{t('addResident.howToUse')}</h3>
              </div>
              <div className="p-4 space-y-3 text-sm text-gray-300">
                <div className="flex gap-2">
                  <span className="text-primary-400 font-bold">1.</span>
                  <span>{t('addResident.howStep1')}</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-primary-400 font-bold">2.</span>
                  <span>{t('addResident.howStep2')}</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-primary-400 font-bold">3.</span>
                  <span>{t('addResident.howStep3')}</span>
                </div>
                <div className="mt-3 bg-gray-700/50 p-3 rounded text-gray-400 text-xs">
                  {t('addResident.howTip')}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </AdminPageWrapper>
  );
}