import React, { useState, useEffect } from 'react';

const ExhibitMonitor = ({ exhibitId }) => {
  const [sensorData, setSensorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Make sure to set the correct API base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!exhibitId) {
      setError("No exhibit ID provided");
      setLoading(false);
      return;
    }

    const fetchExhibitData = async () => {
      try {
        setError(null); // Clear previous errors
        
        const response = await fetch(`${API_BASE_URL}/exhibits/${exhibitId}/monitor`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        
        const data = await response.json();
        setSensorData(data);
        
      } catch (err) {
        console.error('Fetch error:', err);
        setError(`Failed to fetch data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchExhibitData();
    
    // Set up interval for updates
    const interval = setInterval(fetchExhibitData, 2000);

    // Cleanup function
    return () => {
      clearInterval(interval);
    };
  }, [exhibitId, API_BASE_URL]); // Added API_BASE_URL to dependencies

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading exhibit data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-red-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="text-red-800 font-medium">Connection Error</p>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <p className="text-red-600 text-xs mt-2">
              Make sure your FastAPI server is running on {API_BASE_URL}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!sensorData) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800">No sensor data available for exhibit {exhibitId}</p>
      </div>
    );
  }

  const isRealData = sensorData?.sensor_data?.is_real_data;
  const dataSource = sensorData?.sensor_data?.data_source;

  return (
    <div className="space-y-6">
      {/* Data Source Indicator */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isRealData ? 'bg-green-500 animate-pulse' : 'bg-blue-500'
            }`}></div>
            <div>
              <p className="font-medium text-gray-900">
                {isRealData ? 'Live ESP32 Data' : 'Simulated Data'}
              </p>
              <p className="text-sm text-gray-600">
                Source: {dataSource} {isRealData && sensorData.sensor_data?.esp32_ip && `(ESP32: ${sensorData.sensor_data.esp32_ip})`}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Exhibit {exhibitId}</p>
            <p className="text-xs text-gray-500">
              Updated: {new Date(sensorData.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* Sensor Values Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Temperature */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-red-100 text-red-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div className="ml-4 flex-1">
              <p className="text-2xl font-bold text-gray-900">
                {sensorData.sensor_data?.temperature || 'N/A'}°C
              </p>
              <p className="text-gray-600">Temperature</p>
              <div className="mt-1 text-xs text-gray-500">
                Range: {sensorData.thresholds?.temperature?.min}°C - {sensorData.thresholds?.temperature?.max}°C
              </div>
            </div>
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.002 4.002 0 003 15z" />
              </svg>
            </div>
            <div className="ml-4 flex-1">
              <p className="text-2xl font-bold text-gray-900">
                {sensorData.sensor_data?.humidity || 'N/A'}%
              </p>
              <p className="text-gray-600">Humidity</p>
              <div className="mt-1 text-xs text-gray-500">
                Range: {sensorData.thresholds?.humidity?.min}% - {sensorData.thresholds?.humidity?.max}%
              </div>
            </div>
          </div>
        </div>

        {/* Vibration */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 text-yellow-600 rounded-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="ml-4 flex-1">
              <p className="text-2xl font-bold text-gray-900">
                {sensorData.sensor_data?.vibration || 'N/A'}
              </p>
              <p className="text-gray-600">Vibration</p>
              <div className="mt-1 text-xs text-gray-500">
                Max: {sensorData.thresholds?.vibration?.max}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Anomaly Status */}
      {sensorData.anomaly_status?.is_anomaly && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium text-red-800">Anomaly Detected!</p>
              <p className="text-red-700 text-sm mt-1">{sensorData.anomaly_status.explanation}</p>
              <p className="text-red-600 text-xs mt-1">
                Score: {(sensorData.anomaly_status.anomaly_score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Camera Feed */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Camera Feed {isRealData ? '(Live USB Camera)' : '(Placeholder)'}
          </h3>
          {exhibitId === 1 && (
            <div className="flex items-center text-sm text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
              Live Feed
            </div>
          )}
        </div>
        
        <div className="bg-black rounded-lg overflow-hidden" style={{aspectRatio: '4/3'}}>
          <img 
            src={`${API_BASE_URL}/camera/stream/${exhibitId}`}
            alt={`Camera feed for exhibit ${exhibitId}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
          <div 
            className="w-full h-full flex items-center justify-center text-white bg-gray-800" 
            style={{display: 'none'}}
          >
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
              <p className="text-sm">Camera feed unavailable</p>
            </div>
          </div>
        </div>
        
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
          <span>Exhibit {exhibitId} Camera</span>
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => window.open(`${API_BASE_URL}/camera/snapshot/${exhibitId}`, '_blank')}
              className="text-blue-600 hover:text-blue-800"
            >
              Take Snapshot
            </button>
            <span>Updated: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Raw Data Display (for debugging) */}
      <details className="bg-gray-50 rounded-lg p-4">
        <summary className="cursor-pointer font-medium text-gray-700 mb-2">
          Raw Sensor Data (Debug)
        </summary>
        <pre className="text-xs text-gray-600 bg-white p-3 rounded border overflow-x-auto">
          {JSON.stringify(sensorData, null, 2)}
        </pre>
      </details>
    </div>
  );
};

export default ExhibitMonitor;