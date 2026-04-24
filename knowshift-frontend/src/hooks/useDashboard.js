import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/knowshiftApi';

/**
 * useDashboard — fetches domain health metrics and exposes a stale-scan action.
 *
 * @param {string} domain  Active knowledge domain
 */
export function useDashboard(domain) {
  const [data,     setData]     = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);
  const [scanning, setScanning] = useState(false);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.getDashboard(domain);
      setData(response.data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [domain]);

  /** Trigger POST /freshness/scan then refresh */
  const runScan = useCallback(async () => {
    setScanning(true);
    try {
      await api.runStaleScan();
      await fetchDashboard();
    } catch (err) {
      setError(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  }, [fetchDashboard]);

  // Auto-fetch when domain changes
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    data,
    loading,
    error,
    scanning,
    refresh: fetchDashboard,
    runScan,
  };
}
