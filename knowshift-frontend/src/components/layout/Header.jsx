import { useState, useEffect } from 'react';
import { Activity, Github } from 'lucide-react';
import { api } from '../../api/knowshiftApi';

/**
 * Header — sticky top bar with logo, API health indicator, and hackathon badge.
 */
export function Header() {
  const [serverStatus, setServerStatus] = useState('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.health();
        setServerStatus('online');
      } catch {
        setServerStatus('offline');
      }
    };

    checkHealth();
    // Poll every 30 seconds
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, []);

  const statusDot = {
    online:   'bg-green-400 animate-pulse',
    offline:  'bg-red-400',
    checking: 'bg-yellow-400 animate-pulse',
  }[serverStatus];

  return (
    <header className="border-b border-slate-800 bg-slate-900/50
                       backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4
                      flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Activity className="w-5 h-5 text-white" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white tracking-tight">
              KnowShift
            </h1>
            <p className="text-xs text-slate-500">Temporal Self-Healing RAG</p>
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-4">
          {/* API status indicator */}
          <div className="flex items-center gap-1.5 text-xs" aria-live="polite">
            <div className={`w-2 h-2 rounded-full ${statusDot}`} aria-hidden="true" />
            <span className="text-slate-400 hidden sm:inline">
              API {serverStatus}
            </span>
          </div>

          {/* Hackathon badge */}
          <span className="hidden sm:flex items-center gap-1.5 text-xs
                           bg-red-900/30 text-red-400 border border-red-800
                           px-3 py-1 rounded-full">
            🏆 AMD Hackathon 2025
          </span>

          {/* GitHub */}
          <a
            href="https://github.com/yourusername/knowshift"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View source on GitHub"
            className="p-2 text-slate-400 hover:text-slate-200
                       hover:bg-slate-700 rounded-lg transition-colors"
          >
            <Github className="w-4 h-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </header>
  );
}
