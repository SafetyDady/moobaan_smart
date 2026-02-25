import { useState, useEffect } from 'react';
import { Gift } from 'lucide-react';
import { creditNotesAPI, promotionsAPI } from '../api/client';
import { t } from '../hooks/useLocale';

/**
 * Credit Note Modal (Phase D.2-UI + D.4 Promotion Suggestions)
 * 
 * Allows Admin to create a credit note to reduce invoice outstanding amount.
 * Credit notes are IMMUTABLE - cannot be edited/deleted after creation.
 * 
 * Phase D.4: If payinId is provided, evaluates promotions and shows suggestions.
 */
export default function CreditNoteModal({ isOpen, onClose, invoice, payinId, onSuccess }) {
  const [form, setForm] = useState({
    credit_amount: '',
    reason: '',
    is_full_credit: false,
    confirm: false
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  const [promotionSuggestion, setPromotionSuggestion] = useState(null);
  const [loadingPromotion, setLoadingPromotion] = useState(false);

  useEffect(() => {
    if (isOpen && invoice) {
      setForm({
        credit_amount: '',
        reason: '',
        is_full_credit: false,
        confirm: false
      });
      setError('');
      setPromotionSuggestion(null);
    }
  }, [isOpen, invoice]);

  useEffect(() => {
    if (isOpen && payinId) {
      setLoadingPromotion(true);
      promotionsAPI.evaluate(payinId)
        .then((res) => {
          const eligible = res.data.suggestions?.find(s => s.eligible);
          if (eligible) {
            setPromotionSuggestion(eligible);
          }
        })
        .catch((err) => {
          console.error('Failed to evaluate promotions:', err);
        })
        .finally(() => {
          setLoadingPromotion(false);
        });
    }
  }, [isOpen, payinId]);

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

  const handleUseSuggestion = () => {
    if (!promotionSuggestion) return;
    const suggestedAmount = Math.min(promotionSuggestion.suggested_credit, outstanding);
    setForm(prev => ({
      ...prev,
      credit_amount: suggestedAmount.toString(),
      reason: `${t('creditNote.promotion')}: ${promotionSuggestion.promotion_name} (${promotionSuggestion.promotion_code})`,
      is_full_credit: false
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const amount = parseFloat(form.credit_amount);
    if (isNaN(amount) || amount <= 0) {
      setError(t('creditNote.invalidAmount'));
      return;
    }

    if (amount > outstanding) {
      setError(`${t('creditNote.exceedsOutstanding')} (${t('creditNote.max')} ฿${outstanding.toLocaleString()})`);
      return;
    }

    if (!form.reason.trim()) {
      setError(t('creditNote.pleaseSpecifyReason'));
      return;
    }

    if (!form.confirm) {
      setError(t('creditNote.pleaseConfirm'));
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

      onSuccess?.();
      onClose();
    } catch (err) {
      console.error('Create credit note error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        if (detail.includes('exceeds')) {
          setError(t('creditNote.exceedsOutstandingError'));
        } else if (detail.includes('fully credited')) {
          setError(t('creditNote.alreadyFullyCredited'));
        } else {
          setError(detail);
        }
      } else {
        setError(t('creditNote.createFailed'));
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
            <h2 className="text-xl font-bold text-white">{t('creditNote.title')}</h2>
            <p className="text-gray-400 text-sm">{t('creditNote.subtitle')}</p>
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
              <span className="text-gray-400">{t('creditNote.invoice')}</span>
              <span className="text-white font-medium">#{invoice.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{t('invoices.house')}</span>
              <span className="text-white">{invoice.house_number || invoice.house_code}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">{t('applyPayment.cycleDesc')}</span>
              <span className="text-white">{invoice.cycle || invoice.manual_reason || '-'}</span>
            </div>
            <div className="flex justify-between text-sm border-t border-slate-600 pt-2 mt-2">
              <span className="text-gray-400">{t('invoices.total')}</span>
              <span className="text-white">฿{invoice.total.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-yellow-400 font-medium">{t('creditNote.outstanding')}</span>
              <span className="text-yellow-400 font-bold">฿{outstanding.toLocaleString()}</span>
            </div>
          </div>

          {/* Promotion Suggestion Banner */}
          {loadingPromotion && (
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
              <span className="text-blue-300 text-sm">{t('creditNote.checkingPromotion')}</span>
            </div>
          )}
          
          {promotionSuggestion && !loadingPromotion && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div><Gift size={28} className="text-green-400" /></div>
                <div className="flex-1">
                  <p className="text-green-300 font-medium text-sm">
                    {t('creditNote.promotion')}: {promotionSuggestion.promotion_name}
                  </p>
                  <p className="text-green-400 text-xs mt-1">
                    {t('creditNote.promotionCode')}: {promotionSuggestion.promotion_code}
                  </p>
                  <p className="text-white mt-2">
                    {t('creditNote.suggestedCredit')}: <span className="font-bold text-green-400">฿{promotionSuggestion.suggested_credit.toLocaleString()}</span>
                  </p>
                  <button
                    type="button"
                    onClick={handleUseSuggestion}
                    className="mt-3 px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-sm rounded-lg transition-colors"
                    disabled={submitting}
                  >
                    {t('creditNote.useSuggested')}
                  </button>
                </div>
              </div>
            </div>
          )}

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
              {t('creditNote.fullCredit')} (฿{outstanding.toLocaleString()})
            </label>
          </div>

          {/* Credit Amount */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              {t('creditNote.creditAmount')} <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              min="0.01"
              max={outstanding}
              step="0.01"
              value={form.credit_amount}
              onChange={(e) => setForm({ ...form, credit_amount: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent disabled:opacity-50"
              placeholder={`${t('creditNote.max')} ${outstanding.toLocaleString()}`}
              required
              disabled={submitting || form.is_full_credit}
            />
            {parseFloat(form.credit_amount) > outstanding && (
              <p className="text-red-400 text-xs mt-1">{t('creditNote.exceedsOutstanding')}</p>
            )}
          </div>

          {/* Reason */}
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              {t('creditNote.reason')} <span className="text-red-400">*</span>
            </label>
            <textarea
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              rows={2}
              placeholder={t('creditNote.reasonPlaceholder')}
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
                <span className="font-medium">{t('creditNote.confirmAction')}:</span> {t('creditNote.confirmWarning')} <span className="text-orange-400 font-bold">{t('creditNote.irreversible')}</span>
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
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={submitting || !form.confirm}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {submitting ? t('common.saving') : t('invoices.confirmCreditNote')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
