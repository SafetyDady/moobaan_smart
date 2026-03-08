import { CheckCircle, Circle, XCircle, Clock, Loader2 } from 'lucide-react';
import { t } from '../hooks/useLocale';

/**
 * Payment Status Timeline
 * Shows the progress of the most recent payment report.
 *
 * Status mapping:
 *   SUBMITTED / PENDING → step 1 done, step 2 in-progress
 *   ACCEPTED            → all steps done
 *   REJECTED_NEEDS_FIX  → step 2 failed
 *   DRAFT               → not shown (parent should hide)
 */
export default function PaymentTimeline({ payin }) {
  if (!payin) return null;

  const status = payin.status;
  const amount = payin.amount;
  const date = payin.transfer_date
    ? new Date(payin.transfer_date).toLocaleDateString('th-TH', { day: 'numeric', month: 'short' })
    : '';

  const isRejected = status === 'REJECTED_NEEDS_FIX' || status === 'REJECTED';
  const isAccepted = status === 'ACCEPTED';
  const isPending = status === 'SUBMITTED' || status === 'PENDING';

  // Define 3 steps
  const steps = [
    {
      label: t('timeline.submitted'),
      detail: `฿${Number(amount).toLocaleString()} • ${date}`,
      state: 'done', // always done if payin exists
    },
    {
      label: isRejected ? t('timeline.rejected') : t('timeline.reviewing'),
      detail: isRejected ? payin.reject_reason || '' : isPending ? t('timeline.reviewingDetail') : '',
      state: isAccepted ? 'done' : isRejected ? 'failed' : 'active',
    },
    {
      label: t('timeline.confirmed'),
      detail: isAccepted ? t('timeline.confirmedDetail') : '',
      state: isAccepted ? 'done' : 'pending',
    },
  ];

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <p className="text-sm font-semibold text-gray-200 mb-4">
        {t('timeline.title')}
      </p>

      <div className="relative">
        {steps.map((step, i) => {
          const isLast = i === steps.length - 1;
          return (
            <div key={i} className="flex gap-3" style={{ minHeight: isLast ? 'auto' : '48px' }}>
              {/* Dot + Line */}
              <div className="flex flex-col items-center">
                <StepIcon state={step.state} />
                {!isLast && (
                  <div className={`w-0.5 flex-1 mt-1 ${
                    step.state === 'done' ? 'bg-emerald-500/50' :
                    step.state === 'failed' ? 'bg-red-500/50' : 'bg-gray-600'
                  }`} />
                )}
              </div>

              {/* Label + Detail */}
              <div className="pb-3">
                <p className={`text-sm font-medium leading-5 ${
                  step.state === 'done' ? 'text-emerald-400' :
                  step.state === 'active' ? 'text-amber-400' :
                  step.state === 'failed' ? 'text-red-400' : 'text-gray-500'
                }`}>
                  {step.label}
                </p>
                {step.detail && (
                  <p className="text-xs text-gray-500 mt-0.5">{step.detail}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StepIcon({ state }) {
  switch (state) {
    case 'done':
      return <CheckCircle size={20} className="text-emerald-400 shrink-0" />;
    case 'active':
      return (
        <div className="relative shrink-0">
          <Clock size={20} className="text-amber-400 animate-pulse" />
        </div>
      );
    case 'failed':
      return <XCircle size={20} className="text-red-400 shrink-0" />;
    default: // pending
      return <Circle size={20} className="text-gray-600 shrink-0" />;
  }
}
