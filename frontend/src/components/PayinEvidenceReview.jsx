import { useEffect, useState } from 'react';
import { payinsAPI } from '../api/client';
import { t } from '../hooks/useLocale';

const dateTime = (value) => value ? new Date(value).toLocaleString('th-TH', { timeZone: 'Asia/Bangkok' }) : '-';
const money = (value) => Number(value).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// A comparison for human review, not automatic verification of the slip image.
export default function PayinEvidenceReview({ payinId, candidate, onConfirm, onCancel }) {
  const [payin, setPayin] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const [imageReady, setImageReady] = useState(false);
  useEffect(() => {
    let active = true;
    setPayin(null); setError(''); setImageFailed(false); setImageReady(false);
    payinsAPI.get(payinId).then(({ data }) => { if (active) setPayin(data); })
      .catch(() => { if (active) setError(t('payins.reviewLoadFailed')); });
    return () => { active = false; };
  }, [payinId]);
  const bank = candidate || payin?.matched_statement;
  const amountDiff = payin && bank ? Math.abs(Math.round(Number(payin.amount) * 100) - Math.round(Number(bank.credit) * 100)) : null;
  const timeDiff = payin && bank ? Math.abs(new Date(payin.transfer_date) - new Date(bank.effective_at)) / 1000 : null;
  const invalid = !payin || !bank || !Number.isFinite(amountDiff) || !Number.isFinite(timeDiff) || amountDiff > 1 || timeDiff > 60;
  const changed = !invalid && (amountDiff > 0 || timeDiff > 0);
  const reviewable = ['PENDING', 'SUBMITTED'].includes(payin?.status);
  const staleCandidate = candidate && payin?.matched_statement_txn_id;
  const submit = async () => {
    setBusy(true); setError('');
    try { await onConfirm(payin, bank); }
    catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : detail?.message || t('payins.reviewActionFailed'));
    } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-[10000] bg-black/70 flex items-center justify-center p-3">
      <div role="dialog" aria-modal="true" aria-labelledby="evidence-title" className="bg-slate-800 border border-slate-600 rounded-xl p-4 w-full max-w-5xl max-h-[95vh] overflow-y-auto">
        <h2 id="evidence-title" className="text-xl text-white font-semibold mb-3">{t('payins.reviewEvidence')}</h2>
        {!payin && !error && <p>{t('common.loading')}</p>}
        {payin && <>
          <p className="text-white mb-3">{t('payins.house')}: <strong>{payin.house_number}</strong></p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <section className="bg-slate-900 rounded p-3 min-w-0">
              <h3 className="text-white font-semibold mb-2">{t('payins.slip')}</h3>
              {payin.slip_image_url && !imageFailed ? <a href={payinsAPI.slipUrl(payin.id)} target="_blank" rel="noreferrer">
                <img src={payinsAPI.slipUrl(payin.id)} alt={t('payins.slip')} onLoad={() => setImageReady(true)} onError={() => setImageFailed(true)} className="w-full max-h-80 object-contain" />
              </a> : <p className="text-amber-300">{t(imageFailed ? 'payins.reviewImageFailed' : 'payins.reviewNoSlip')}</p>}
            </section>
            <section className="bg-slate-900 rounded p-3 min-w-0">
              <h3 className="text-white font-semibold mb-2">{t('payins.reviewEntered')}</h3>
              <p className="text-white text-lg tabular-nums">฿{money(payin.amount)}</p>
              <p className="text-slate-300 mt-2">{dateTime(payin.transfer_date)}</p>
            </section>
            <section className="bg-slate-900 rounded p-3 min-w-0 break-words">
              <h3 className="text-white font-semibold mb-2">{t('payins.reviewStatement')}</h3>
              {bank ? <>
                <p className="text-white text-lg tabular-nums">฿{money(bank.credit)}</p>
                <p className="text-slate-300 mt-2">{dateTime(bank.effective_at)}</p>
                <p className="text-slate-300 mt-2">{bank.description || '-'}</p>
                <p className="text-slate-400 mt-2">{t('payins.channelLabel')}: {bank.channel || '-'}</p>
              </> : <p className="text-amber-300">{t('payins.reviewNoStatement')}</p>}
            </section>
          </div>
          <p className={`rounded p-3 mt-3 ${invalid || !reviewable || staleCandidate ? 'bg-red-950 text-red-300' : 'bg-amber-950 text-amber-200'}`}>
            {t(invalid || !reviewable || staleCandidate ? 'payins.reviewMismatch' : changed ? 'payins.reviewSmallDifference' : 'payins.reviewImageReminder')}
          </p>
        </>}
        {error && <p role="alert" className="text-red-300 mt-3">{error}</p>}
        <div className="flex justify-end gap-3 mt-4">
          <button onClick={onCancel} disabled={busy} className="btn-secondary">{t('common.cancel')}</button>
          <button onClick={submit} disabled={busy || invalid || imageFailed || (payin?.slip_image_url && !imageReady) || !reviewable || !!staleCandidate} className="btn-primary disabled:opacity-50">
            {busy ? t('common.loading') : t(candidate ? 'payins.reviewConfirmMatch' : 'payins.confirmAndPostBtn')}
          </button>
        </div>
      </div>
    </div>
  );
}
