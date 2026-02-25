import { Component } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

/**
 * ErrorBoundary — catches unhandled JS errors in child components
 *
 * Usage (wrap around routes or major sections):
 *   <ErrorBoundary>
 *     <App />
 *   </ErrorBoundary>
 *
 * Or with a custom fallback:
 *   <ErrorBoundary fallback={<MyCustomError />}>
 *     <SomeComponent />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to console for debugging
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDev = import.meta.env?.DEV;

      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-lg w-full p-8 text-center">
            {/* Icon */}
            <div className="mx-auto w-16 h-16 rounded-full bg-red-900/50 flex items-center justify-center mb-6">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold text-white mb-2">
              เกิดข้อผิดพลาด
            </h1>
            <p className="text-gray-400 mb-6">
              ระบบพบข้อผิดพลาดที่ไม่คาดคิด กรุณาลองใหม่อีกครั้ง
            </p>

            {/* Error details (dev only) */}
            {isDev && this.state.error && (
              <div className="bg-slate-900 border border-slate-600 rounded-lg p-4 mb-6 text-left overflow-auto max-h-48">
                <p className="text-red-400 text-sm font-mono break-all">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo?.componentStack && (
                  <pre className="text-gray-500 text-xs mt-2 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-500 transition-colors font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                ลองใหม่
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 text-gray-300 rounded-lg hover:bg-slate-600 transition-colors font-medium"
              >
                <Home className="w-4 h-4" />
                กลับหน้าหลัก
              </button>
            </div>

            {/* Reload hint */}
            <p className="text-gray-500 text-xs mt-4">
              หากปัญหายังคงอยู่{' '}
              <button onClick={this.handleReload} className="text-primary-400 hover:underline">
                รีโหลดหน้าเว็บ
              </button>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
