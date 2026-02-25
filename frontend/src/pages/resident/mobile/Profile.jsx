import { useState } from 'react';
import { ChevronLeft, LogOut, Home, User, Mail, Phone, Edit3, Check, X, ArrowRightLeft, Circle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { useRole } from '../../../contexts/RoleContext';
import { authAPI } from '../../../api/client';
import ConfirmModal from '../../../components/ConfirmModal';
import MobileLayout from './MobileLayout';
import { t } from '../../../hooks/useLocale';

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout, updateUser, setResidentUser } = useAuth();
  const { currentHouseCode } = useRole();
  const [toast, setToast] = useState(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
  });
  const [switching, setSwitching] = useState(false);
  const [confirmSwitch, setConfirmSwitch] = useState({ open: false, houseId: null, houseCode: '' });
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 2500);
  };
  
  const startEdit = () => {
    setForm({
      full_name: user?.full_name || '',
      email: user?.email || '',
      phone: user?.phone || '',
    });
    setEditing(true);
  };
  
  const cancelEdit = () => {
    setEditing(false);
  };
  
  const saveProfile = async () => {
    setSaving(true);
    try {
      const payload = {};
      if (form.full_name !== (user?.full_name || '')) payload.full_name = form.full_name;
      if (form.email !== (user?.email || '')) payload.email = form.email;
      if (form.phone !== (user?.phone || '')) payload.phone = form.phone;
      
      if (Object.keys(payload).length === 0) {
        setEditing(false);
        return;
      }
      
      const resp = await authAPI.updateMe(payload);
      updateUser(resp.data);
      setEditing(false);
      showToast(t('profile.saveSuccess'), 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || t('profile.saveError');
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };
  
  const handleSwitchHouse = async (houseId, houseCode) => {
    setConfirmSwitch({ open: false, houseId: null, houseCode: '' });
    if (switching) return;
    
    setSwitching(true);
    try {
      const resp = await authAPI.selectHouse(houseId);
      const userData = resp.data?.user || resp.data;
      // Update auth context with new house info
      setResidentUser(userData);
      showToast(`${t('profile.switchSuccess')} ${houseCode}`, 'success');
      // Navigate to dashboard to reload data for new house
      setTimeout(() => navigate('/resident/dashboard'), 1000);
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.detail || t('profile.saveError');
      showToast(msg, 'error');
    } finally {
      setSwitching(false);
    }
  };

  const handleLogout = async () => {
    setShowLogoutConfirm(false);
    await logout();
    navigate('/login');
  };
  
  return (
    <MobileLayout>
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 left-4 right-4 z-50 rounded-lg p-3 shadow-lg border ${
          toast.type === 'success' ? 'bg-green-900 border-green-600' :
          toast.type === 'error' ? 'bg-red-900 border-red-600' :
          'bg-gray-800 border-gray-600'
        }`}>
          <p className="text-sm text-gray-200 text-center">{toast.message}</p>
        </div>
      )}
      
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/resident/dashboard')}
              className="text-white active:text-gray-300"
            >
              <ChevronLeft size={24} />
            </button>
            <h1 className="text-lg font-bold text-white">{t('profile.title')}</h1>
          </div>
          {!editing && (
            <button
              onClick={startEdit}
              className="flex items-center gap-1 text-primary-400 active:text-primary-300 text-sm"
            >
              <Edit3 size={16} />
              <span>{t('profile.edit')}</span>
            </button>
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Info Section */}
          {editing ? (
            /* ─── Edit Mode ─── */
            <div className="bg-gray-800 rounded-lg border border-primary-500/50 divide-y divide-gray-700">
              <div className="p-4">
                <label className="text-xs text-gray-400 mb-1 block">{t('profile.fullName')}</label>
                <div className="flex items-center gap-2">
                  <User size={18} className="text-gray-400 shrink-0" />
                  <input
                    type="text"
                    value={form.full_name}
                    onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
                    placeholder={t('profile.fullNamePlaceholder')}
                  />
                </div>
              </div>
              
              <div className="p-4">
                <label className="text-xs text-gray-400 mb-1 block">{t('profile.email')}</label>
                <div className="flex items-center gap-2">
                  <Mail size={18} className="text-gray-400 shrink-0" />
                  <input
                    type="email"
                    value={form.email}
                    onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
                    placeholder="example@email.com"
                  />
                </div>
              </div>
              
              <div className="p-4">
                <label className="text-xs text-gray-400 mb-1 block">{t('profile.phone')}</label>
                <div className="flex items-center gap-2">
                  <Phone size={18} className="text-gray-400 shrink-0" />
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
                    placeholder="08X-XXX-XXXX"
                  />
                </div>
              </div>
              
              {currentHouseCode && (
                <div className="p-4">
                  <div className="text-xs text-gray-400 mb-1">{t('profile.houseNo')}</div>
                  <div className="flex items-center gap-2 text-gray-400">
                    <Home size={18} />
                    <span className="text-white">{currentHouseCode}</span>
                    <span className="text-xs text-gray-500 ml-auto">{t('profile.notEditable')}</span>
                  </div>
                </div>
              )}
              
              {/* Save / Cancel buttons */}
              <div className="p-4 flex gap-3">
                <button
                  onClick={cancelEdit}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-1 py-2.5 rounded-lg border border-gray-600 text-gray-300 active:bg-gray-700 text-sm"
                >
                  <X size={16} />
                  <span>{t('profile.cancel')}</span>
                </button>
                <button
                  onClick={saveProfile}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-1 py-2.5 rounded-lg bg-primary-500 text-white active:bg-primary-600 text-sm font-medium disabled:opacity-50"
                >
                  <Check size={16} />
                  <span>{saving ? t('profile.saving') : t('profile.save')}</span>
                </button>
              </div>
            </div>
          ) : (
            /* ─── View Mode ─── */
            <div className="bg-gray-800 rounded-lg border border-gray-700 divide-y divide-gray-700">
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">{t('profile.fullName')}</div>
                <div className="flex items-center gap-2 text-white">
                  <User size={18} className="text-gray-400" />
                  <span>{user?.full_name || t('profile.notSpecified')}</span>
                </div>
              </div>
              
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">{t('profile.email')}</div>
                <div className="flex items-center gap-2 text-white">
                  <Mail size={18} className="text-gray-400" />
                  <span className={user?.email ? 'text-white' : 'text-gray-500 italic'}>
                    {user?.email || t('profile.notFilledEdit')}
                  </span>
                </div>
              </div>
              
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">{t('profile.phone')}</div>
                <div className="flex items-center gap-2 text-white">
                  <Phone size={18} className="text-gray-400" />
                  <span className={user?.phone ? 'text-white' : 'text-gray-500 italic'}>
                    {user?.phone || t('profile.notFilledEdit')}
                  </span>
                </div>
              </div>
              
              {currentHouseCode && (
                <div className="p-4">
                  <div className="text-xs text-gray-400 mb-1">{t('profile.houseNo')}</div>
                  <div className="flex items-center gap-2 text-white">
                    <Home size={18} className="text-gray-400" />
                    <span>{currentHouseCode}</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* LINE info + Multi-house */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Circle size={16} className="text-green-500 fill-green-500" />
                <span className="text-white text-sm">{t('profile.lineConnected')}</span>
              </div>
              <span className="text-xs text-green-400">{t('profile.loginViaLine')}</span>
            </div>
            
            {user?.houses && user.houses.length > 1 && (
              <div className="p-4 border-t border-gray-700">
                <div className="flex items-center gap-2 mb-3">
                  <ArrowRightLeft size={14} className="text-gray-400" />
                  <span className="text-xs text-gray-400">{t('profile.switchHouse')}</span>
                </div>
                <div className="flex flex-col gap-2">
                  {user.houses.map(h => {
                    const isCurrent = h.house_code === currentHouseCode;
                    return (
                      <button
                        key={h.id}
                        disabled={isCurrent || switching}
                        onClick={() => !isCurrent && setConfirmSwitch({ open: true, houseId: h.id, houseCode: h.house_code })}
                        className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-colors ${
                          isCurrent
                            ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30 cursor-default'
                            : 'bg-gray-700 text-gray-300 border border-gray-600 active:bg-gray-600 cursor-pointer'
                        } ${switching && !isCurrent ? 'opacity-50' : ''}`}
                      >
                        <div className="flex items-center gap-2">
                          <Home size={16} />
                          <span>{t('profile.house')} {h.house_code}</span>
                        </div>
                        {isCurrent ? (
                          <span className="text-xs bg-primary-500/30 px-2 py-0.5 rounded-full">{t('profile.current')}</span>
                        ) : (
                          <span className="text-xs text-gray-400">{switching ? t('profile.switching') : t('profile.tapToSwitch')}</span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          
          {/* About Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">{t('profile.about')}</h3>
            <div className="text-xs text-gray-400 space-y-1">
              <div>{t('profile.appName')}: Moobaan Smart</div>
              <div>{t('profile.version')}: 1.0.0</div>
              <div>© 2026 Moobaan Smart. All rights reserved.</div>
            </div>
          </div>
          
          {/* Logout Button */}
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="w-full bg-red-500/10 border border-red-500 text-red-400 rounded-lg p-4 flex items-center justify-center gap-2 font-medium active:bg-red-500/20"
          >
            <LogOut size={20} />
            <span>{t('profile.logout')}</span>
          </button>
          
          <div className="h-4"></div>
        </div>
      </div>
      <ConfirmModal
        open={confirmSwitch.open}
        title={t('profile.switchHouse')}
        message={`${t('profile.switchConfirmMsg')} ${confirmSwitch.houseCode} ?`}
        variant="info"
        confirmText={t('profile.switchBtn')}
        onConfirm={() => handleSwitchHouse(confirmSwitch.houseId, confirmSwitch.houseCode)}
        onCancel={() => setConfirmSwitch({ open: false, houseId: null, houseCode: '' })}
      />
      <ConfirmModal
        open={showLogoutConfirm}
        title={t('profile.logoutConfirmTitle')}
        message={t('profile.logoutConfirmMsg')}
        variant="warning"
        confirmText={t('profile.logout')}
        onConfirm={handleLogout}
        onCancel={() => setShowLogoutConfirm(false)}
      />
    </MobileLayout>
  );
}
