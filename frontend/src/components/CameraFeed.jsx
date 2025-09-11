export default function CameraFeed({ apiBase }) {
  const streamUrl = `${apiBase}/camera/stream`
  
  return (
    <div className="relative border border-slate-600 rounded-lg overflow-hidden bg-black backdrop-blur-sm">
      {/* Status indicator overlay */}
      <div className="absolute top-3 left-3 z-10">
        <div className="flex items-center space-x-2 bg-slate-900/80 backdrop-blur-sm rounded-full px-3 py-1 border border-slate-700">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-green-300 text-xs font-medium">LIVE</span>
        </div>
      </div>
      
      {/* Recording indicator */}
      <div className="absolute top-3 right-3 z-10">
        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
      </div>
      
      {/* Camera stream */}
      <div className="aspect-video bg-slate-900 flex items-center justify-center">
        <img 
          src={streamUrl} 
          alt="ESP32-CAM Stream" 
          className="w-full h-full object-contain"
          onError={(e) => {
            // Show placeholder on error
            e.target.style.display = 'none'
            e.target.nextSibling.style.display = 'flex'
          }}
        />
        
        {/* Placeholder when camera is unavailable */}
        <div className="hidden flex-col items-center justify-center text-slate-400 space-y-3">
          <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd"/>
          </svg>
          <div className="text-center">
            <p className="text-sm font-medium">Camera Offline</p>
            <p className="text-xs mt-1">Connect ESP32-CAM to view live feed</p>
          </div>
        </div>
      </div>
      
      {/* Bottom overlay with timestamp */}
      <div className="absolute bottom-3 left-3 right-3 z-10">
        <div className="bg-slate-900/80 backdrop-blur-sm rounded px-3 py-1 border border-slate-700">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-300">Gallery Monitor #1</span>
            <span className="text-slate-300 font-mono">
              {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

