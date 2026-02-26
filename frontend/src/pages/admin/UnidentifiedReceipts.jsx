import { useState, useEffect, useRef } from 'react';
import { Upload, X, Image as ImageIcon, CheckCircle } from 'lucide-react';
import { api } from '../../api/client';
import compressImage from '../../utils/compressImage';
import { useToast } from '../../components/Toast';
import { SkeletonPage } from '../../components/Skeleton';
import { safeParseDate, formatThaiDate, formatThaiTime } from '../../utils/payinStatus';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';


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

  // Sorting & Pagination
  const { sortConfig, requestSort, sortedData } = useSort(transactions);
  const paged = usePagination(sortedData);

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

  const handleSlipChange = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.warning(t('unidentified.imageOnly'));
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.warning(t('unidentified.maxFileSize'));
        return;
      }
      // Compress image before storing
      const compressed = await compressImage(file);
      setSlipFile(compressed);
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setSlipPreview(e.target.result);
      reader.readAsDataURL(compressed);
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
      toast.warning(t('unidentified.selectHouseRequired'));
      return;
    }
    
    // Slip is REQUIRED for audit completeness
    if (!slipFile) {
      toast.warning(t('unidentified.slipRequired'));
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
        // Ensure a safe filename with recognized extension (prevents 400 from backend)
        const safeName = (slipFile.name && slipFile.name !== 'blob' && /\.(jpe?g|png|gif|webp)$/i.test(slipFile.name))
          ? slipFile.name
          : 'slip.jpg';
        slipFormData.append('slip', slipFile, safeName);
        
        await api.post(`/api/payin-state/${newPayinId}/attach-slip`, slipFormData);
      }
      
      toast.success(t('unidentified.createSuccess'));
      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to create pay-in:', error);
      const errorMsg = error.response?.data?.detail || t('unidentified.createFailed');
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
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('unidentified.title')}</h1>
        <p className="text-gray-400">
          {t('unidentified.subtitle')}
        </p>
      </div>

      {transactions.length === 0 ? (
        <div className="card p-8">
          <EmptyState icon={<CheckCircle size={32} />} message={t('unidentified.allMatched')} description={t('unidentified.allMatchedDesc')} />
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <SortableHeader label={t('common.date')} sortKey="effective_at" sortConfig={sortConfig} onSort={requestSort} />
                  <SortableHeader label={t('common.description')} sortKey="description" sortConfig={sortConfig} onSort={requestSort} />
                  <SortableHeader label={t('common.amount')} sortKey="amount" sortConfig={sortConfig} onSort={requestSort} />
                  <th>{t('unidentified.bank')}</th>
                  <th>{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {paged.currentItems.map((tx) => {
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
                          {t('unidentified.createPayin')}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {transactions.length > 0 && <Pagination {...paged} />}
        </div>
      )}

      {/* Create Pay-in Modal */}
      {showModal && selectedTx && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">{t('unidentified.createPayinTitle')}</h3>
            
            <div className="mb-4 p-3 bg-gray-700 rounded">
              <p className="text-gray-300 text-sm">
                <strong>{t('unidentified.dateLabel')}</strong> {formatThaiDate(selectedTx.effective_at)} {formatThaiTime(selectedTx.effective_at)}
              </p>
              <p className="text-gray-300 text-sm">
                <strong>{t('unidentified.amountLabel')}</strong> ฿{selectedTx.amount?.toLocaleString('th-TH') ?? selectedTx.credit?.toLocaleString('th-TH') ?? '0'}
              </p>
              <p className="text-gray-300 text-sm truncate">
                <strong>{t('unidentified.descLabel')}</strong> {selectedTx.description || '-'}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('unidentified.houseLabel')}</label>
                <select
                  value={formData.house_id}
                  onChange={(e) => setFormData({ ...formData, house_id: e.target.value })}
                  className="input w-full"
                >
                  <option value="">{t('unidentified.selectHouse')}</option>
                  {houses.map((house) => (
                    <option key={house.id} value={house.id}>
                      {house.house_code} - {house.owner_name || t('unidentified.noOwnerName')}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('unidentified.sourceLabel')}</label>
                <select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="input w-full"
                >
                  <option value="ADMIN_CREATED">{t('unidentified.adminCreated')}</option>
                  <option value="LINE_RECEIVED">{t('unidentified.lineReceived')}</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">{t('unidentified.noteLabel')}</label>
                <textarea
                  value={formData.admin_note}
                  onChange={(e) => setFormData({ ...formData, admin_note: e.target.value })}
                  className="input w-full"
                  rows="2"
                  placeholder={t('unidentified.notePlaceholder')}
                />
              </div>

              {/* Slip Upload - REQUIRED */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  {t('unidentified.slipLabel')} <span className="text-red-400">*</span>
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
                    <p className="text-sm text-gray-400">{t('unidentified.slipClickToSelect')}</p>
                    <p className="text-xs text-gray-500 mt-1">{t('unidentified.slipFormat')}</p>
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
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCreate}
                className="btn-primary"
                disabled={creating}
              >
                {creating ? t('common.loading') : t('unidentified.createPayin')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}
