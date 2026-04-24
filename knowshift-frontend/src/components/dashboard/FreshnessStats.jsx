/**
 * FreshnessStats — 2×2 grid of chunk count boxes per freshness category.
 *
 * @param {{ fresh, aging, stale, deprecated }} data
 */
export function FreshnessStats({ data }) {
  const stats = [
    { label: 'Fresh',      value: data.fresh,      color: 'text-green-400',  bg: 'bg-green-900/20 border-green-800'  },
    { label: 'Aging',      value: data.aging,      color: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-800'},
    { label: 'Stale',      value: data.stale,      color: 'text-red-400',    bg: 'bg-red-900/20 border-red-800'      },
    { label: 'Deprecated', value: data.deprecated, color: 'text-slate-400',  bg: 'bg-slate-800 border-slate-700'     },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`rounded-lg border p-3 text-center ${stat.bg}`}
        >
          <p className={`text-xl font-black ${stat.color}`}>{stat.value}</p>
          <p className="text-xs text-slate-500 mt-0.5">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
