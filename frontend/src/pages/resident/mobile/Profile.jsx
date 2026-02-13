import { useState } from 'react';
import { ChevronLeft, LogOut, Home, User, Mail, Phone, Edit3, Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import { useRole } from '../../../contexts/RoleContext';
import { authAPI } from '../../../api/client';
import MobileLayout from './MobileLayout';

export default function Profile() {
  const navigate = useNavigate();
  const { user, logout, updateUser } = useAuth();
  const { currentHouseCode } = useRole();
  const [toast, setToast] = useState(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
  });
  
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
      showToast('✅ บันทึกข้อมูลเรียบร้อย', 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'เกิดข้อผิดพลาด';
      showToast(`❌ ${msg}`, 'error');
    } finally {
      setSaving(false);
    }
  };
  
  const handleLogout = async () => {
    if (confirm('ต้องการออกจากระบบหรือไม่?')) {
      await logout();
      navigate('/login');
    }
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
            <h1 className="text-lg font-bold text-white">โปรไฟล์</h1>
          </div>
          {!editing && (
            <button
              onClick={startEdit}
              className="flex items-center gap-1 text-primary-400 active:text-primary-300 text-sm"
            >
              <Edit3 size={16} />
              <span>แก้ไข</span>
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
                <label className="text-xs text-gray-400 mb-1 block">ชื่อ-นามสกุล</label>
                <div className="flex items-center gap-2">
                  <User size={18} className="text-gray-400 shrink-0" />
                  <input
                    type="text"
                    value={form.full_name}
                    onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-primary-500"
                    placeholder="ระบุชื่อ-นามสกุล"
                  />
                </div>
              </div>
              
              <div className="p-4">
                <label className="text-xs text-gray-400 mb-1 block">อีเมล</label>
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
                <label className="text-xs text-gray-400 mb-1 block">เบอร์โทรศัพท์</label>
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
                  <div className="text-xs text-gray-400 mb-1">บ้านเลขที่</div>
                  <div className="flex items-center gap-2 text-gray-400">
                    <Home size={18} />
                    <span className="text-white">{currentHouseCode}</span>
                    <span className="text-xs text-gray-500 ml-auto">แก้ไขไม่ได้</span>
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
                  <span>ยกเลิก</span>
                </button>
                <button
                  onClick={saveProfile}
                  disabled={saving}
                  className="flex-1 flex items-center justify-center gap-1 py-2.5 rounded-lg bg-primary-500 text-white active:bg-primary-600 text-sm font-medium disabled:opacity-50"
                >
                  <Check size={16} />
                  <span>{saving ? 'กำลังบันทึก...' : 'บันทึก'}</span>
                </button>
              </div>
            </div>
          ) : (
            /* ─── View Mode ─── */
            <div className="bg-gray-800 rounded-lg border border-gray-700 divide-y divide-gray-700">
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">ชื่อ-นามสกุล</div>
                <div className="flex items-center gap-2 text-white">
                  <User size={18} className="text-gray-400" />
                  <span>{user?.full_name || 'ไม่ได้ระบุ'}</span>
                </div>
              </div>
              
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">อีเมล</div>
                <div className="flex items-center gap-2 text-white">
                  <Mail size={18} className="text-gray-400" />
                  <span className={user?.email ? 'text-white' : 'text-gray-500 italic'}>
                    {user?.email || 'ยังไม่ได้กรอก — กดแก้ไขเพื่อเพิ่ม'}
                  </span>
                </div>
              </div>
              
              <div className="p-4">
                <div className="text-xs text-gray-400 mb-1">เบอร์โทรศัพท์</div>
                <div className="flex items-center gap-2 text-white">
                  <Phone size={18} className="text-gray-400" />
                  <span className={user?.phone ? 'text-white' : 'text-gray-500 italic'}>
                    {user?.phone || 'ยังไม่ได้กรอก — กดแก้ไขเพื่อเพิ่ม'}
                  </span>
                </div>
              </div>
              
              {currentHouseCode && (
                <div className="p-4">
                  <div className="text-xs text-gray-400 mb-1">บ้านเลขที่</div>
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
                <span className="text-lg">🟢</span>
                <span className="text-white text-sm">LINE เชื่อมต่อ</span>
              </div>
              <span className="text-xs text-green-400">เข้าสู่ระบบผ่าน LINE</span>
            </div>
            
            {user?.houses && user.houses.length > 1 && (
              <div className="p-4 border-t border-gray-700">
                <div className="text-xs text-gray-400 mb-2">บ้านที่เชื่อมต่อ</div>
                <div className="flex flex-wrap gap-2">
                  {user.houses.map(h => (
                    <span key={h.id} className={`text-xs px-2 py-1 rounded-full ${
                      h.house_code === currentHouseCode 
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' 
                        : 'bg-gray-700 text-gray-300'
                    }`}>
                      บ้าน {h.house_code}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* About Section */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-300 mb-2">เกี่ยวกับ</h3>
            <div className="text-xs text-gray-400 space-y-1">
              <div>แอปพลิเคชัน: Moobaan Smart</div>
              <div>เวอร์ชัน: 1.0.0</div>
              <div>© 2026 Moobaan Smart. All rights reserved.</div>
            </div>
          </div>
          
          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full bg-red-500/10 border border-red-500 text-red-400 rounded-lg p-4 flex items-center justify-center gap-2 font-medium active:bg-red-500/20"
          >
            <LogOut size={20} />
            <span>ออกจากระบบ</span>
          </button>
          
          <div className="h-4"></div>
        </div>
      </div>
    </MobileLayout>
  );
}
