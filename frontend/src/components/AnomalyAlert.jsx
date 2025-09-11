export default function AnomalyAlert({ issues }) {
  if (!issues || issues.length === 0) {
    return (
      <div className="p-4 rounded-lg border bg-green-900/20 border-green-700/50 backdrop-blur-sm">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-green-300 text-sm font-medium">All systems normal</span>
        </div>
        <p className="text-green-200/70 text-sm mt-2">No environmental anomalies detected</p>
      </div>
    )
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'text-red-300 border-red-500/50 bg-red-500/10'
      case 'medium':
        return 'text-yellow-300 border-yellow-500/50 bg-yellow-500/10'
      default:
        return 'text-orange-300 border-orange-500/50 bg-orange-500/10'
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return (
          <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
          </svg>
        )
      case 'medium':
        return (
          <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
          </svg>
        )
      default:
        return (
          <svg className="w-4 h-4 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
          </svg>
        )
    }
  }

  return (
    <div className="p-4 rounded-lg border bg-red-900/20 border-red-700/50 backdrop-blur-sm">
      <div className="flex items-center space-x-2 mb-4">
        <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse" />
        <span className="text-red-300 font-semibold">{issues.length} Anomal{issues.length > 1 ? 'ies' : 'y'} Detected</span>
      </div>
      
      <div className="space-y-3">
        {issues.map((issue, idx) => (
          <div key={idx} className={`p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}>
            <div className="flex items-start space-x-3">
              {getSeverityIcon(issue.severity)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="font-medium capitalize text-white">{issue.type}</span>
                  <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                    issue.severity === 'high' ? 'bg-red-500/20 text-red-300' :
                    issue.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-orange-500/20 text-orange-300'
                  }`}>
                    {issue.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-slate-300 text-sm">{issue.message}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

