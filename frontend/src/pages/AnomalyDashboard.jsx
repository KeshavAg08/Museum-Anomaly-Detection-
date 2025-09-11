import React, { useState, useEffect, useCallback } from 'react'
import { Helmet } from 'react-helmet'
import Header from '../components/ui/Header'
import Button from '../components/ui/Button'
import { fetchSensors, checkAnomaly, chat } from '../api'

const AnomalyDashboard = () => {
  const [anomalies, setAnomalies] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(Date.now())
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)

  // Mock anomaly data
  const mockAnomalies = [
    {
      id: 'ANO-001',
      exhibitId: 'EXH-R001',
      exhibitName: 'Robotic Arm Demo',
      type: 'visual',
      severity: 'critical',
      dataValue: '15.2',
      unit: 'lux',
      timestamp: new Date(Date.now() - 300000)?.toISOString(),
      description: 'Lighting sensor detecting abnormal illumination levels'
    },
    {
      id: 'ANO-002',
      exhibitId: 'EXH-P003',
      exhibitName: 'Pendulum Physics',
      type: 'temperature',
      severity: 'high',
      dataValue: '28.5',
      unit: '°C',
      timestamp: new Date(Date.now() - 180000)?.toISOString(),
      description: 'Temperature sensor reading above normal operating range'
    },
    {
      id: 'ANO-003',
      exhibitId: 'EXH-B007',
      exhibitName: 'DNA Model Interactive',
      type: 'vibration',
      severity: 'medium',
      dataValue: '4.2',
      unit: 'Hz',
      timestamp: new Date(Date.now() - 120000)?.toISOString(),
      description: 'Unusual vibration patterns detected in motor assembly'
    }
  ]

  const fetchAnomalies = useCallback(async () => {
    setIsLoading(true)
    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const anomalyData = mockAnomalies?.map(anomaly => ({
        ...anomaly,
        timestamp: new Date(Date.now() - Math.random() * 600000)?.toISOString(),
        dataValue: (parseFloat(anomaly?.dataValue) + (Math.random() - 0.5) * 2)?.toFixed(1)
      }))
      
      setAnomalies(anomalyData)
      setLastRefresh(Date.now())
    } catch (error) {
      console.error('Failed to fetch anomalies:', error?.message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAnomalies()
    const interval = setInterval(fetchAnomalies, 10000)
    return () => clearInterval(interval)
  }, [fetchAnomalies])

  const getSummaryStats = () => {
    const stats = {
      visual: { count: 0, trend: 'down', trendValue: 12 },
      temperature: { count: 0, trend: 'up', trendValue: 8 },
      vibration: { count: 0, trend: 'down', trendValue: 5 }
    }
    
    anomalies?.forEach(anomaly => {
      if (stats?.[anomaly?.type]) {
        stats[anomaly.type].count++
      }
    })
    
    return stats
  }

  const summaryStats = getSummaryStats()

  const handleAcknowledge = (anomalyId) => {
    const anomaly = anomalies.find(a => a.id === anomalyId)
    if (anomaly && confirm(`Acknowledge anomaly for ${anomaly.exhibitName}?\n\nThis will mark the anomaly as resolved and remove it from the active list.`)) {
      setAnomalies(prev => prev?.filter(anomaly => anomaly?.id !== anomalyId))
    }
  }

  const handleViewDetails = (anomaly) => {
    setSelectedAnomaly(anomaly)
    setIsDetailsModalOpen(true)
  }

  const closeDetailsModal = () => {
    setIsDetailsModalOpen(false)
    setSelectedAnomaly(null)
    setIsChatOpen(false)
    setChatMessages([])
    setChatInput('')
  }

  const handleChatToggle = () => {
    setIsChatOpen(!isChatOpen)
    if (!isChatOpen && chatMessages.length === 0) {
      // Initialize chat with anomaly context
      const welcomeMessage = {
        type: 'assistant',
        content: `Hello! I'm here to help you with the ${selectedAnomaly?.type} anomaly detected at ${selectedAnomaly?.exhibitName}. What specific advice or solution do you need?`,
        timestamp: new Date().toISOString()
      }
      setChatMessages([welcomeMessage])
    }
  }

  const handleChatSend = async () => {
    if (!chatInput.trim() || isChatLoading) return

    const userMessage = {
      type: 'user',
      content: chatInput,
      timestamp: new Date().toISOString()
    }

    setChatMessages(prev => [...prev, userMessage])
    setChatInput('')
    setIsChatLoading(true)

    try {
      // Create context-aware message for the AI
      const contextMessage = `ANOMALY CONTEXT:
- Exhibit: ${selectedAnomaly?.exhibitName} (${selectedAnomaly?.exhibitId})
- Type: ${selectedAnomaly?.type}
- Severity: ${selectedAnomaly?.severity}
- Reading: ${selectedAnomaly?.dataValue} ${selectedAnomaly?.unit}
- Description: ${selectedAnomaly?.description}

STAFF QUESTION: ${chatInput}

Please provide specific, actionable advice for museum staff to address this anomaly. Focus on immediate steps, safety considerations, and preventive measures.`

      const response = await chat(contextMessage)
      
      const assistantMessage = {
        type: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString()
      }

      setChatMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = {
        type: 'assistant',
        content: 'I apologize, but I\'m having trouble connecting right now. Please try again or contact technical support for immediate assistance with this anomaly.',
        timestamp: new Date().toISOString()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleChatKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleChatSend()
    }
  }

  const SummaryCard = ({ title, count, type, trend, trendValue }) => (
    <div className="bg-card rounded-lg border border-border p-6 shadow-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-text-secondary">{title}</p>
          <p className="text-2xl font-bold text-text-primary">{count}</p>
        </div>
        <div className={`p-3 rounded-lg ${
          type === 'visual' ? 'bg-blue-100 text-blue-600' :
          type === 'temperature' ? 'bg-red-100 text-red-600' :
          'bg-yellow-100 text-yellow-600'
        }`}>
          {type === 'visual' && (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
            </svg>
          )}
          {type === 'temperature' && (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a3 3 0 00-3 3v6.5a4.5 4.5 0 109 0V5a3 3 0 00-3-3zm0 2a1 1 0 011 1v6.5a2.5 2.5 0 11-5 0V5a1 1 0 011-1z" clipRule="evenodd"/>
            </svg>
          )}
          {type === 'vibration' && (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          )}
        </div>
      </div>
      <div className={`flex items-center mt-4 text-sm ${
        trend === 'up' ? 'text-red-600' : 'text-green-600'
      }`}>
        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
          trend === 'up' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
        }`}>
          {trend === 'up' ? '↗' : '↘'} {trendValue}% vs last week
        </span>
      </div>
    </div>
  )

  const AnomalyTable = ({ anomalies, onAcknowledge, isLoading }) => {
    if (isLoading) {
      return (
        <div className="bg-card rounded-lg border border-border p-6 shadow-card">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-muted rounded w-1/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-muted rounded"></div>
              <div className="h-4 bg-muted rounded"></div>
              <div className="h-4 bg-muted rounded"></div>
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className="bg-card rounded-lg border border-border shadow-card">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">Recent Anomalies</h3>
          <p className="text-text-secondary text-sm">Monitor and manage exhibit anomalies</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Exhibit</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Severity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {anomalies.map((anomaly) => (
                <tr key={anomaly.id} className="hover:bg-muted/50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-text-primary">{anomaly.exhibitName}</div>
                      <div className="text-sm text-text-secondary">{anomaly.exhibitId}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      anomaly.type === 'visual' ? 'bg-blue-100 text-blue-800' :
                      anomaly.type === 'temperature' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {anomaly.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      anomaly.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      anomaly.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {anomaly.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                    {anomaly.dataValue} {anomaly.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                    {new Date(anomaly.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleAcknowledge(anomaly.id)}
                      className="text-primary hover:text-primary/80 transition-colors font-medium"
                    >
                      Acknowledge
                    </button>
                    <button 
                      onClick={() => handleViewDetails(anomaly)}
                      className="text-text-secondary hover:text-text-primary transition-colors font-medium px-2 py-1 rounded hover:bg-muted"
                      aria-label={`View details for ${anomaly.exhibitName} anomaly`}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <>
      <Helmet>
        <title>Anomaly Dashboard - Museum Monitoring System</title>
        <meta name="description" content="Real-time monitoring dashboard for museum exhibit anomalies and alerts" />
      </Helmet>
      <div className="min-h-screen bg-background">
        <Header />
        
        {/* Anomaly Details Modal */}
        {isDetailsModalOpen && selectedAnomaly && (
          <div className="fixed inset-0 z-1100 flex items-center justify-center p-4">
            <div 
              className="absolute inset-0 bg-black bg-opacity-50 cursor-pointer" 
              onClick={closeDetailsModal}
              aria-label="Close modal"
            ></div>
            <div className={`relative bg-card rounded-lg border border-border shadow-modal w-full z-1100 max-h-[90vh] overflow-y-auto ${
              isChatOpen ? 'max-w-4xl' : 'max-w-2xl'
            }`}>
              <div className={`${isChatOpen ? 'grid grid-cols-2 gap-6' : ''} p-6`}>
                <div className={isChatOpen ? '' : ''}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-text-primary">Anomaly Details</h3>
                    <div className="flex items-center space-x-2">
                      <button 
                        onClick={handleChatToggle}
                        className={`p-2 rounded-md transition-colors ${
                          isChatOpen 
                            ? 'bg-primary text-primary-foreground' 
                            : 'text-text-secondary hover:text-text-primary hover:bg-muted'
                        }`}
                        aria-label="Toggle chat assistant"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      </button>
                      <button 
                        onClick={closeDetailsModal} 
                        className="text-text-secondary hover:text-text-primary p-2 hover:bg-muted rounded-md transition-colors"
                        aria-label="Close anomaly details modal"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div><span className="font-medium text-text-secondary">Exhibit:</span><br/><span className="text-text-primary">{selectedAnomaly.exhibitName}</span></div>
                  <div><span className="font-medium text-text-secondary">Exhibit ID:</span><br/><span className="text-text-primary">{selectedAnomaly.exhibitId}</span></div>
                  <div><span className="font-medium text-text-secondary">Type:</span><br/><span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                    selectedAnomaly.type === 'visual' ? 'bg-blue-100 text-blue-800' :
                    selectedAnomaly.type === 'temperature' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>{selectedAnomaly.type.toUpperCase()}</span></div>
                  <div><span className="font-medium text-text-secondary">Severity:</span><br/><span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                    selectedAnomaly.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    selectedAnomaly.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>{selectedAnomaly.severity.toUpperCase()}</span></div>
                  <div><span className="font-medium text-text-secondary">Reading:</span><br/><span className="text-text-primary font-mono">{selectedAnomaly.dataValue} {selectedAnomaly.unit}</span></div>
                  <div><span className="font-medium text-text-secondary">Timestamp:</span><br/><span className="text-text-primary">{new Date(selectedAnomaly.timestamp).toLocaleString()}</span></div>
                </div>
                
                <div>
                  <span className="font-medium text-text-secondary">Description:</span>
                  <p className="text-text-primary mt-1 p-3 bg-muted rounded-lg">{selectedAnomaly.description}</p>
                </div>
                
                <div>
                  <span className="font-medium text-text-secondary">Recommended Actions:</span>
                  <ul className="text-text-primary mt-1 p-3 bg-muted rounded-lg text-sm space-y-1">
                    <li>• Inspect the exhibit immediately</li>
                    <li>• Check sensor calibration</li>
                    <li>• Document the incident</li>
                    <li>• Contact maintenance if needed</li>
                    {selectedAnomaly.severity === 'critical' && <li className="text-red-600 font-medium">• Consider temporary exhibit shutdown</li>}
                  </ul>
                </div>
              </div>
              
              {!isChatOpen && (
                <div className="mt-6 flex justify-end space-x-3">
                  <Button variant="outline" onClick={closeDetailsModal}>Close</Button>
                  <Button variant="default" onClick={() => {handleAcknowledge(selectedAnomaly.id); closeDetailsModal()}}>Acknowledge</Button>
                </div>
              )}
              </div>
              
              {/* Chat Interface */}
              {isChatOpen && (
                <div className="flex flex-col h-full">
                  <div className="flex items-center justify-between mb-4 pb-4 border-b border-border">
                    <h3 className="text-lg font-semibold text-text-primary flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                      AI Assistant
                    </h3>
                    <div className="text-xs text-text-secondary bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      Online
                    </div>
                  </div>
                  
                  {/* Chat Messages */}
                  <div className="flex-1 overflow-y-auto mb-4 max-h-64">
                    <div className="space-y-3">
                      {chatMessages.map((message, index) => (
                        <div key={index} className={`flex ${
                          message.type === 'user' ? 'justify-end' : 'justify-start'
                        }`}>
                          <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            message.type === 'user' 
                              ? 'bg-primary text-primary-foreground' 
                              : 'bg-muted text-text-primary'
                          }`}>
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p className={`text-xs mt-1 opacity-70`}>
                              {new Date(message.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))}
                      {isChatLoading && (
                        <div className="flex justify-start">
                          <div className="bg-muted text-text-primary px-4 py-2 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary"></div>
                              <span className="text-sm">AI is thinking...</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Chat Input */}
                  <div className="border-t border-border pt-4">
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={handleChatKeyPress}
                        placeholder="Ask for advice about this anomaly..."
                        className="flex-1 px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                        disabled={isChatLoading}
                      />
                      <Button 
                        onClick={handleChatSend}
                        disabled={!chatInput.trim() || isChatLoading}
                        size="sm"
                        className="px-3"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      </Button>
                    </div>
                    <p className="text-xs text-text-secondary mt-2">
                      Ask specific questions about handling this {selectedAnomaly?.severity} {selectedAnomaly?.type} anomaly
                    </p>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="mt-4 pt-4 border-t border-border flex justify-end space-x-3">
                    <Button variant="outline" onClick={closeDetailsModal}>Close</Button>
                    <Button variant="default" onClick={() => {handleAcknowledge(selectedAnomaly.id); closeDetailsModal()}}>Acknowledge</Button>
                  </div>
                </div>
              )}
              </div>
            </div>
          </div>
        )}
        
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Page Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-text-primary mb-2">
                Anomaly Dashboard
              </h1>
              <p className="text-text-secondary">
                Monitor real-time exhibit anomalies and respond to critical issues
              </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <SummaryCard
                title="Visual Anomalies"
                count={summaryStats?.visual?.count}
                type="visual"
                trend={summaryStats?.visual?.trend}
                trendValue={summaryStats?.visual?.trendValue}
              />
              <SummaryCard
                title="Temperature Anomalies"
                count={summaryStats?.temperature?.count}
                type="temperature"
                trend={summaryStats?.temperature?.trend}
                trendValue={summaryStats?.temperature?.trendValue}
              />
              <SummaryCard
                title="Vibration Anomalies"
                count={summaryStats?.vibration?.count}
                type="vibration"
                trend={summaryStats?.vibration?.trend}
                trendValue={summaryStats?.vibration?.trendValue}
              />
            </div>

            {/* Anomaly Table */}
            <AnomalyTable
              anomalies={anomalies}
              onAcknowledge={handleAcknowledge}
              isLoading={isLoading}
            />

            {/* Refresh indicator */}
            <div className="mt-6 text-center text-sm text-text-secondary">
              Last updated: {new Date(lastRefresh).toLocaleTimeString()}
            </div>
          </div>
        </main>
      </div>
    </>
  )
}

export default AnomalyDashboard
