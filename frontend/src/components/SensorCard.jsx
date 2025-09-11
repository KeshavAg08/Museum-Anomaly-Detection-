export default function SensorCard({ title, value, unit, healthy, icon }) {
  const getIcon = () => {
    switch (icon) {
      case 'temperature':
        return (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 2a3 3 0 00-3 3v6.5a4.5 4.5 0 109 0V5a3 3 0 00-3-3zm0 2a1 1 0 011 1v6.5a2.5 2.5 0 11-5 0V5a1 1 0 011-1z" clipRule="evenodd"/>
          </svg>
        )
      case 'humidity':
        return (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 6a3 3 0 013-3h10a1 1 0 01.8 1.6L14.25 8l2.55 3.4A1 1 0 0116 13H6a3 3 0 01-3-3V6z" clipRule="evenodd"/>
          </svg>
        )
      case 'vibration':
        return (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        )
      default:
        return (
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        )
    }
  }

  return (
    <div className={`relative overflow-hidden rounded-xl border backdrop-blur-sm transition-all duration-200 hover:scale-105 ${
      healthy 
        ? 'bg-slate-700/50 border-slate-600 hover:border-green-500' 
        : 'bg-red-900/20 border-red-700 hover:border-red-500'
    }`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-2 rounded-lg ${
            healthy ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {getIcon()}
          </div>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            healthy 
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-red-500/20 text-red-400 border border-red-500/30'
          }`}>
            {healthy ? 'Normal' : 'Alert'}
          </div>
        </div>
        
        <div className="text-slate-400 text-sm font-medium mb-2">{title}</div>
        <div className="text-white text-3xl font-bold mb-1">
          {value}<span className="text-lg text-slate-400 ml-1">{unit}</span>
        </div>
        
        {/* Animated pulse for anomalies */}
        {!healthy && (
          <div className="absolute inset-0 bg-red-500/5 animate-pulse pointer-events-none" />
        )}
        
        {/* Gradient overlay */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
      </div>
    </div>
  )
}

