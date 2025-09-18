const LogsPanel = ({ logs, onClearLogs }) => {
  const getLogIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      case 'info':
        return 'ℹ️';
      case 'debug':
        return '🔍';
      default:
        return '📝';
    }
  };

  const getLogStyle = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return 'log-error';
      case 'warning':
        return 'log-warning';
      case 'success':
        return 'log-success';
      case 'info':
        return 'log-info';
      default:
        return 'log-info';
    }
  };

  const formatTime = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center">
          📜 Activity Logs
          <span className="ml-2 text-sm text-gray-500 font-normal">({logs?.length || 0} entries)</span>
        </h2>
        
        {/* Clear Logs Button */}
        {logs && logs.length > 0 && onClearLogs && (
          <button
            onClick={() => {
              if (window.confirm('Are you sure you want to clear all activity logs?')) {
                onClearLogs();
              }
            }}
            className="btn-secondary text-sm px-3 py-1 flex items-center space-x-1"
            title="Clear all activity logs"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1-1H8a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span>Clear Logs</span>
          </button>
        )}
      </div>
      
      <div className="h-64 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
        {!logs || logs.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-2">📝</div>
            <p className="text-gray-500 dark:text-gray-400">No logs available</p>
          </div>
        ) : (
          logs.slice().reverse().map((log, index) => (
            <div key={index} className={`${getLogStyle(log.level)} animate-fade-in`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-2 flex-1">
                  <span className="text-lg">{getLogIcon(log.level)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm break-words">{log.message}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs opacity-75">
                        {formatTime(log.timestamp)}
                      </span>
                      {log.logger && (
                        <>
                          <span className="text-xs opacity-50">•</span>
                          <span className="text-xs opacity-75">{log.logger}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Auto-scroll indicator */}
      {logs && logs.length > 0 && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          Latest logs appear at the top • {logs.length} total entries
        </div>
      )}
    </div>
  );
};

export default LogsPanel;