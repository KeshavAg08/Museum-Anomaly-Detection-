import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/ui/Header'
import Button from '../components/ui/Button'

const AddNewExhibit = () => {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    id: '',
    category: 'Interactive Technology',
    location: '',
    status: 'Active',
    maintenance: 'Monthly'
  })
  const [photo, setPhoto] = useState(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [recommendedSensors, setRecommendedSensors] = useState([])

  // Exhibit categories
  const exhibitCategories = [
    'Interactive Technology',
    'Robotics & Automation',
    'Natural History',
    'Art & Sculpture',
    'Historical Artifacts',
    'Science & Physics',
    'Biology & Life Sciences',
    'Geology & Minerals',
    'Cultural Heritage',
    'Digital Media',
    'Archaeological Finds',
    'Transportation',
    'Military History',
    'Textiles & Fashion',
    'Coins & Currency'
  ]

  // Available sensors for recommendations
  const availableSensors = [
    { id: 'camera', name: 'Camera (Visual Monitoring)', icon: '📹' },
    { id: 'vibration', name: 'Vibration/Accelerometer', icon: '📳' },
    { id: 'power', name: 'Current/Power Sensor', icon: '⚡' },
    { id: 'temperature', name: 'Temperature Sensor', icon: '🌡️' },
    { id: 'humidity', name: 'Humidity Sensor', icon: '💧' },
    { id: 'light', name: 'Light Sensor', icon: '💡' },
    { id: 'sound', name: 'Sound/Microphone Sensor', icon: '🎤' },
    { id: 'proximity', name: 'Proximity/Motion (PIR/Ultrasonic)', icon: '👋' },
    { id: 'magnetic', name: 'Magnetic/Reed Switch', icon: '🧲' },
    { id: 'strain', name: 'Strain Gauge', icon: '⚖️' }
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const analyzeExhibitPhoto = async (photo) => {
    if (!photo) return

    setIsAnalyzing(true)
    
    try {
      // Simulate AI analysis - in real implementation, this would call OpenAI Vision API
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Mock analysis based on common exhibit types
      const mockAnalysis = {
        artifactType: 'Interactive Digital Display',
        category: 'Interactive Technology',
        failureModes: [
          'Screen burn-in or pixel degradation',
          'Overheating of display components',
          'Touch interface malfunction',
          'Power supply failure',
          'Software crashes or freezing',
          'User tampering or vandalism'
        ],
        riskAssessment: 'Medium-High',
        recommendedSensors: ['camera', 'temperature', 'power', 'proximity', 'vibration'],
        maintenanceSchedule: 'Weekly',
        specialNotes: 'Interactive exhibits require frequent cleaning and software updates. Monitor for excessive heat buildup and user interaction patterns.'
      }
      
      setAnalysisResult(mockAnalysis)
      setRecommendedSensors(mockAnalysis.recommendedSensors)
      
      // Auto-fill form with analysis results
      setForm(prev => ({
        ...prev,
        category: mockAnalysis.category,
        maintenance: mockAnalysis.maintenanceSchedule
      }))
      
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleSubmit = async () => {
    if (!form.name || !form.id || !photo) return
    setIsSaving(true)
    await new Promise(r => setTimeout(r, 1500))
    navigate('/exhibit-management')
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="pt-16">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-text-primary">Add New Exhibit</h1>
                <p className="text-text-secondary mt-1">
                  Register a new exhibit in the monitoring system
                </p>
              </div>
              
              <Button
                variant="outline"
                iconName="ArrowLeft"
                iconPosition="left"
                onClick={() => navigate('/exhibit-management')}
              >
                Back to Management
              </Button>
            </div>
          </div>

          {/* Form */}
          <div className="space-y-6">
            <div className="bg-card rounded-lg border border-border p-6 shadow-card">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Exhibit Details</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Exhibit Name</label>
                  <input name="name" value={form.name} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2" placeholder="Holographic Projector" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Exhibit ID</label>
                  <input name="id" value={form.id} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2" placeholder="EXH-009" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                  <select name="category" value={form.category} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2">
                    {exhibitCategories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Location</label>
                  <input name="location" value={form.location} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2" placeholder="Robotics Hall - Section B" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Status</label>
                  <select name="status" value={form.status} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2">
                    <option>Active</option>
                    <option>Maintenance</option>
                    <option>Inactive</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Maintenance Schedule</label>
                  <select name="maintenance" value={form.maintenance} onChange={handleChange} className="w-full border border-border rounded-md px-3 py-2">
                    <option>Daily</option>
                    <option>Weekly</option>
                    <option>Bi-weekly</option>
                    <option>Monthly</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Photo Upload & AI Analysis */}
            <div className="bg-card rounded-lg border border-border p-6 shadow-card">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Exhibit Photo & AI Analysis</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <div className="w-full h-48 bg-muted rounded-lg border border-border flex items-center justify-center overflow-hidden mb-4">
                    {photo ? (
                      <img src={URL.createObjectURL(photo)} alt="Preview" className="w-full h-full object-cover" />
                    ) : (
                      <div className="text-center text-text-secondary">
                        <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                        </svg>
                        <span className="text-sm">Upload exhibit photo</span>
                      </div>
                    )}
                  </div>
                  <div className="space-y-3">
                    <label className="inline-flex items-center px-4 py-2 bg-muted hover:bg-muted/80 border border-border rounded-md cursor-pointer transition-colors">
                      <input type="file" accept="image/*" className="hidden" onChange={(e) => setPhoto(e.target.files[0])} />
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span>Upload Photo</span>
                    </label>
                    {photo && (
                      <Button 
                        variant="default" 
                        onClick={() => analyzeExhibitPhoto(photo)}
                        disabled={isAnalyzing}
                        loading={isAnalyzing}
                        className="w-full"
                      >
                        {isAnalyzing ? 'Analyzing Exhibit...' : '🤖 Analyze with AI'}
                      </Button>
                    )}
                    <p className="text-xs text-text-secondary">PNG or JPG up to 5MB. AI will analyze for optimal sensor recommendations.</p>
                  </div>
                </div>
                
                {/* Analysis Results */}
                <div className="space-y-4">
                  {isAnalyzing && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm font-medium text-blue-800">AI Analysis in Progress...</span>
                      </div>
                      <p className="text-xs text-blue-600">Identifying artifact type, failure modes, and sensor recommendations...</p>
                    </div>
                  )}
                  
                  {analysisResult && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-3 flex items-center">
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        AI Analysis Complete
                      </h4>
                      
                      <div className="space-y-3 text-sm">
                        <div>
                          <span className="font-medium text-green-700">Artifact Type:</span>
                          <span className="ml-2 text-green-600">{analysisResult.artifactType}</span>
                        </div>
                        
                        <div>
                          <span className="font-medium text-green-700">Risk Assessment:</span>
                          <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                            analysisResult.riskAssessment === 'High' ? 'bg-red-100 text-red-800' :
                            analysisResult.riskAssessment === 'Medium-High' ? 'bg-orange-100 text-orange-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {analysisResult.riskAssessment}
                          </span>
                        </div>
                        
                        <div>
                          <span className="font-medium text-green-700">Failure Modes:</span>
                          <ul className="ml-2 mt-1 text-green-600">
                            {analysisResult.failureModes.map((mode, idx) => (
                              <li key={idx} className="text-xs">• {mode}</li>
                            ))}
                          </ul>
                        </div>
                        
                        {analysisResult.specialNotes && (
                          <div>
                            <span className="font-medium text-green-700">Special Notes:</span>
                            <p className="ml-2 text-green-600 text-xs mt-1">{analysisResult.specialNotes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {!photo && !isAnalyzing && (
                    <div className="bg-muted rounded-lg p-4 text-center text-text-secondary">
                      <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      <p className="text-sm">Upload a photo to enable AI analysis</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Recommended Sensors */}
            {recommendedSensors.length > 0 && (
              <div className="bg-card rounded-lg border border-border p-6 shadow-card">
                <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                    <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
                  </svg>
                  Recommended Sensors
                </h3>
                <p className="text-text-secondary text-sm mb-4">Based on AI analysis, these sensors are recommended for optimal monitoring:</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {availableSensors
                    .filter(sensor => recommendedSensors.includes(sensor.id))
                    .map(sensor => (
                      <div key={sensor.id} className="flex items-center p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <span className="text-lg mr-3">{sensor.icon}</span>
                        <div>
                          <div className="text-sm font-medium text-blue-800">{sensor.name}</div>
                          <div className="text-xs text-blue-600">Recommended</div>
                        </div>
                        <div className="ml-auto">
                          <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    ))
                  }
                </div>
                
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 text-amber-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <h4 className="text-sm font-medium text-amber-800">Installation Note</h4>
                      <p className="text-xs text-amber-700 mt-1">These sensor recommendations are based on AI analysis of your exhibit photo. Actual sensor requirements may vary based on specific installation conditions and museum policies.</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="bg-card rounded-lg border border-border p-6 shadow-card">
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                <div>
                  <h3 className="font-semibold text-text-primary mb-1">Ready to Submit?</h3>
                  <p className="text-sm text-text-secondary">
                    {!form.name && !form.id && !photo && "Complete the form, upload a photo, and run AI analysis"}
                    {form.name && form.id && !photo && "Upload a photo to enable AI analysis"}
                    {form.name && form.id && photo && !analysisResult && "Run AI analysis for sensor recommendations"}
                    {form.name && form.id && photo && analysisResult && "All requirements met - ready to submit"}
                    {(!form.name || !form.id) && photo && "Complete the exhibit details form"}
                  </p>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                  <Button 
                    variant="outline" 
                    iconName="X" 
                    iconPosition="left" 
                    onClick={() => navigate('/exhibit-management')}
                    disabled={isSaving}
                  >
                    Cancel
                  </Button>
                  
                  <Button 
                    variant="default" 
                    iconName="Plus" 
                    iconPosition="left" 
                    loading={isSaving} 
                    disabled={!form.name || !form.id || !photo || isSaving} 
                    onClick={handleSubmit}
                    className="sm:min-w-[140px]"
                  >
                    {isSaving ? 'Adding Exhibit...' : 'Add Exhibit'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AddNewExhibit
