/**
 * LoadingSpinner — animated spinner with optional text label.
 *
 * @param {'sm'|'md'|'lg'} size
 * @param {string|null}    label  Optional loading message
 */
export function LoadingSpinner({ size = 'md', label }) {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-[3px]',
  };

  return (
    <div
      role="status"
      aria-label={label ?? 'Loading…'}
      className="flex flex-col items-center justify-center gap-3"
    >
      <div
        className={`
          ${sizes[size] ?? sizes.md}
          border-slate-600 border-t-blue-500
          rounded-full animate-spin
        `}
      />
      {label && (
        <p className="text-slate-400 text-sm animate-pulse">{label}</p>
      )}
    </div>
  );
}
