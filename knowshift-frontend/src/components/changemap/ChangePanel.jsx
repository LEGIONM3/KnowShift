import { FreshnessTag } from '../shared/FreshnessTag';
import { ConfidenceBar } from '../shared/ConfidenceBar';
import { truncate } from '../../utils/formatting';

const PANEL_STYLES = {
  fresh: {
    border: 'border-green-700/50',
    bg:     'bg-green-950/20',
    header: 'text-green-400',
  },
  stale: {
    border: 'border-red-700/50',
    bg:     'bg-red-950/20',
    header: 'text-red-400',
  },
};

/**
 * ChangePanel — one column in the 3-panel Change Map.
 *
 * @param {'fresh'|'stale'} type
 * @param {string}          title
 * @param {string}          answer
 * @param {number}          confidence   freshness_confidence score
 * @param {Array}           sources
 */
export function ChangePanel({ type, title, answer, confidence, sources }) {
  const styles = PANEL_STYLES[type] ?? PANEL_STYLES.fresh;

  return (
    <div className={`border-2 ${styles.border} ${styles.bg} rounded-xl p-4 space-y-3`}>
      <h3 className={`font-bold text-sm ${styles.header}`}>{title}</h3>

      {confidence != null && <FreshnessTag score={confidence} size="sm" />}

      {answer ? (
        <div className="space-y-3">
          <p className="text-xs text-slate-300 leading-relaxed">
            {truncate(answer, 250)}
          </p>

          {confidence != null && (
            <ConfidenceBar score={confidence} label="Index Freshness" />
          )}

          {sources?.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-slate-500 font-medium">Sources:</p>
              {sources.slice(0, 2).map((s, i) => (
                <div key={i} className="text-xs text-slate-400 flex items-center gap-1.5">
                  <span aria-hidden="true">•</span>
                  <span className="truncate">{s.source_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center py-6">
          <p className="text-slate-500 text-xs text-center">
            Run comparison to see answer
          </p>
        </div>
      )}
    </div>
  );
}
