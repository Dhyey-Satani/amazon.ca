const StatusCard = ({ title, value, subtitle, icon, status = 'neutral' }) => {
  const getStatusStyles = () => {
    switch (status) {
      case 'running':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'stopped':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800';
    }
  };

  const getValueColor = () => {
    switch (status) {
      case 'running':
        return 'text-green-600 dark:text-green-400';
      case 'stopped':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-gray-900 dark:text-gray-100';
    }
  };

  return (
    <div className={`rounded-lg border p-6 transition-all duration-200 hover:shadow-md ${getStatusStyles()}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
            {title}
          </p>
          <p className={`text-2xl font-bold mt-1 ${getValueColor()}`}>
            {value}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            {subtitle}
          </p>
        </div>
        <div className="text-2xl">{icon}</div>
      </div>
    </div>
  );
};

export default StatusCard;