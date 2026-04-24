import {
  getFreshnessCategory,
  getFreshnessColors,
  getFreshnessEmoji,
  getFreshnessLabel,
  formatFreshnessPercent,
} from '../../utils/freshness';

/**
 * FreshnessTag — pill-shaped badge showing freshness category and score.
 *
 * @param {number}  score      0.0 → 1.0
 * @param {boolean} showScore  Include the percentage (default true)
 * @param {'sm'|'md'|'lg'} size
 */
export function FreshnessTag({ score, showScore = true, size = 'md' }) {
  const colors = getFreshnessColors(score);
  const emoji  = getFreshnessEmoji(score);
  const label  = getFreshnessLabel(score);

  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full font-semibold
        border ${colors.bg} ${colors.text} ${colors.border}
        ${sizes[size] ?? sizes.md}
      `}
    >
      <span aria-hidden="true">{emoji}</span>
      <span>{label}</span>
      {showScore && (
        <span className="opacity-80">({formatFreshnessPercent(score)})</span>
      )}
    </span>
  );
}
