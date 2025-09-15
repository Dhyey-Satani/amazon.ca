const JobTable = ({ jobs }) => {
  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const openJobLink = (url, jobTitle) => {
    // Check if this is a direct application link
    if (url.includes('application/start') || url.includes('apply') || url.includes('job-details')) {
      // Direct application link - open in same tab for better UX
      window.open(url, '_blank', 'noopener,noreferrer');
    } else {
      // Category page - open and provide guidance
      window.open(url, '_blank', 'noopener,noreferrer');
      
      // Show user guidance
      if (window.confirm(`Opening ${jobTitle} opportunities page. Once there, you can:

1. Enter your location/postal code
2. Select specific shifts and positions
3. Click "Apply Now" for individual positions

Would you like to continue?`)) {
        // User confirmed, link already opened above
        console.log('User proceeding to job application page');
      }
    }
  };

  if (!jobs || jobs.length === 0) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          💼 Job Listings
          <span className="ml-2 text-sm text-gray-500 font-normal">(0 jobs)</span>
        </h2>
        <div className="text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2h8zM8 14v.01M12 14v.01M16 14v.01" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No jobs found yet</h3>
          <p className="text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Start monitoring to begin detecting new job postings. Jobs will appear here as they are discovered.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        💼 Job Listings
        <span className="ml-2 text-sm text-gray-500 font-normal">({jobs.length} jobs)</span>
      </h2>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Job Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Posted Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Detected
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {jobs.map((job, index) => (
              <tr key={job.job_id || index} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {job.title}
                    </div>
                    {job.description && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate max-w-xs">
                        {job.description}
                      </div>
                    )}
                    {/* Show URL type indicator */}
                    {(job.url.includes('application/start') || job.url.includes('apply')) && (
                      <div className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Direct Application Link
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {job.location}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900 dark:text-gray-100">
                    {job.posted_date}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(job.detected_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => openJobLink(job.url, job.title)}
                    className="text-amazon-orange hover:text-orange-600 transition-colors duration-200 flex items-center"
                    title={job.url.includes('application/start') || job.url.includes('apply') ? 'Direct application link' : 'View job opportunities'}
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    {job.url.includes('application/start') || job.url.includes('apply') ? 'Apply Now' : 'View Jobs'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Job Stats */}
      <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>Total Jobs: {jobs.length}</span>
          <span>Latest: {jobs.length > 0 ? formatDate(jobs[0]?.detected_at) : 'None'}</span>
        </div>
      </div>
    </div>
  );
};

export default JobTable;