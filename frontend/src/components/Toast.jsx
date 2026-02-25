import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';

/* ─── Toast Context ─── */
const ToastContext = createContext(null);

/**
 * useToast() — hook to show toast notifications
 *
 * const toast = useToast();
 * toast.success('บันทึกสำเร็จ');
 * toast.error('เกิดข้อผิดพลาด');
 * toast.warning('กรุณาตรวจสอบข้อมูล');
 * toast.info('กำลังดำเนินการ...');
 */
/**
 * Safe fallback: if ToastProvider is not yet mounted, useToast() returns
 * no-op functions that log to console instead of crashing the app.
 * This allows gradual integration — pages work before App.jsx is updated.
 */
const FALLBACK_TOAST = {
  success: (msg) => console.log('[Toast fallback] success:', msg),
  error:   (msg) => console.warn('[Toast fallback] error:', msg),
  warning: (msg) => console.warn('[Toast fallback] warning:', msg),
  info:    (msg) => console.log('[Toast fallback] info:', msg),
};

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Warn once in dev, but never crash
    if (import.meta.env?.DEV) {
      console.warn('[Toast] useToast() called outside <ToastProvider>. Using console fallback.');
    }
    return FALLBACK_TOAST;
  }
  return ctx;
}

/* ─── Variant config ─── */
const VARIANTS = {
  success: {
    icon: CheckCircle,
    bg: 'bg-emerald-900/90 border-emerald-700',
    iconColor: 'text-emerald-400',
    progressColor: 'bg-emerald-500',
  },
  error: {
    icon: XCircle,
    bg: 'bg-red-900/90 border-red-700',
    iconColor: 'text-red-400',
    progressColor: 'bg-red-500',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-yellow-900/90 border-yellow-700',
    iconColor: 'text-yellow-400',
    progressColor: 'bg-yellow-500',
  },
  info: {
    icon: Info,
    bg: 'bg-blue-900/90 border-blue-700',
    iconColor: 'text-blue-400',
    progressColor: 'bg-blue-500',
  },
};

/* ─── Single toast item ─── */
function ToastItem({ id, type, message, duration, onRemove }) {
  const v = VARIANTS[type] || VARIANTS.info;
  const Icon = v.icon;
  const [exiting, setExiting] = useState(false);
  const timerRef = useRef(null);

  const dismiss = useCallback(() => {
    setExiting(true);
    setTimeout(() => onRemove(id), 200);
  }, [id, onRemove]);

  useEffect(() => {
    timerRef.current = setTimeout(dismiss, duration);
    return () => clearTimeout(timerRef.current);
  }, [dismiss, duration]);

  return (
    <div
      className={`
        flex items-start gap-3 w-full max-w-sm px-4 py-3 rounded-lg border shadow-lg backdrop-blur-sm
        ${v.bg}
        ${exiting ? 'animate-out fade-out slide-out-to-right duration-200' : 'animate-in fade-in slide-in-from-right duration-300'}
      `}
      role="alert"
    >
      <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${v.iconColor}`} />
      <p className="flex-1 text-sm text-white whitespace-pre-line">{message}</p>
      <button
        onClick={dismiss}
        className="flex-shrink-0 text-gray-400 hover:text-white transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

/* ─── Provider ─── */
let toastIdCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((type, message, duration = 4000) => {
    const id = ++toastIdCounter;
    setToasts((prev) => [...prev, { id, type, message, duration }]);
    return id;
  }, []);

  const api = {
    success: (msg, dur) => addToast('success', msg, dur),
    error: (msg, dur) => addToast('error', msg, dur ?? 6000),
    warning: (msg, dur) => addToast('warning', msg, dur ?? 5000),
    info: (msg, dur) => addToast('info', msg, dur),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}

      {/* Toast container — fixed top-right */}
      <div className="fixed top-4 right-4 z-[9998] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <ToastItem {...t} onRemove={removeToast} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
