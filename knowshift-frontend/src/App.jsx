import { Component } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header }   from './components/layout/Header';
import { HomePage } from './pages/HomePage';

// ---------------------------------------------------------------------------
// Error Boundary — catches render-phase errors and shows a recovery screen
// ---------------------------------------------------------------------------
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[KnowShift ErrorBoundary]', error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div className="min-h-screen bg-slate-950 flex items-center
                      justify-center px-6">
        <div className="max-w-md w-full bg-slate-900 border border-red-800
                        rounded-2xl p-8 text-center space-y-5">
          <div className="text-5xl" aria-hidden="true">⚠️</div>
          <h1 className="text-xl font-bold text-red-400">
            Something went wrong
          </h1>
          <p className="text-slate-400 text-sm">
            KnowShift encountered an unexpected error.
          </p>
          <pre className="text-xs text-red-300 bg-slate-800/60 rounded-lg
                          p-3 text-left overflow-auto max-h-40">
            {this.state.error?.message ?? 'Unknown error'}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary w-full"
          >
            Reload Application
          </button>
        </div>
      </div>
    );
  }
}


// ---------------------------------------------------------------------------
// App — root component
// ---------------------------------------------------------------------------
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-950">
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* Phase 4+: /admin, /settings */}
          </Routes>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
