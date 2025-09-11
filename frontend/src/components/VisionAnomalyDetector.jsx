import { useState, useRef, useEffect } from 'react'
import { checkVisionAnomaly, getCameraStreamUrl } from '../api'

export default function VisionAnomalyDetector({ exhibitId = 'default' }) {
  const [isDetecting, setIsDetecting] = useState(false)
  const [visionResult, setVisionResult] = useState(null)
  const [lastCheck, setLastCheck] = useState(null)
  const [autoCapture, setAutoCapture] = useState(false)
  const canvasRef = useRef(null)
  const intervalRef = useRef(null)

  const streamUrl = getCameraStreamUrl(exhibitId)

  // Auto-capture every 5 seconds when enabled
  useEffect(() => {
    if (autoCapture) {
      intervalRef.current = setInterval(() => {
        captureAndAnalyze()
      }, 5000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoCapture])

  const captureFrameFromStream = () => {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.crossOrigin = 'anonymous'
      
      img.onload = () => {
        const canvas = canvasRef.current
        if (!canvas) {
          reject(new Error('Canvas not available'))
          return
        }

        const ctx = canvas.getContext('2d')
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob)
          } else {
            reject(new Error('Failed to create blob from canvas'))
          }
        }, 'image/jpeg', 0.8)
      }

      img.onerror = () => {
        reject(new Error('Failed to load image from stream'))
      }

      // Add timestamp to prevent caching
      img.src = `${streamUrl}?t=${Date.now()}`
    })
  }

  const captureAndAnalyze = async () => {
    if (isDetecting) return

    setIsDetecting(true)
    try {
      // Capture frame from camera stream
      const imageBlob = await captureFrameFromStream()
      
      // Send to vision API
      const result = await checkVisionAnomaly(imageBlob)
      
      setVisionResult(result)
      setLastCheck(new Date())
    } catch (error) {
      console.error('Vision detection error:', error)
      setVisionResult({
        detections: [],
        anomaly_detected: false,
        status: '❌ Detection Error',
        error: error.message
      })
      setLastCheck(new Date())
    } finally {
      setIsDetecting(false)
    }
  }

  const handleManualCapture = () => {
    captureAndAnalyze()
  }

  const toggleAutoCapture = () => {
    setAutoCapture(!autoCapture)
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6 shadow-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">Vision Anomaly Detection</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleAutoCapture}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              autoCapture 
                ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {autoCapture ? '🟢 Auto' : '⭕ Manual'}
          </button>
          <button
            onClick={handleManualCapture}
            disabled={isDetecting}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            {isDetecting ? '🔄 Analyzing...' : '📸 Capture & Analyze'}
          </button>
        </div>
      </div>

      {/* Camera Stream Preview */}
      <div className="mb-4">
        <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
          <img
            src={streamUrl}
            alt="Live camera feed"
            className="w-full h-full object-contain"
            onError={(e) => {
              e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIyNSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZDNkM2QzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkNhbWVyYSBOb3QgQXZhaWxhYmxlPC90ZXh0Pjwvc3ZnPg=='
            }}
          />
          
          {/* Overlay for detection status */}
          {visionResult && (
            <div className="absolute top-2 right-2 z-10">
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                visionResult.anomaly_detected 
                  ? 'bg-red-500 text-white' 
                  : 'bg-green-500 text-white'
              }`}>
                {visionResult.status}
              </div>
            </div>
          )}

          {/* Loading overlay */}
          {isDetecting && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-20">
              <div className="bg-white rounded-lg p-4 flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                <span className="text-sm font-medium">Analyzing image...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Detection Results */}
      {visionResult && (
        <div className="space-y-4">
          <div className={`p-4 rounded-lg border-l-4 ${
            visionResult.anomaly_detected 
              ? 'bg-red-50 border-red-500' 
              : 'bg-green-50 border-green-500'
          }`}>
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-lg">
                {visionResult.anomaly_detected ? '⚠️' : '✅'}
              </span>
              <span className="font-medium">
                {visionResult.status}
              </span>
            </div>
            
            {visionResult.error && (
              <p className="text-red-600 text-sm">
                Error: {visionResult.error}
              </p>
            )}
          </div>

          {/* Detections List */}
          {visionResult.detections && visionResult.detections.length > 0 && (
            <div className="bg-muted rounded-lg p-4">
              <h4 className="font-medium text-text-primary mb-3">
                Objects Detected ({visionResult.detections.length})
              </h4>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {visionResult.detections.map((detection, index) => (
                  <div 
                    key={index} 
                    className="flex items-center justify-between text-sm p-2 bg-card rounded border border-border"
                  >
                    <span className="capitalize font-medium">
                      {detection.label}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="text-text-secondary">
                        {Math.round(detection.confidence * 100)}%
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        detection.confidence > 0.8 
                          ? 'bg-green-100 text-green-800' 
                          : detection.confidence > 0.5 
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {detection.confidence > 0.8 ? 'High' : detection.confidence > 0.5 ? 'Medium' : 'Low'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last Check Info */}
          {lastCheck && (
            <div className="text-xs text-text-secondary text-center">
              Last checked: {lastCheck.toLocaleTimeString()}
              {autoCapture && <span className="ml-2">(Auto-checking every 5 seconds)</span>}
            </div>
          )}
        </div>
      )}

      {!visionResult && !isDetecting && (
        <div className="text-center text-text-secondary py-8">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p>Click "Capture & Analyze" to start vision anomaly detection</p>
          <p className="text-xs mt-1">Or enable auto-capture for continuous monitoring</p>
        </div>
      )}
    </div>
  )
}
