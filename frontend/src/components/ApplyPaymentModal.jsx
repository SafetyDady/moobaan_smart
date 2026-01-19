import { useState, useEffect } from 'react';
import { invoicesAPI } from '../api/client';

export default function ApplyPaymentModal({ 
  isOpen, 
  onClose, 
  invoice, 
  onSuccess 
}) {
  const [ledgers, setLedgers] = useState([]);
  const [selectedLedger, setSelectedLedger] = useState(null);
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && invoice) {
      loadAllocatableLedgers();
      setSelectedLedger(null);
      setAmount('');
      setNote('');
      setError('');
    }
  }, [isOpen, invoice]);

  const loadAllocatableLedgers = async () => {
    setLoading(true);
    try {
      const response = await invoicesAPI.getAllocatableLedgers(invoice.house_id);
      const ledgerList = response.data.ledgers || [];
      setLedgers(ledgerList);
      
      // Auto-select first ledger and set default amount
      if (ledgerList.length > 0) {
        const firstLedger = ledgerList[0];
        setSelectedLedger(firstLedger);
        const outstanding = invoice.outstanding || invoice.total_amount || 0;
        const maxAmount = Math.min(outstanding, firstLedger.remaining);
        setAmount(maxAmount.toString());
      }
    } catch (err) {
      console.error('Failed to load ledgers:', err);
      setError('ไม่สามารถโหลดรายการ Ledger ได้');
    } finally {
      setLoading(false);
    }
  };

  const handleLedgerSelect = (ledger) => {
    setSelectedLedger(ledger);
    // Default amount = min(outstanding, ledger remaining)
    const maxAmount = Math.min(invoice.outstanding || invoice.total_amount, ledger.remaining);
    setAmount(maxAmount.toString());
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedLedger || !amount) return;

    const applyAmount = parseFloat(amount);
    
    // Validate
    if (applyAmount <= 0) {
      setError('จำนวนเงินต้องมากกว่า 0');
      return;
    }
    if (applyAmount > selectedLedger.remaining) {
      setError(`จำนวนเงินเกินยอดคงเหลือของ Ledger (฿${selectedLedger.remaining.toLocaleString()})`);
      return;
    }
    if (applyAmount > (invoice.outstanding || invoice.total_amount)) {
      setError(`จำนวนเงินเกินยอดค้างชำระ (฿${(invoice.outstanding || invoice.total_amount).toLocaleString()})`);
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await invoicesAPI.applyPayment(invoice.id, {
        income_transaction_id: selectedLedger.id,
        amount: applyAmount,
        note: note || undefined
      });
      
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Failed to apply payment:', err);
      setError(err.response?.data?.detail || 'ไม่สามารถบันทึกการชำระเงินได้');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const outstanding = invoice?.outstanding ?? invoice?.total_amount ?? 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-xl font-bold text-white">Apply Payment / ชำระเงิน</h2>
          <p className="text-gray-400 text-sm mt-1">
            Invoice #{invoice?.id} - {invoice?.house_code}
          </p>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Invoice Summary */}
          <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-gray-400 text-sm">Total Amount</div>
                <div className="text-white font-bold text-lg">
                  ฿{(invoice?.total_amount || 0).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Paid</div>
                <div className="text-green-400 font-bold text-lg">
                  ฿{((invoice?.total_amount || 0) - outstanding).toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm">Outstanding</div>
                <div className="text-yellow-400 font-bold text-lg">
                  ฿{outstanding.toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Ledger Selection */}
          <div className="mb-6">
            <h3 className="text-white font-medium mb-3">Select Ledger Entry / เลือกรายการรับเงิน</h3>
            
            {loading ? (
              <div className="text-center py-8 text-gray-400">Loading...</div>
            ) : ledgers.length === 0 ? (
              <div className="text-center py-8 text-gray-400 bg-slate-700/30 rounded-lg">
                <p>ไม่มี Ledger ที่สามารถใช้ชำระได้</p>
                <p className="text-sm mt-1">บ้านนี้ยังไม่มีรายการรับเงินที่ผ่านการยืนยัน</p>
              </div>
            ) : (
              <div className="space-y-2">
                {ledgers.map((ledger) => (
                  <div
                    key={ledger.id}
                    onClick={() => handleLedgerSelect(ledger)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      selectedLedger?.id === ledger.id
                        ? 'bg-primary-600/30 border-2 border-primary-500'
                        : 'bg-slate-700/50 border-2 border-transparent hover:border-slate-500'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="text-white font-medium">
                          Ledger #{ledger.id} - Pay-in #{ledger.payin_id}
                        </div>
                        <div className="text-gray-400 text-sm mt-1">
                          Received: {ledger.received_at ? new Date(ledger.received_at).toLocaleDateString('th-TH') : '-'}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-gray-400 text-sm">Remaining</div>
                        <div className="text-green-400 font-bold">
                          ฿{ledger.remaining.toLocaleString()}
                        </div>
                        <div className="text-gray-500 text-xs">
                          of ฿{ledger.amount.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Amount Input */}
          {selectedLedger && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Amount to Apply / จำนวนเงินที่ต้องการชำระ
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">฿</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={Math.min(outstanding, selectedLedger.remaining)}
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full bg-slate-700 text-white rounded-lg pl-8 pr-4 py-3 focus:ring-2 focus:ring-primary-500 focus:outline-none"
                    placeholder="0.00"
                    required
                  />
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-400">
                    Max: ฿{Math.min(outstanding, selectedLedger.remaining).toLocaleString()}
                  </span>
                  <button
                    type="button"
                    onClick={() => setAmount(Math.min(outstanding, selectedLedger.remaining).toString())}
                    className="text-primary-400 hover:text-primary-300"
                  >
                    Apply Max
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Note (Optional) / หมายเหตุ
                </label>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-primary-500 focus:outline-none"
                  placeholder="Optional note..."
                />
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors"
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedLedger || !amount || submitting}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Processing...' : 'Apply Payment'}
          </button>
        </div>
      </div>
    </div>
  );
}
