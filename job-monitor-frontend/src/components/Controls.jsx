import { useState } from 'react';

const Controls = ({ 
  isRunning, 
  onStart, 
  onStop, 
  onRestart, 
  onClearJobs, 
  pollInterval 
}) => {
  const [customInterval, setCustomInterval] = useState(pollInterval);
  const [loading, setLoading] = useState(false);

  const handleAction = async (action, ...args) => {
    setLoading(true);
    try {
      await action(...args);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        🎮 Bot Controls
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Start/Stop Controls */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Monitoring Control
          </label>
          <div className="flex space-x-2">
            {!isRunning ? (
              <button
                onClick={() => handleAction(onStart, customInterval)}
                disabled={loading}
                className="btn-primary flex-1 flex items-center justify-center"
              >
                {loading ? (
                  <svg className="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1M9 16h1m4 0h1m-6-8h6a2 2 0 012 2v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6a2 2 0 012-2z" />
                  </svg>
                )}
                Start
              </button>
            ) : (
              <button
                onClick={() => handleAction(onStop)}
                disabled={loading}
                className="btn-danger flex-1 flex items-center justify-center"
              >
                {loading ? (
                  <svg className="w-4 h-4 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                  </svg>
                )}
                Stop
              </button>
            )}
          </div>
        </div>

        {/* Restart Button */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Quick Actions
          </label>
          <button
            onClick={() => handleAction(onRestart)}
            disabled={loading}
            className="btn-secondary w-full flex items-center justify-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Restart
          </button>
        </div>

        {/* Poll Interval Setting */}
        <div className="space-y-2">
          <label htmlFor="pollInterval" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Poll Interval (seconds)
          </label>
          <input
            type="number"
            id="pollInterval"
            min="5"
            max="300"
            value={customInterval}
            onChange={(e) => setCustomInterval(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-amazon-orange focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>

        {/* Clear Jobs Button */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Data Management
          </label>
          <button
            onClick={() => {
              if (window.confirm('Are you sure you want to clear all jobs? This action cannot be undone.')) {
                handleAction(onClearJobs);
              }
            }}
            disabled={loading}
            className="btn-danger w-full flex items-center justify-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear Jobs
          </button>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Current Status:</span>
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className={`font-medium ${isRunning ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {isRunning ? 'Monitoring Active' : 'Monitoring Stopped'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Controls;