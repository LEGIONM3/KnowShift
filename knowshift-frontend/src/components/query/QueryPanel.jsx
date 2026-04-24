import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Zap, Clock, AlertTriangle } from 'lucide-react';
import { useQuery } from '../../hooks/useQuery';
import { FreshnessTag } from '../shared/FreshnessTag';
import { ConfidenceBar } from '../shared/ConfidenceBar';
import { ErrorBanner } from '../shared/ErrorBanner';
import { LoadingSpinner } from '../layout/LoadingSpinner';
import { SourceCard } from './SourceCard';
import { formatProcessingTime } from '../../utils/formatting';

/** Sample demo questions per domain */
const DEMO_QUESTIONS = {
  medical:   'What is the first-line treatment for Type 2 Diabetes?',
  finance:   'What is the tax rate for income between Rs 10–12 lakhs?',
  ai_policy: 'What obligations do high-risk AI system providers have?',
};

/**
 * QueryPanel — main question-answer UI with fresh/stale mode toggle.
 *
 * @param {string} domain  Active knowledge domain
 */
export function QueryPanel({ domain }) {
  const [question, setQuestion] = useState('');
  const [mode,     setMode]     = useState('fresh'); // 'fresh' | 'stale'
  const { result, loading, error, ask, reset } = useQuery(domain);

  const handleAsk = async () => {
    if (!question.trim()) return;
    await ask(question, mode === 'stale');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) handleAsk();
  };

  return (
    <div className="card space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="section-title flex items-center gap-2 mb-0">
          <Search className="w-5 h-5 text-blue-400" aria-hidden="true" />
          Query Knowledge Base
        </h2>
        {result && (
          <button
            onClick={reset}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Demo hint */}
      <button
        onClick={() => setQuestion(DEMO_QUESTIONS[domain])}
        className="w-full text-left text-xs text-slate-500 hover:text-slate-400
                   transition-colors border border-dashed border-slate-700
                   rounded-lg p-3 hover:border-slate-600"
      >
        💡 Try: &ldquo;{DEMO_QUESTIONS[domain]}&rdquo;
      </button>

      {/* Textarea */}
      <textarea
        id="query-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about the selected domain…"
        aria-label="Query input"
        className="input-field resize-none h-24 text-sm"
      />

      {/* Mode toggle + submit */}
      <div className="flex gap-2">
        <div className="flex rounded-lg overflow-hidden border border-slate-700 flex-shrink-0">
          <button
            id="mode-fresh"
            onClick={() => setMode('fresh')}
            aria-pressed={mode === 'fresh'}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors
              ${mode === 'fresh'
                ? 'bg-green-700 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
          >
            <Zap className="w-3.5 h-3.5" aria-hidden="true" />
            Fresh Index
          </button>
          <button
            id="mode-stale"
            onClick={() => setMode('stale')}
            aria-pressed={mode === 'stale'}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors
              ${mode === 'stale'
                ? 'bg-red-700 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
          >
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            Include Stale
          </button>
        </div>

        <button
          id="query-submit"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          {loading ? <LoadingSpinner size="sm" /> : <Search className="w-4 h-4" aria-hidden="true" />}
          {loading ? 'Searching…' : 'Ask'}
        </button>
      </div>

      <p className="text-xs text-slate-600">Tip: Press Ctrl + Enter to submit</p>

      {/* Error */}
      {error && <ErrorBanner message={error} />}

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4 pt-2 border-t border-slate-700"
          >
            {/* Freshness badge + timing */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <FreshnessTag score={result.freshness_confidence} size="lg" />
              {result.processing_time_ms != null && (
                <span className="text-xs text-slate-500">
                  ⚡ {formatProcessingTime(result.processing_time_ms)}
                </span>
              )}
            </div>

            {/* Staleness warning */}
            {result.staleness_warning && (
              <div className="flex items-start gap-2 p-3 bg-yellow-950/50
                              border border-yellow-700 rounded-lg text-yellow-300 text-sm">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <p>
                  Some sources used in this answer may be outdated.
                  Consider uploading newer documents.
                </p>
              </div>
            )}

            {/* Confidence bar */}
            <ConfidenceBar score={result.freshness_confidence} />

            {/* Answer */}
            <div className="space-y-2">
              <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">
                Answer
              </p>
              <div className="bg-slate-800/50 rounded-lg p-4 text-sm text-slate-200
                              leading-relaxed whitespace-pre-wrap">
                {result.answer}
              </div>
            </div>

            {/* Sources */}
            {result.sources?.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">
                  Sources ({result.sources.length})
                </p>
                <div className="space-y-2">
                  {result.sources.map((src, i) => (
                    <SourceCard key={i} source={src} />
                  ))}
                </div>
              </div>
            )}

            {/* Ranking conflicts */}
            {result.ranking_conflicts?.length > 0 && (
              <div className="p-3 bg-orange-950/40 border border-orange-800
                              rounded-lg text-xs text-orange-300 space-y-1">
                <p className="font-semibold">⚡ Knowledge Conflicts Detected</p>
                {result.ranking_conflicts.map((c, i) => (
                  <p key={i} className="text-orange-400">{c.reason}</p>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
