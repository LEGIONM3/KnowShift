/**
 * KnowShift — Freshness Utility Functions
 * Score → category, color, emoji, and label mapping.
 */

// ---------------------------------------------------------------------------
// Thresholds
// ---------------------------------------------------------------------------
export const FRESHNESS_THRESHOLDS = {
  FRESH: 0.7,
  AGING: 0.4,
  STALE: 0.0,
};

// ---------------------------------------------------------------------------
// Color maps (Tailwind classes + hex for Recharts)
// ---------------------------------------------------------------------------
export const FRESHNESS_COLORS = {
  fresh: {
    bg:     'bg-green-900/40',
    text:   'text-green-400',
    border: 'border-green-700',
    hex:    '#22c55e',
    panel:  'border-green-500 bg-green-950/30',
  },
  aging: {
    bg:     'bg-yellow-900/40',
    text:   'text-yellow-400',
    border: 'border-yellow-700',
    hex:    '#f59e0b',
    panel:  'border-yellow-500 bg-yellow-950/30',
  },
  stale: {
    bg:     'bg-red-900/40',
    text:   'text-red-400',
    border: 'border-red-700',
    hex:    '#ef4444',
    panel:  'border-red-500 bg-red-950/30',
  },
  deprecated: {
    bg:     'bg-slate-800',
    text:   'text-slate-400',
    border: 'border-slate-600',
    hex:    '#64748b',
    panel:  'border-slate-500 bg-slate-900/30',
  },
};

/**
 * Get freshness category string from a numeric score.
 * @param {number} score  0.0 → 1.0
 * @returns {'fresh' | 'aging' | 'stale'}
 */
export function getFreshnessCategory(score) {
  if (score >= FRESHNESS_THRESHOLDS.FRESH) return 'fresh';
  if (score >= FRESHNESS_THRESHOLDS.AGING) return 'aging';
  return 'stale';
}

/**
 * Get the color config object for a given score.
 * @param {number} score
 * @returns {object}
 */
export function getFreshnessColors(score) {
  return FRESHNESS_COLORS[getFreshnessCategory(score)];
}

/**
 * Get an emoji indicator for a freshness score.
 * @param {number} score
 * @returns {string}
 */
export function getFreshnessEmoji(score) {
  if (score >= FRESHNESS_THRESHOLDS.FRESH) return '✅';
  if (score >= FRESHNESS_THRESHOLDS.AGING) return '⏳';
  return '⚠️';
}

/**
 * Get a human-readable label for a freshness score.
 * @param {number} score
 * @returns {'Fresh' | 'Aging' | 'Stale'}
 */
export function getFreshnessLabel(score) {
  if (score >= FRESHNESS_THRESHOLDS.FRESH) return 'Fresh';
  if (score >= FRESHNESS_THRESHOLDS.AGING) return 'Aging';
  return 'Stale';
}

/**
 * Format a freshness score as a percentage string.
 * @param {number} score
 * @returns {string}  e.g. "87%"
 */
export function formatFreshnessPercent(score) {
  return `${Math.round(score * 100)}%`;
}

/**
 * Compute an overall health score (0-100) from dashboard summary data.
 * @param {{ fresh: number, total: number }|null} data
 * @returns {number}
 */
export function calculateHealthScore(data) {
  if (!data || data.total === 0) return 0;
  return Math.round((data.fresh / data.total) * 100);
}
