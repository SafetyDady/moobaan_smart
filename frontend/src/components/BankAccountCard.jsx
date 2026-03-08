import { useState } from 'react';
import { Copy, Check, Building2 } from 'lucide-react';
import { t } from '../hooks/useLocale';

export default function BankAccountCard({ bankName, accountNo, accountName }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(accountNo.replace(/-/g, ''));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = accountNo.replace(/-/g, '');
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Building2 size={18} className="text-emerald-400" />
        <span className="text-sm font-semibold text-gray-200">
          {t('mobileDashboard.transferToAccount')}
        </span>
      </div>

      <p className="text-xs text-gray-400 mb-1">{bankName}</p>

      <div className="flex items-center justify-between mb-2">
        <span className="text-lg font-bold text-white tracking-wider">{accountNo}</span>
        <button
          onClick={handleCopy}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            copied
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-gray-700 text-gray-300 active:bg-gray-600'
          }`}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? t('mobileDashboard.copied') : t('mobileDashboard.copyAccountNo')}
        </button>
      </div>

      <p className="text-xs text-gray-400">{accountName}</p>
    </div>
  );
}
