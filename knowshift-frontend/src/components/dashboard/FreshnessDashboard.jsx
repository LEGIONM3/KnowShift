import { motion } from 'framer-motion';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Activity, RefreshCw } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
import { FreshnessStats } from './FreshnessStats';
import { LoadingSpinner } from '../layout/LoadingSpinner';
import { ErrorBanner } from '../shared/ErrorBanner';
import { calculateHealthScore } from '../../utils/freshness';

const PIE_COLORS = {
  Fresh:      '#22c55e',
  Aging:      '#f59e0b',
  Stale:      '#ef4444',
  Deprecated: '#64748b',
};

/** Custom Recharts tooltip rendered inside the dark UI */
const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm shadow-xl">
      <p className="font-semibold" style={{ color: item.payload.fill }}>
        {item.name}
      </p>
      <p className="text-slate-300">{item.value} chunks</p>
    </div>
  );
};

/**
 * FreshnessDashboard — donut chart + stats + scan button.
 *
 * @param {string}   domain
 * @param {Function} onRefresh  Optional callback after data refresh
 */
export function FreshnessDashboard({ domain, onRefresh }) {
  const { data, loading, error, scanning, refresh, runScan } = useDashboard(domain);

  const handleRefresh = async () => {
    await refresh();
    onRefresh?.();
  };

  const chartData = data
    ? [
        { name: 'Fresh',      value: data.fresh      },
        { name: 'Aging',      value: data.aging      },
        { name: 'Stale',      value: data.stale      },
        { name: 'Deprecated', value: data.deprecated },
      ].filter((d) => d.value > 0)
    : [];

  const healthScore = calculateHealthScore(data);

  return (
    <div className="card space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="section-title flex items-center gap-2 mb-0">
          <Activity className="w-5 h-5 text-green-400" aria-hidden="true" />
          Freshness Dashboard
        </h2>
        <button
          id="dashboard-refresh"
          onClick={handleRefresh}
          disabled={loading}
          title="Refresh data"
          aria-label="Refresh dashboard"
          className="p-2 text-slate-400 hover:text-slate-200
                     hover:bg-slate-700 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
        </button>
      </div>

      {/* Health score headline */}
      {data && (
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="flex items-center justify-center py-2"
        >
          <div className="text-center">
            <div
              className={`text-4xl font-black ${
                healthScore >= 70 ? 'text-green-400' :
                healthScore >= 40 ? 'text-yellow-400' :
                'text-red-400'
              }`}
            >
              {healthScore}%
            </div>
            <p className="text-slate-500 text-xs mt-1">Knowledge Health Score</p>
          </div>
        </motion.div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-8">
          <LoadingSpinner label="Loading dashboard…" />
        </div>
      )}

      {/* Error */}
      {error && <ErrorBanner message={error} />}

      {/* Donut chart */}
      {data && chartData.length > 0 && (
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={PIE_COLORS[entry.name]}
                  stroke="transparent"
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value) => (
                <span className="text-xs text-slate-300">{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      )}

      {/* Stats grid */}
      {data && <FreshnessStats data={data} />}

      {/* Scan button */}
      <button
        id="run-stale-scan"
        onClick={runScan}
        disabled={scanning}
        className="w-full btn-secondary flex items-center justify-center gap-2 text-sm"
      >
        <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} aria-hidden="true" />
        {scanning ? 'Scanning…' : 'Run Stale Scan'}
      </button>
    </div>
  );
}
