import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api';
import StatusCard from './StatusCard';
import Controls from './Controls';
import JobTable from './JobTable';
import LogsPanel from './LogsPanel';
import Header from './Header';

const Dashboard = ({ darkMode, onToggleDarkMode }) => {
  const [status, setStatus] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      const [statusRes, jobsRes, logsRes] = await Promise.all([
        apiClient.getStatus(),
        apiClient.getJobs(50),
        apiClient.getLogs(50)
      ]);

      setStatus(statusRes);
      setJobs(jobsRes.jobs || []);
      setLogs(logsRes.logs || []);
      setError(null);
    } catch (err) {
      setError(`Failed to fetch data: ${err.message}`);
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 2 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [fetchData, autoRefresh]);

  // Control actions
  const handleStartMonitoring = async (pollInterval) => {
    try {
      await apiClient.startMonitoring(pollInterval);
      await fetchData(); // Refresh data immediately
    } catch (err) {
      setError(`Failed to start monitoring: ${err.message}`);
    }
  };

  const handleStopMonitoring = async () => {
    try {
      await apiClient.stopMonitoring();
      await fetchData(); // Refresh data immediately
    } catch (err) {
      setError(`Failed to stop monitoring: ${err.message}`);
    }
  };

  const handleRestartMonitoring = async () => {
    try {
      await apiClient.restartMonitoring();
      await fetchData(); // Refresh data immediately
    } catch (err) {
      setError(`Failed to restart monitoring: ${err.message}`);
    }
  };

  const handleClearJobs = async () => {
    try {
      await apiClient.clearJobs();
      await fetchData(); // Refresh data immediately
    } catch (err) {
      setError(`Failed to clear jobs: ${err.message}`);
    }
  };

  const handleClearLogs = async () => {
    try {
      await apiClient.clearLogs();
      await fetchData(); // Refresh data immediately
    } catch (err) {
      setError(`Failed to clear logs: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-amazon-orange"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header 
        darkMode={darkMode} 
        onToggleDarkMode={onToggleDarkMode}
        autoRefresh={autoRefresh}
        onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6 animate-fade-in">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"></path>
              </svg>
              {error}
              <button 
                onClick={() => setError(null)}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title="Bot Status"
            value={status?.is_running ? 'Running' : 'Stopped'}
            subtitle={status?.last_check ? `Last check: ${new Date(status.last_check).toLocaleTimeString()}` : 'Never checked'}
            icon="🤖"
            status={status?.is_running ? 'running' : 'stopped'}
          />
          <StatusCard
            title="Total Jobs"
            value={status?.total_jobs || 0}
            subtitle={`Found this session: ${status?.stats?.new_jobs_this_session || 0}`}
            icon="💼"
            status="neutral"
          />
          <StatusCard
            title="Total Checks"
            value={status?.stats?.total_checks || 0}
            subtitle={`Errors: ${status?.stats?.errors || 0}`}
            icon="🔍"
            status="neutral"
          />
          <StatusCard
            title="Poll Interval"
            value={`${status?.config?.poll_interval || 30}s`}
            subtitle={`Selenium: ${status?.config?.use_selenium ? 'On' : 'Off'}`}
            icon="⏱️"
            status="neutral"
          />
        </div>

        {/* Controls */}
        <div className="mb-8">
          <Controls
            isRunning={status?.is_running || false}
            onStart={handleStartMonitoring}
            onStop={handleStopMonitoring}
            onRestart={handleRestartMonitoring}
            onClearJobs={handleClearJobs}
            pollInterval={status?.config?.poll_interval || 30}
          />
        </div>

        {/* Main Content Grid */}
        <div className="space-y-6">
          {/* Jobs Table - Full Width */}
          <div>
            <JobTable jobs={jobs} />
          </div>
          
          {/* Activity Log - Full Width Below Jobs */}
          <div>
            <LogsPanel logs={logs} onClearLogs={handleClearLogs} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;