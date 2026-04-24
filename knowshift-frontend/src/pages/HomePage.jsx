import { useState } from 'react';
import { motion } from 'framer-motion';
import { DomainSelector }      from '../components/domain/DomainSelector';
import { QueryPanel }          from '../components/query/QueryPanel';
import { ChangeMap }           from '../components/changemap/ChangeMap';
import { FreshnessDashboard }  from '../components/dashboard/FreshnessDashboard';
import { UploadPanel }         from '../components/upload/UploadPanel';

/**
 * HomePage — full-page layout wiring all feature panels together.
 */
export function HomePage() {
  const [domain,     setDomain]     = useState('medical');
  // Increment to force FreshnessDashboard to remount after uploads / scans
  const [refreshKey, setRefreshKey] = useState(0);

  const bumpRefresh = () => setRefreshKey((k) => k + 1);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">

      {/* ── Hero ── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <p className="text-slate-300 text-lg font-medium">
          The RAG that knows when the world changed.
        </p>
        <p className="text-slate-500 text-sm max-w-2xl">
          KnowShift treats temporal validity as a first-class retrieval signal.
          It detects stale knowledge, repairs its own index, and delivers
          answers with explicit freshness transparency.
        </p>
      </motion.div>

      {/* ── Domain Selector ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <DomainSelector selected={domain} onSelect={setDomain} />
      </motion.div>

      {/* ── Main grid: 2/3 left  |  1/3 right ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Left column */}
        <motion.div
          className="xl:col-span-2 space-y-6"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <QueryPanel domain={domain} />
          <ChangeMap  domain={domain} />
        </motion.div>

        {/* Right sidebar */}
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <FreshnessDashboard
            key={refreshKey}
            domain={domain}
            onRefresh={bumpRefresh}
          />
          <UploadPanel
            domain={domain}
            onUploadComplete={bumpRefresh}
          />
        </motion.div>
      </div>

      {/* ── Footer ── */}
      <footer className="text-center text-slate-600 text-xs py-4
                         border-t border-slate-800">
        Built for AMD Developer Hackathon 2025 ·
        Powered by Gemini + Supabase pgvector ·
        KnowShift v1.0.0
      </footer>
    </main>
  );
}
