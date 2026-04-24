import { useState } from 'react';
import { motion } from 'framer-motion';
import { GitCompare, ArrowRight, Loader2 } from 'lucide-react';
import { api } from '../../api/knowshiftApi';
import { ChangePanel } from './ChangePanel';
import { ChangeLogItem } from './ChangeLogItem';
import { ErrorBanner } from '../shared/ErrorBanner';
import { useChangeLog } from '../../hooks/useChangeLog';

const DEMO_QUESTIONS = {
  medical:   'What is the first-line treatment for Type 2 Diabetes?',
  finance:   'What is the tax rate for income between Rs 10–12 lakhs?',
  ai_policy: 'What obligations do high-risk AI system providers have?',
};

/**
 * ChangeMap — the signature KnowShift UI feature.
 * Shows a 3-panel layout: Stale answer | What changed | Fresh answer.
 *
 * @param {string} domain  Active knowledge domain
 */
export function ChangeMap({ domain }) {
  const [question,   setQuestion]   = useState('');
  const [comparison, setComparison] = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  const { logs } = useChangeLog(domain);

  const runComparison = async () => {
    const q = question.trim() || DEMO_QUESTIONS[domain];
    setLoading(true);
    setError(null);

    try {
      const response = await api.compare(q, domain);
      setComparison(response.data);
    } catch (err) {
      setError(err.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-center gap-2 flex-wrap">
        <GitCompare className="w-5 h-5 text-purple-400" aria-hidden="true" />
        <h2 className="section-title mb-0">Change Map</h2>
        <span className="text-xs bg-purple-900/40 text-purple-400
                         border border-purple-700 px-2 py-0.5 rounded-full">
          Signature Feature
        </span>
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <input
          id="changemap-input"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && runComparison()}
          placeholder={`Try: "${DEMO_QUESTIONS[domain]}"`}
          aria-label="Change map comparison question"
          className="input-field text-sm flex-1"
        />
        <button
          id="changemap-compare"
          onClick={runComparison}
          disabled={loading}
          className="btn-primary flex items-center gap-2 whitespace-nowrap"
        >
          {loading
            ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            : <GitCompare className="w-4 h-4" aria-hidden="true" />
          }
          Compare
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* ── 3-panel comparison ── */}
      {comparison && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Panel 1 — Stale */}
            <ChangePanel
              type="stale"
              title="⚠️ Old Answer (Stale Index)"
              answer={comparison.stale_answer?.answer}
              confidence={comparison.stale_answer?.freshness_confidence}
              sources={comparison.stale_answer?.sources}
            />

            {/* Panel 2 — What Changed */}
            <div className="border-2 border-yellow-700/50 bg-yellow-950/20
                            rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-yellow-400 font-bold text-sm">📋 What Changed</span>
                <ArrowRight className="w-3.5 h-3.5 text-yellow-600" aria-hidden="true" />
              </div>

              {comparison.difference_detected ? (
                <div className="space-y-2">
                  <p className="text-xs text-yellow-300 font-medium">
                    Knowledge updates detected:
                  </p>
                  {logs.slice(0, 5).map((log, i) => (
                    <ChangeLogItem key={i} log={log} compact />
                  ))}
                  {logs.length === 0 && (
                    <p className="text-xs text-yellow-600 italic">
                      Run a stale scan to see what changed
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-6 text-center">
                  <div className="space-y-1">
                    <p className="text-green-400 text-sm font-medium">✅ No differences detected</p>
                    <p className="text-slate-500 text-xs">Stale and fresh answers match</p>
                  </div>
                </div>
              )}
            </div>

            {/* Panel 3 — Fresh */}
            <ChangePanel
              type="fresh"
              title="✅ New Answer (Fresh Index)"
              answer={comparison.fresh_answer?.answer}
              confidence={comparison.fresh_answer?.freshness_confidence}
              sources={comparison.fresh_answer?.sources}
            />
          </div>

          {/* Difference indicator strip */}
          <div className={`text-center text-sm py-2 rounded-lg ${
            comparison.difference_detected
              ? 'bg-orange-950/40 text-orange-400 border border-orange-800'
              : 'bg-green-950/40 text-green-400 border border-green-800'
          }`}>
            {comparison.difference_detected
              ? '⚡ Knowledge difference detected! The self-healing index prevented outdated information.'
              : '✅ Both indexes returned consistent answers.'
            }
          </div>
        </motion.div>
      )}

      {/* Empty state */}
      {!comparison && !loading && (
        <div className="text-center py-8 text-slate-500 text-sm">
          <GitCompare className="w-10 h-10 mx-auto mb-3 opacity-30" aria-hidden="true" />
          <p>Run a comparison to see how KnowShift heals itself</p>
          <p className="text-xs mt-1 text-slate-600">
            Old (stale) answer vs New (fresh) answer — side by side
          </p>
        </div>
      )}
    </div>
  );
}
