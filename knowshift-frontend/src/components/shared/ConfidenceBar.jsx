import { getFreshnessColors } from '../../utils/freshness';

/**
 * ConfidenceBar — animated horizontal progress bar for freshness confidence.
 *
 * @param {number} score  0.0 → 1.0
 * @param {string} label  Display label (default "Freshness Confidence")
 */
export function ConfidenceBar({ score, label = 'Freshness Confidence' }) {
  const colors     = getFreshnessColors(score);
  const percentage = Math.round(score * 100);

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-400">{label}</span>
        <span className={`font-bold ${colors.text}`}>{percentage}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 bg-slate-700 rounded-full overflow-hidden"
      >
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${percentage}%`, backgroundColor: colors.hex }}
        />
      </div>
    </div>
  );
}
