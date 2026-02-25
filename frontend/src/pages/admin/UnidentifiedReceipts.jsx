import { useState, useEffect, useRef } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/Toast';
import { SkeletonPage } from '../../components/Skeleton';
import { safeParseDate, formatThaiDate, formatThaiTime } from '../../utils/payinStatus';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function UnidentifiedReceipts() {
  const toast = useToast();
  const [transactions, setTransactions] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [creating, setCreating] = useState(false);
  const [slipFile, setSlipFile] = useState(null);
  const [slipPreview, setSlipPreview] = useState(null);
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    house_id: '',
    source: 'ADMIN_CREATED',
    admin_note: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [txRes, housesRes] = await Promise.all([
        api.get('/api/payin-state/unidentified-bank-credits'),
        api.get('/api/houses')
      ]);
      // API returns { count, transactions: [...] } - extract the array
      const txData = txRes.data;
      const txList = Array.isArray(txData) ? txData : (txData.transactions ?? txData.items ?? []);
      setTransactions(txList);
      setHouses(housesRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = (tx) => {
    setSelectedTx(tx);
    setFormData({
      house_id: '',
      source: 'ADMIN_CREATED',
      admin_note: ''
    });
    setSlipFile(null);
    setSlipPreview(null);
    setShowModal(true);
  };

  const handleSlipChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.warning('กรุณาเลือกไฟล์รูปภาพเท่านั้น');
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.warning('ไฟล์ต้องมีขนาดไม่เกิน 5MB');
        return;
      }
      setSlipFile(file);
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setSlipPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const clearSlip = () => {
    setSlipFile(null);
    setSlipPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCreate = async () => {
    if (!formData.house_id) {
      toast.warning('กรุณาเลือกบ้าน');
      return;
    }
    
    // Slip is REQUIRED for audit completeness
    if (!slipFile) {
      toast.warning('กรุณาแนบสลิปการโอนเงิน (จำเป็นสำหรับการตรวจสอบ)');
      return;
    }

    setCreating(true);
    try {
      // Step 1: Create Pay-in from bank transaction
      const createRes = await api.post('/api/payin-state/admin-create-from-bank', {
        bank_transaction_id: selectedTx.id,
        house_id: parseInt(formData.house_id),
        source: formData.source,
        note: formData.admin_note || null
      });
      
      const newPayinId = createRes.data?.payin?.id;
      
      // Step 2: Attach slip to the created Pay-in
      if (newPayinId && slipFile) {
        const slipFormData = new FormData();
        slipFormData.append('slip', slipFile);
        
        await api.post(`/api/payin-state/${newPayinId}/attach-slip`, slipFormData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }
      
      toast.success('สร้าง Pay-in และแนบสลิปสำเร็จ');
      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to create pay-in:', error);
      const errorMsg = error.response?.data?.detail || 'สร้าง Pay-in ไม่สำเร็จ';
      toast.error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <div className="p-4 sm:p-6 lg:p-8"><SkeletonPage /></div>;
  }

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">รายการเงินเข้าที่ยังไม่ระบุ</h1>
        <p className="text-gray-400">
          รายการ CREDIT จาก Bank Statement ที่ยังไม่ได้จับคู่กับ Pay-in ใดๆ
        </p>
      </div>

      {transactions.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-gray-400 text-lg">✅ ไม่มีรายการเงินเข้าที่รอระบุ</p>
          <p className="text-gray-500 mt-2">รายการ CREDIT ทั้งหมดได้จับคู่กับ Pay-in แล้ว</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>วันที่</th>
                  <th>รายละเอียด</th>
                  <th>จำนวนเงิน</th>
                  <th>ธนาคาร</th>
                  <th>การดำเนินการ</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => {
                  // Use effective_at (correct field from backend), NOT transaction_date
                  const txDate = formatThaiDate(tx.effective_at);
                  const txTime = formatThaiTime(tx.effective_at);
                  
                  return (
                    <tr key={tx.id}>
                      <td className="text-gray-300">
                        {txDate}
                        {txTime !== '-' && (
                          <span className="text-gray-500 text-sm ml-1">{txTime}</span>
                        )}
                      </td>
                      <td className="text-gray-300 max-w-xs truncate" title={tx.description}>
                        {tx.description || '-'}
                      </td>
                      <td className="font-medium text-green-400">
                        +฿{tx.amount?.toLocaleString('th-TH') ?? tx.credit?.toLocaleString('th-TH') ?? '0'}
                      </td>
                      <td className="text-gray-400">{tx.bank_name || '-'}</td>
                      <td>
                        <button
                          onClick={() => openCreateModal(tx)}
                          className="btn-primary text-sm"
                        >
                          สร้าง Pay-in
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Pay-in Modal */}
      {showModal && selectedTx && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">สร้าง Pay-in จากรายการธนาคาร</h3>
            
            <div className="mb-4 p-3 bg-gray-700 rounded">
              <p className="text-gray-300 text-sm">
                <strong>วันที่:</strong> {formatThaiDate(selectedTx.effective_at)} {formatThaiTime(selectedTx.effective_at)}
              </p>
              <p className="text-gray-300 text-sm">
                <strong>จำนวนเงิน:</strong> ฿{selectedTx.amount?.toLocaleString('th-TH') ?? selectedTx.credit?.toLocaleString('th-TH') ?? '0'}
              </p>
              <p className="text-gray-300 text-sm truncate">
                <strong>รายละเอียด:</strong> {selectedTx.description || '-'}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">บ้าน *</label>
                <select
                  value={formData.house_id}
                  onChange={(e) => setFormData({ ...formData, house_id: e.target.value })}
                  className="input w-full"
                >
                  <option value="">-- เลือกบ้าน --</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} - {house.owner_name || 'ไม่ระบุชื่อ'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">แหล่งที่มา</label>
                <select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="input w-full"
                >
                  <option value="ADMIN_CREATED">Admin สร้าง</option>
                  <option value="LINE_RECEIVED">รับจาก LINE</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">หมายเหตุ (ถ้ามี)</label>
                <textarea
                  value={formData.admin_note}
                  onChange={(e) => setFormData({ ...formData, admin_note: e.target.value })}
                  className="input w-full"
                  rows="2"
                  placeholder="เช่น ลูกบ้านโทรมาแจ้ง..."
                />
              </div>

              {/* Slip Upload - REQUIRED */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  สลิปการโอนเงิน <span className="text-red-400">*</span>
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleSlipChange}
                  className="hidden"
                />
                
                {!slipPreview ? (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full border-2 border-dashed border-gray-600 rounded-lg p-4 text-center hover:border-primary-500 transition-colors"
                  >
                    <Upload className="mx-auto mb-2 text-gray-400" size={24} />
                    <p className="text-sm text-gray-400">คลิกเพื่อเลือกรูปสลิป</p>
                    <p className="text-xs text-gray-500 mt-1">รองรับ JPG, PNG (สูงสุด 5MB)</p>
                  </button>
                ) : (
                  <div className="relative">
                    <img
                      src={slipPreview}
                      alt="Slip preview"
                      className="w-full max-h-48 object-contain rounded-lg border border-gray-600"
                    />
                    <button
                      type="button"
                      onClick={clearSlip}
                      className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 hover:bg-red-700"
                    >
                      <X size={16} />
                    </button>
                    <p className="text-xs text-gray-400 mt-1 text-center">{slipFile?.name}</p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="btn-secondary"
                disabled={creating}
              >
                ยกเลิก
              </button>
              <button
                onClick={handleCreate}
                className="btn-primary"
                disabled={creating}
              >
                {creating ? 'กำลังสร้าง...' : 'สร้าง Pay-in'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}
