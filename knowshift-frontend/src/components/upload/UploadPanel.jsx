import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, CheckCircle, AlertCircle, Zap } from 'lucide-react';
import { api } from '../../api/knowshiftApi';

/**
 * UploadPanel — drag-and-drop PDF ingestion with self-healing feedback.
 *
 * @param {string}   domain            Active knowledge domain
 * @param {Function} onUploadComplete  Called after a successful upload
 */
export function UploadPanel({ domain, onUploadComplete }) {
  const [file,       setFile]       = useState(null);
  const [sourceName, setSourceName] = useState('');
  const [sourceUrl,  setSourceUrl]  = useState('');
  const [status,     setStatus]     = useState('idle');   // idle | uploading | success | error
  const [result,     setResult]     = useState(null);
  const [error,      setError]      = useState(null);
  const [dragOver,   setDragOver]   = useState(false);
  const fileRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.type === 'application/pdf') setFile(dropped);
  };

  const handleUpload = async () => {
    if (!file || !sourceName.trim()) return;

    setStatus('uploading');
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append('file',        file);
      form.append('domain',      domain);
      form.append('source_name', sourceName);
      if (sourceUrl) form.append('source_url', sourceUrl);

      const response = await api.upload(form);
      setResult(response.data);
      setStatus('success');
      setFile(null);
      setSourceName('');
      setSourceUrl('');
      onUploadComplete?.();
    } catch (err) {
      setError(err.message || 'Upload failed');
      setStatus('error');
    }
  };

  const reset = () => {
    setStatus('idle');
    setResult(null);
    setError(null);
  };

  return (
    <div className="card space-y-4">
      <h2 className="section-title flex items-center gap-2 mb-0">
        <Upload className="w-5 h-5 text-indigo-400" aria-hidden="true" />
        Live Document Injection
      </h2>

      <p className="text-xs text-slate-500">
        Upload a PDF to trigger self-healing. KnowShift automatically
        deprecates overlapping stale chunks.
      </p>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop PDF here or click to browse"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && fileRef.current?.click()}
        className={`
          border-2 border-dashed rounded-xl p-6 text-center
          cursor-pointer transition-all duration-200
          ${dragOver
            ? 'border-blue-500 bg-blue-950/30'
            : file
            ? 'border-green-600 bg-green-950/20'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
          }
        `}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => setFile(e.target.files[0] ?? null)}
        />
        {file ? (
          <div className="flex items-center justify-center gap-2.5">
            <FileText className="w-5 h-5 text-green-400" aria-hidden="true" />
            <div className="text-left">
              <p className="text-sm font-medium text-green-300">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload className="w-7 h-7 mx-auto text-slate-500" aria-hidden="true" />
            <p className="text-sm text-slate-400">Drop PDF here or click to browse</p>
          </div>
        )}
      </div>

      {/* Metadata inputs */}
      <div className="space-y-2">
        <input
          id="source-name"
          type="text"
          value={sourceName}
          onChange={(e) => setSourceName(e.target.value)}
          placeholder="Source name (e.g. WHO 2025 Update) *"
          aria-label="Source name"
          className="input-field text-sm"
        />
        <input
          id="source-url"
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          placeholder="Source URL (optional)"
          aria-label="Source URL"
          className="input-field text-sm"
        />
      </div>

      {/* Upload button */}
      <button
        id="upload-submit"
        onClick={handleUpload}
        disabled={!file || !sourceName.trim() || status === 'uploading'}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {status === 'uploading' ? (
          <>
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Indexing PDF…
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" aria-hidden="true" />
            Upload &amp; Heal
          </>
        )}
      </button>

      {/* Status feedback */}
      <AnimatePresence>
        {status === 'success' && result && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-2 p-4 bg-green-950/40 border border-green-700 rounded-xl"
          >
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" aria-hidden="true" />
              <p className="text-sm font-semibold text-green-300">Upload successful!</p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-green-900/30 rounded-lg p-2 text-center">
                <p className="text-xl font-black text-green-400">{result.chunks_ingested}</p>
                <p className="text-green-600">Chunks indexed</p>
              </div>
              <div className="bg-orange-900/30 rounded-lg p-2 text-center">
                <p className="text-xl font-black text-orange-400">
                  {result.deprecated_old_chunks ?? 0}
                </p>
                <p className="text-orange-600">Chunks deprecated</p>
              </div>
            </div>
            {result.self_healing_triggered && (
              <p className="text-xs text-blue-300 flex items-center gap-1.5">
                <Zap className="w-3 h-3" aria-hidden="true" />
                Self-healing triggered! Stale knowledge removed.
              </p>
            )}
            <button onClick={reset} className="text-xs text-slate-500 hover:text-slate-400 transition-colors">
              Upload another
            </button>
          </motion.div>
        )}

        {status === 'error' && error && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-2 p-3 bg-red-950/40 border border-red-700 rounded-xl"
          >
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div className="space-y-1">
              <p className="text-sm text-red-300">{error}</p>
              <button onClick={reset} className="text-xs text-red-500 hover:text-red-400 transition-colors">
                Try again
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
