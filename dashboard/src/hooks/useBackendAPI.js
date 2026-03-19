import { useState, useEffect, useCallback } from "react";

const API_BASE = "/insights";
const POLL_INTERVAL = 5000; // 5 seconds

export function useBackendAPI() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const id = setInterval(fetchDashboard, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchDashboard]);

  return { data, error, loading, refresh: fetchDashboard };
}
