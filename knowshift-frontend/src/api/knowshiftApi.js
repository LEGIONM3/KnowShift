/**
 * KnowShift — Centralized Axios API Layer
 * All HTTP calls to the FastAPI backend originate from this module.
 * Uses an axios instance with interceptors for logging and error normalisation.
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 s — Gemini embedding can be slow
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — debug logging
apiClient.interceptors.request.use(
  (config) => {
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — normalise error messages
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'Unknown API error';
    console.error(`[API Error] ${message}`);
    return Promise.reject(new Error(message));
  },
);

// ---------------------------------------------------------------------------
// API surface
// ---------------------------------------------------------------------------
export const api = {
  // ── Health ────────────────────────────────────────────────────────────────
  health: () => apiClient.get('/health'),

  // ── Query ─────────────────────────────────────────────────────────────────
  /** Full RAG query with temporal reranking */
  ask: (question, domain, includeStale = false, topK = 10) =>
    apiClient.post('/query/ask', {
      question,
      domain,
      include_stale: includeStale,
      top_k: topK,
      return_sources: true,
    }),

  /** Side-by-side stale-vs-fresh comparison */
  compare: (question, domain) =>
    apiClient.get('/query/compare', { params: { question, domain } }),

  // ── Ingest ────────────────────────────────────────────────────────────────
  /** Upload PDF — uses multipart/form-data, 2-minute timeout */
  upload: (formData) =>
    apiClient.post('/ingest/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }),

  // ── Freshness ─────────────────────────────────────────────────────────────
  runStaleScan: () => apiClient.post('/freshness/scan'),

  getDashboard: (domain) => apiClient.get(`/freshness/dashboard/${domain}`),

  getChangeLog: (domain, limit = 50, changeType = null) =>
    apiClient.get(`/freshness/change-log/${domain}`, {
      params: { limit, ...(changeType ? { change_type: changeType } : {}) },
    }),

  getReindexCandidates: (domain) =>
    apiClient.get(`/freshness/reindex-candidates/${domain}`),

  triggerReindex: (documentId) =>
    apiClient.post(`/freshness/trigger-reindex/${documentId}`),
};

export default api;
