/**
 * KnowShift — General Formatting Utilities
 */

/**
 * Format a datetime string (ISO) to a localised short date.
 * @param {string|null} dateStr
 * @returns {string}
 */
export function formatDate(dateStr) {
  if (!dateStr) return 'Unknown';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year:  'numeric',
      month: 'short',
      day:   'numeric',
    });
  } catch {
    return 'Unknown';
  }
}

/**
 * Return a human-readable relative time string.
 * @param {string|null} dateStr
 * @returns {string}  e.g. "3 months ago"
 */
export function timeAgo(dateStr) {
  if (!dateStr) return 'Unknown';
  try {
    const date     = new Date(dateStr);
    const now      = new Date();
    const diffDays = Math.floor((now - date) / 86_400_000);

    if (diffDays === 0)   return 'Today';
    if (diffDays === 1)   return 'Yesterday';
    if (diffDays < 30)    return `${diffDays} days ago`;
    if (diffDays < 365)   return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  } catch {
    return 'Unknown';
  }
}

/**
 * Truncate text to a maximum character length.
 * @param {string} text
 * @param {number} maxLength
 * @returns {string}
 */
export function truncate(text, maxLength = 120) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '…';
}

/**
 * Format a domain key to display label.
 * @param {string} domain
 * @returns {string}
 */
export function formatDomain(domain) {
  const labels = {
    medical:   'Medical',
    finance:   'Finance',
    ai_policy: 'AI Policy',
  };
  return labels[domain] ?? domain;
}

/**
 * Format a change_log change_type to human-readable label.
 * @param {string} changeType
 * @returns {string}
 */
export function formatChangeType(changeType) {
  const labels = {
    deprecated:   'Deprecated',
    updated:      'Updated',
    're-indexed': 'Re-indexed',
    stale_flagged:'Flagged Stale',
  };
  return labels[changeType] ?? changeType;
}

/**
 * Format a processing time in ms to a readable string.
 * @param {number} ms
 * @returns {string}
 */
export function formatProcessingTime(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
