import { useState, useCallback } from 'react';
import { api } from '../api/knowshiftApi';

/**
 * useQuery — manages RAG query state for a given domain.
 * Provides ask() and compare() actions with loading / error tracking.
 *
 * @param {string} domain  Active knowledge domain
 */
export function useQuery(domain) {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  /** Submit a single /query/ask call */
  const ask = useCallback(async (question, includeStale = false) => {
    if (!question.trim()) return null;

    setLoading(true);
    setError(null);

    try {
      const response = await api.ask(question, domain, includeStale);
      setResult(response.data);
      return response.data;
    } catch (err) {
      setError(err.message || 'Query failed. Please try again.');
      return null;
    } finally {
      setLoading(false);
    }
  }, [domain]);

  /** Submit a /query/compare call (stale vs fresh) */
  const compare = useCallback(async (question) => {
    if (!question.trim()) return null;

    setLoading(true);
    setError(null);

    try {
      const response = await api.compare(question, domain);
      return response.data;
    } catch (err) {
      setError(err.message || 'Comparison failed. Please try again.');
      return null;
    } finally {
      setLoading(false);
    }
  }, [domain]);

  /** Clear result and error */
  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, ask, compare, reset };
}
