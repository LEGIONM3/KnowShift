import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/knowshiftApi';

/**
 * useChangeLog — fetches paginated change-log entries for a domain.
 * Supports change_type filtering via setFilter().
 *
 * @param {string} domain  Active knowledge domain
 */
export function useChangeLog(domain) {
  const [logs,    setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [filter,  setFilter]  = useState(null);  // null = no type filter

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.getChangeLog(domain, 50, filter);
      setLogs(response.data?.changes ?? []);
    } catch (err) {
      setError(err.message || 'Failed to load change log');
    } finally {
      setLoading(false);
    }
  }, [domain, filter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return {
    logs,
    loading,
    error,
    filter,
    setFilter,
    refresh: fetchLogs,
  };
}
