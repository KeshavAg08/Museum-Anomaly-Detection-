export default function StatusIndicator({ status }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          bgColor: 'bg-green-500',
          textColor: 'text-green-100',
          borderColor: 'border-green-400',
          label: 'System Healthy',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
            </svg>
          )
        }
      case 'warning':
        return {
          bgColor: 'bg-yellow-500',
          textColor: 'text-yellow-100',
          borderColor: 'border-yellow-400',
          label: 'Anomaly Detected',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
            </svg>
          )
        }
      case 'critical':
        return {
          bgColor: 'bg-red-500',
          textColor: 'text-red-100',
          borderColor: 'border-red-400',
          label: 'Critical Alert',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
            </svg>
          )
        }
      default:
        return {
          bgColor: 'bg-gray-500',
          textColor: 'text-gray-100',
          borderColor: 'border-gray-400',
          label: 'Unknown',
          icon: (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"/>
            </svg>
          )
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-full border ${config.bgColor} ${config.borderColor} ${config.textColor}`}>
      <div className="flex items-center space-x-1">
        {config.icon}
        <span className="text-sm font-medium">{config.label}</span>
      </div>
    </div>
  )
}
