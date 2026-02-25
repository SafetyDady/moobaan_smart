import { useEffect, useRef } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';

/**
 * AlertModal — drop-in replacement for window.alert()
 *
 * Usage:
 *   <AlertModal
 *     open={showAlert}
 *     title="สำเร็จ"
 *     message="บันทึกข้อมูลเรียบร้อยแล้ว"
 *     variant="success"         // "success" | "error" | "warning" | "info" (default)
 *     buttonText="ตกลง"         // default "ตกลง"
 *     onClose={() => setShowAlert(false)}
 *   />
 */
const VARIANTS = {
  success: {
    icon: CheckCircle,
    iconBg: 'bg-emerald-900/50',
    iconColor: 'text-emerald-400',
    btn: 'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500',
  },
  error: {
    icon: XCircle,
    iconBg: 'bg-red-900/50',
    iconColor: 'text-red-400',
    btn: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-yellow-900/50',
    iconColor: 'text-yellow-400',
    btn: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
  },
  info: {
    icon: Info,
    iconBg: 'bg-blue-900/50',
    iconColor: 'text-blue-400',
    btn: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  },
};

export default function AlertModal({
  open,
  title = 'แจ้งเตือน',
  message = '',
  variant = 'info',
  buttonText = 'ตกลง',
  onClose,
}) {
  const btnRef = useRef(null);
  const v = VARIANTS[variant] || VARIANTS.info;
  const Icon = v.icon;

  useEffect(() => {
    if (!open) return;
    btnRef.current?.focus();

    const handleKey = (e) => {
      if (e.key === 'Escape' || e.key === 'Enter') onClose?.();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative bg-slate-800 rounded-xl shadow-2xl border border-gray-700 w-full max-w-md animate-in fade-in zoom-in duration-200">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-6">
          {/* Icon */}
          <div className={`mx-auto w-12 h-12 rounded-full ${v.iconBg} flex items-center justify-center mb-4`}>
            <Icon className={`w-6 h-6 ${v.iconColor}`} />
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold text-white text-center mb-2">
            {title}
          </h3>

          {/* Message */}
          <p className="text-sm text-gray-300 text-center whitespace-pre-line">
            {message}
          </p>
        </div>

        {/* Action */}
        <div className="px-6 pb-6">
          <button
            ref={btnRef}
            onClick={onClose}
            className={`w-full px-4 py-2.5 text-sm font-medium text-white rounded-lg focus:outline-none focus:ring-2 transition-colors ${v.btn}`}
          >
            {buttonText}
          </button>
        </div>
      </div>
    </div>
  );
}
