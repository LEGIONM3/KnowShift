import { useState } from 'react';
import { AlertCircle, X } from 'lucide-react';

/**
 * ErrorBanner — dismissible error notification strip.
 *
 * @param {string}        message    Error text to display
 * @param {Function|null} onDismiss  Optional callback when dismissed
 */
export function ErrorBanner({ message, onDismiss }) {
  const [visible, setVisible] = useState(true);

  if (!visible || !message) return null;

  const handleDismiss = () => {
    setVisible(false);
    onDismiss?.();
  };

  return (
    <div
      role="alert"
      className="flex items-start gap-3 p-4 bg-red-950/50
                 border border-red-700 rounded-lg text-red-300"
    >
      <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <p className="flex-1 text-sm">{message}</p>
      <button
        onClick={handleDismiss}
        aria-label="Dismiss error"
        className="text-red-400 hover:text-red-300 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
