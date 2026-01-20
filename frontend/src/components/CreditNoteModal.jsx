import { useState, useEffect } from 'react';
import { creditNotesAPI } from '../api/client';

/**
 * Credit Note Modal (Phase D.2-UI)
 * 
 * Allows Admin to create a credit note to reduce invoice outstanding amount.
 * Credit notes are IMMUTABLE - cannot be edited/deleted after creation.
 */
export default function CreditNoteModal({ isOpen, onClose, invoice, onSuccess }) {
  const [form, setForm] = useState({
    credit_amount: '',
    reason: '',
    is_full_credit: false,
    confirm: false
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen && invoice) {
      setForm({
        credit_amount: '',
        reason: '',
        is_full_credit: false,
        confirm: false
      });
      setError('');
    }
  }, [isOpen, invoice]);

  // Handle full credit checkbox - auto-fill amount
  useEffect(() => {
    if (form.is_full_credit && invoice) {
      setForm(prev => ({
        ...prev,
        credit_amount: invoice.outstanding.toString()
      }));
    }
  }, [form.is_full_credit, invoice]);

  if (!isOpen || !invoice) return null;

  const outstanding = invoice.outstanding ?? (invoice.total - (invoice.paid || 0));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate
    const amount = parseFloat(form.credit_amount);
    if (isNaN(amount) || amount <= 0) {
      setError('กรุณาระบุจำนวนเงินที่ถูกต้อง');
      return;
    }

    if (amount > outstanding) {
      setError(`จำนวนเงินเกินยอดค้างชำระ (สูงสุด ฿${outstanding.toLocaleString()})`);
      return;
    }

    if (!form.reason.trim()) {
      setError('กรุณาระบุเหตุผล');
      return;
    }

    if (!form.confirm) {
      setError('กรุณายืนยันการดำเนินการ');
      return;
    }

    setSubmitting(true);
    try {
      await creditNotesAPI.create({
        invoice_id: invoice.id,
        credit_amount: amount,
        reason: form.reason.trim(),
        is_full_credit: form.is_full_credit
      });

      // Success
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Create credit note error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        // Map known error messages
        if (detail.includes('exceeds')) {
          setError('Credit amount exceeds outstanding / จำนวนเงินเกินยอดค้าง');
        } else if (detail.includes('fully credited')) {
          setError('Invoice already fully credited / Invoice ถูก Credit เต็มจำนวนแล้ว');
        } else {
          setError(detail);
        }
      } else {
        setError('ไม่สามารถสร้าง Credit Note ได้');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Create Credit Note</h2>
            <p className="text-gray-400 text-sm">ลดยอดค้างชำระ Invoice</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
            disabled={submitting}
          >
            ×
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Invoice Reference (readonly) */}
          <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Invoice</span>
              <span className="text-white font-medium">#{invoice.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">House</span>
              <span className="text-white">{invoice.house_number || invoice.house_code}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Cycle/Description</span>
              <span className="text-white">{invoice.cycle || invoice.manual_reason || '-'}</span>
            </div>
            <div className="flex justify-between text-sm border-t border-slate-600 pt-2 mt-2">
              <span className="text-gray-400">Total Amount</span>
              <span className="text-white">฿{invoice.total.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-yellow-400 font-medium">Outstanding</span>
              <span className="text-yellow-400 font-bold">฿{outstanding.toLocaleString()}</span>
            </div>
          </div>

          {/* Full Credit Checkbox */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_full_credit"
              checked={form.is_full_credit}
              onChange={(e) => setForm({ ...form, is_full_credit: e.target.checked })}
              className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-primary-600 focus:ring-primary-500"
              disabled={submitting}
            />
            <label htmlFor="is_full_credit" className="text-gray-300">
              Credit เต็มจำนวน (฿{outstanding.toLocaleString()})
            </label>
          </div>

          {/* Credit Amount */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Credit Amount (บาท) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              min="0.01"
              max={outstanding}
              step="0.01"
              value={form.credit_amount}
              onChange={(e) => setForm({ ...form, credit_amount: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:opacity-50"
              placeholder={`สูงสุด ${outstanding.toLocaleString()}`}
              required
              disabled={submitting || form.is_full_credit}
            />
            {parseFloat(form.credit_amount) > outstanding && (
              <p className="text-red-400 text-xs mt-1">เกินยอดค้างชำระ</p>
            )}
          </div>

          {/* Reason */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Reason / เหตุผล <span className="text-red-400">*</span>
            </label>
            <textarea
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              rows={2}
              placeholder="เช่น คิดค่าบริการผิด, ส่วนลดพิเศษ..."
              required
              disabled={submitting}
            />
          </div>

          {/* Confirmation Checkbox */}
          <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="confirm"
                checked={form.confirm}
                onChange={(e) => setForm({ ...form, confirm: e.target.checked })}
                className="w-5 h-5 mt-0.5 rounded border-slate-600 bg-slate-700 text-orange-600 focus:ring-orange-500"
                disabled={submitting}
              />
              <label htmlFor="confirm" className="text-orange-300 text-sm">
                <span className="font-medium">ยืนยันการดำเนินการ:</span> การสร้าง Credit Note จะลดยอดค้างชำระและ <span className="text-orange-400 font-bold">ไม่สามารถย้อนกลับได้</span>
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="flex-1 px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !form.confirm}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {submitting ? 'กำลังสร้าง...' : 'Confirm Credit Note'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
