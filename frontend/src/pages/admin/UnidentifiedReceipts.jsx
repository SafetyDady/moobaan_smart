import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import { safeParseDate, formatThaiDate, formatThaiTime } from '../../utils/payinStatus';

export default function UnidentifiedReceipts() {
  const [transactions, setTransactions] = useState([]);
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [creating, setCreating] = useState(false);
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
    setShowModal(true);
  };

  const handleCreate = async () => {
    if (!formData.house_id) {
      alert('กรุณาเลือกบ้าน');
      return;
    }

    setCreating(true);
    try {
      await api.post('/api/payin-state/admin-create-from-bank', {
        bank_transaction_id: selectedTx.id,
        house_id: parseInt(formData.house_id),
        source: formData.source,
        admin_note: formData.admin_note || null
      });
      alert('สร้าง Pay-in สำเร็จ');
      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to create pay-in:', error);
      alert(error.response?.data?.detail || 'สร้าง Pay-in ไม่สำเร็จ');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-gray-400">Loading...</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">รายการเงินเข้าที่ยังไม่ระบุ</h1>
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
                        +฿{tx.amount?.toLocaleString() ?? tx.credit?.toLocaleString() ?? '0'}
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
                <strong>จำนวนเงิน:</strong> ฿{selectedTx.amount?.toLocaleString() ?? selectedTx.credit?.toLocaleString() ?? '0'}
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
  );
}
