import { useEffect, useRef } from 'react';
import { AlertTriangle, Info, Trash2, X } from 'lucide-react';

/**
 * ConfirmModal — drop-in replacement for window.confirm()
 *
 * Usage:
 *   <ConfirmModal
 *     open={showConfirm}
 *     title="ยืนยันการลบ"
 *     message="คุณต้องการลบรายการนี้ใช่หรือไม่?"
 *     variant="danger"          // "danger" | "warning" | "info" (default)
 *     confirmText="ลบ"          // default "ยืนยัน"
 *     cancelText="ยกเลิก"       // default "ยกเลิก"
 *     onConfirm={() => { ... }}
 *     onCancel={() => setShowConfirm(false)}
 *   />
 */
const VARIANTS = {
  danger: {
    icon: Trash2,
    iconBg: 'bg-red-900/50',
    iconColor: 'text-red-400',
    confirmBtn: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-yellow-900/50',
    iconColor: 'text-yellow-400',
    confirmBtn: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
  },
  info: {
    icon: Info,
    iconBg: 'bg-blue-900/50',
    iconColor: 'text-blue-400',
    confirmBtn: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
  },
};

export default function ConfirmModal({
  open,
  title = 'ยืนยันการดำเนินการ',
  message = 'คุณต้องการดำเนินการนี้ใช่หรือไม่?',
  variant = 'info',
  confirmText = 'ยืนยัน',
  cancelText = 'ยกเลิก',
  onConfirm,
  onCancel,
}) {
  const cancelRef = useRef(null);
  const v = VARIANTS[variant] || VARIANTS.info;
  const Icon = v.icon;

  // Focus cancel button on open & trap Escape key
  useEffect(() => {
    if (!open) return;
    cancelRef.current?.focus();

    const handleKey = (e) => {
      if (e.key === 'Escape') onCancel?.();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div className="relative bg-slate-800 rounded-xl shadow-2xl border border-gray-700 w-full max-w-md animate-in fade-in zoom-in duration-200">
        {/* Close button */}
        <button
          onClick={onCancel}
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

        {/* Actions */}
        <div className="flex gap-3 px-6 pb-6">
          <button
            ref={cancelRef}
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-300 bg-slate-700 rounded-lg hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={() => {
              onConfirm?.();
              onCancel?.();
            }}
            className={`flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-lg focus:outline-none focus:ring-2 transition-colors ${v.confirmBtn}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
