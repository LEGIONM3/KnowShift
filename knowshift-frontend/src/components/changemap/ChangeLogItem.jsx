import { Clock, AlertCircle, RefreshCw, CheckCircle } from 'lucide-react';
import { formatChangeType, timeAgo, truncate } from '../../utils/formatting';

/** Icon + color theme per change_type */
const CHANGE_CONFIG = {
  deprecated:   { Icon: AlertCircle, color: 'text-red-400',    bg: 'bg-red-900/20'    },
  updated:      { Icon: CheckCircle, color: 'text-green-400',  bg: 'bg-green-900/20'  },
  're-indexed': { Icon: RefreshCw,   color: 'text-blue-400',   bg: 'bg-blue-900/20'   },
  stale_flagged:{ Icon: Clock,       color: 'text-yellow-400', bg: 'bg-yellow-900/20' },
};

/**
 * ChangeLogItem — renders one change_log entry.
 *
 * @param {object}  log
 * @param {boolean} compact  Render a smaller inline variant
 */
export function ChangeLogItem({ log, compact = false }) {
  const { Icon, color, bg } =
    CHANGE_CONFIG[log.change_type] ?? CHANGE_CONFIG.updated;

  if (compact) {
    return (
      <div className={`flex items-start gap-2 p-2 rounded-lg ${bg} text-xs`}>
        <Icon className={`w-3.5 h-3.5 flex-shrink-0 mt-0.5 ${color}`} aria-hidden="true" />
        <div className="min-w-0">
          <span className={`font-medium ${color}`}>
            {formatChangeType(log.change_type)}:
          </span>
          <span className="text-slate-400 ml-1">
            {truncate(log.reason, 60)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border border-slate-700 ${bg}`}>
      <div className={`p-1.5 rounded-full ${bg}`}>
        <Icon className={`w-4 h-4 ${color}`} aria-hidden="true" />
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between gap-2">
          <span className={`text-sm font-semibold ${color}`}>
            {formatChangeType(log.change_type)}
          </span>
          <span className="text-xs text-slate-500">
            {timeAgo(log.changed_at)}
          </span>
        </div>
        {log.reason && (
          <p className="text-xs text-slate-300 leading-relaxed">{log.reason}</p>
        )}
      </div>
    </div>
  );
}
