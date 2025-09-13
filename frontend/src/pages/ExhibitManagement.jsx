import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/ui/Header'
import Button from '../components/ui/Button'
import { getCameraStreamUrl } from '../api'

const ExhibitManagement = () => {
  const [exhibits, setExhibits] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedExhibit, setSelectedExhibit] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [editingExhibit, setEditingExhibit] = useState(null)
  const [editForm, setEditForm] = useState({})  
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [deletingExhibit, setDeletingExhibit] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState(null)

  // API Base URL - Update this to match your backend
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api'

  // Available exhibit categories
  const exhibitCategories = [
    'Robotics',
    'Physics',
    'Biology',
    'Chemistry',
    'Interactive Technology',
    'Natural History',
    'Art & Culture',
    'Historical Artifacts',
    'Space & Astronomy',
    'Digital Media'
  ]

  // Available status options
  const statusOptions = ['Active', 'Maintenance', 'Inactive']
  const maintenanceOptions = ['Daily', 'Weekly', 'Bi-weekly', 'Monthly', 'Quarterly']

  // API Functions
  const apiCall = async (url, options = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        const errorData = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorData || 'Request failed'}`)
      }

      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }
      return await response.text()
    } catch (error) {
      console.error('API call failed:', error)
      throw error
    }
  }

  const fetchExhibits = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiCall('/exhibits')
      
      // Transform the data to match your component's expected format
      const transformedExhibits = Array.isArray(data) ? data.map(exhibit => ({
        id: exhibit.id || exhibit._id,
        name: exhibit.name || '',
        category: exhibit.category || 'Robotics',
        status: exhibit.status || 'Active',
        lastAnomaly: exhibit.lastAnomaly || null,
        installationDate: exhibit.installationDate || '',
        location: exhibit.location || '',
        maintenanceSchedule: exhibit.maintenanceSchedule || 'Monthly',
        sensors: Array.isArray(exhibit.sensors) ? exhibit.sensors : []
      })) : []
      
      setExhibits(transformedExhibits)
    } catch (error) {
      console.error('Error fetching exhibits:', error)
      setError('Failed to load exhibits. Please check your connection and try again.')
      setExhibits([])
    } finally {
      setLoading(false)
    }
  }

  const updateExhibit = async (exhibitId, exhibitData) => {
    try {
      const response = await apiCall(`/exhibits/${exhibitId}`, {
        method: 'PUT',
        body: JSON.stringify(exhibitData),
      })
      return response
    } catch (error) {
      console.error('Error updating exhibit:', error)
      throw error
    }
  }

  const deleteExhibit = async (exhibitId) => {
    try {
      const response = await apiCall(`/exhibits/${exhibitId}`, {
        method: 'DELETE',
      })
      return response
    } catch (error) {
      console.error('Error deleting exhibit:', error)
      throw error
    }
  }

  // Load exhibits on component mount
  useEffect(() => {
    fetchExhibits()
  }, [])

  // Event Handlers
  const handleStatusChange = async (exhibitId, newStatus) => {
    try {
      const exhibit = exhibits.find(e => e.id === exhibitId)
      if (!exhibit) return

      const updatedExhibitData = { ...exhibit, status: newStatus }
      await updateExhibit(exhibitId, updatedExhibitData)
      
      // Update local state
      setExhibits(prevExhibits =>
        prevExhibits.map(exhibit =>
          exhibit.id === exhibitId
            ? { ...exhibit, status: newStatus }
            : exhibit
        )
      )
    } catch (error) {
      alert(`Failed to update exhibit status: ${error.message}`)
    }
  }

  const handleViewExhibit = (exhibit) => {
    setSelectedExhibit(exhibit)
    setIsModalOpen(true)
  }

  const handleEditExhibit = (exhibit) => {
    setEditingExhibit(exhibit)
    setEditForm({ ...exhibit })
    setIsEditModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setSelectedExhibit(null)
  }

  const closeEditModal = () => {
    setIsEditModalOpen(false)
    setEditingExhibit(null)
    setEditForm({})
    setIsSaving(false)
  }

  const handleEditFormChange = (e) => {
    const { name, value } = e.target
    setEditForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSaveExhibit = async () => {
    if (!editForm.name || !editForm.location) {
      alert('Please fill in all required fields')
      return
    }

    setIsSaving(true)
    
    try {
      // Make actual API call
      await updateExhibit(editingExhibit.id, editForm)
      
      // Update the exhibit in the local state
      setExhibits(prevExhibits =>
        prevExhibits.map(exhibit =>
          exhibit.id === editingExhibit.id
            ? { ...exhibit, ...editForm }
            : exhibit
        )
      )
      
      closeEditModal()
      
      // Show success message
      alert(`Successfully updated ${editForm.name}!`)
      
    } catch (error) {
      console.error('Failed to save exhibit:', error)
      alert(`Failed to save exhibit: ${error.message}`)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteExhibit = (exhibit) => {
    setDeletingExhibit(exhibit)
    setIsDeleteModalOpen(true)
  }

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false)
    setDeletingExhibit(null)
    setIsDeleting(false)
  }

  const confirmDeleteExhibit = async () => {
    if (!deletingExhibit) return

    setIsDeleting(true)
    
    try {
      // Make actual API call
      await deleteExhibit(deletingExhibit.id)
      
      // Remove the exhibit from the local state
      setExhibits(prevExhibits =>
        prevExhibits.filter(exhibit => exhibit.id !== deletingExhibit.id)
      )
      
      closeDeleteModal()
      
      // Show success message
      alert(`Successfully deleted ${deletingExhibit.name}!`)
      
    } catch (error) {
      console.error('Failed to delete exhibit:', error)
      alert(`Failed to delete exhibit: ${error.message}`)
    } finally {
      setIsDeleting(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active': return 'bg-green-100 text-green-800'
      case 'Maintenance': return 'bg-yellow-100 text-yellow-800'
      case 'Inactive': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const ExhibitSummaryCards = ({ exhibits }) => {
    const stats = {
      total: exhibits.length,
      active: exhibits.filter(e => e.status === 'Active').length,
      maintenance: exhibits.filter(e => e.status === 'Maintenance').length,
      inactive: exhibits.filter(e => e.status === 'Inactive').length
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-card rounded-lg border border-border p-6 shadow-card">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-text-primary">{stats.total}</p>
              <p className="text-text-secondary">Total Exhibits</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg border border-border p-6 shadow-card">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 text-green-600 rounded-lg">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-text-primary">{stats.active}</p>
              <p className="text-text-secondary">Active</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg border border-border p-6 shadow-card">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 text-yellow-600 rounded-lg">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-text-primary">{stats.maintenance}</p>
              <p className="text-text-secondary">Maintenance</p>
            </div>
          </div>
        </div>
        <div className="bg-card rounded-lg border border-border p-6 shadow-card">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 text-red-600 rounded-lg">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-text-primary">{stats.inactive}</p>
              <p className="text-text-secondary">Inactive</p>
            </div>
          </div>
        </div>
      </div>
    )
  }
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="pt-16">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-text-secondary">Loading exhibits...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="pt-16">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="text-red-600 mb-4">
                <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-text-primary font-medium mb-2">Unable to load exhibits</p>
              <p className="text-text-secondary mb-4">{error}</p>
              <Button onClick={fetchExhibits} variant="outline">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Exhibit Details Modal */}
      {isModalOpen && selectedExhibit && (
        <div className="fixed inset-0 z-1100 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={closeModal}></div>
          <div className="relative bg-card rounded-lg border border-border shadow-modal w-full max-w-4xl max-h-[90vh] overflow-y-auto z-1100">
            <div className="sticky top-0 bg-card rounded-t-lg px-6 py-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-text-primary">{selectedExhibit.name}</h3>
                  <p className="text-text-secondary text-sm">{selectedExhibit.id}</p>
                </div>
                <button 
                  onClick={closeModal} 
                  className="text-text-secondary hover:text-text-primary transition-colors p-2 hover:bg-muted rounded-md"
                  aria-label="Close modal"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Status Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-muted rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className={`w-3 h-3 rounded-full ${
                      selectedExhibit.status === 'Active' ? 'bg-green-500' :
                      selectedExhibit.status === 'Maintenance' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}></div>
                    <span className="text-sm font-medium text-text-secondary">Status</span>
                  </div>
                  <p className="text-lg font-semibold text-text-primary">{selectedExhibit.status}</p>
                </div>
                
                <div className="bg-muted rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="w-4 h-4 text-text-secondary" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-text-secondary">Location</span>
                  </div>
                  <p className="text-sm font-medium text-text-primary">{selectedExhibit.location}</p>
                </div>
                
                <div className="bg-muted rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <svg className="w-4 h-4 text-text-secondary" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium text-text-secondary">Maintenance</span>
                  </div>
                  <p className="text-sm font-medium text-text-primary">{selectedExhibit.maintenanceSchedule}</p>
                </div>
              </div>
              
              {/* Camera Feed */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-text-primary mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Live Camera Feed
                </h4>
                <div className="bg-black rounded-lg overflow-hidden" style={{aspectRatio: '16/9'}}>
                  <img 
                    src={getCameraStreamUrl(selectedExhibit.id)}
                    alt={`Live feed for ${selectedExhibit.name}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      if (e.target.nextSibling) {
                        e.target.nextSibling.style.display = 'flex'
                      }
                    }}
                  />
                  <div 
                    className="w-full h-full flex items-center justify-center text-white" 
                    style={{display: 'none'}}
                  >
                    <div className="text-center">
                      <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                      </svg>
                      <p className="text-sm">Camera feed unavailable</p>
                      <p className="text-xs opacity-75 mt-1">Check camera connection</p>
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-text-secondary">
                  <span>Camera ID: {selectedExhibit.id}-CAM</span>
                  <div className="flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                    <span>Live</span>
                  </div>
                </div>
              </div>
              
              {/* Exhibit Information */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-text-primary mb-3">Exhibit Information</h4>
                  <div className="space-y-3">
                    <div className="flex items-start justify-between py-2 border-b border-border">
                      <span className="font-medium text-text-secondary">Category</span>
                      <span className="text-text-primary bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                        {selectedExhibit.category}
                      </span>
                    </div>
                    <div className="flex items-start justify-between py-2 border-b border-border">
                      <span className="font-medium text-text-secondary">Installation Date</span>
                      <span className="text-text-primary">{selectedExhibit.installationDate}</span>
                    </div>
                    <div className="flex items-start justify-between py-2 border-b border-border">
                      <span className="font-medium text-text-secondary">Last Anomaly</span>
                      <span className={`text-sm ${
                        selectedExhibit.lastAnomaly 
                          ? 'text-orange-600 font-medium' 
                          : 'text-green-600 font-medium'
                      }`}>
                        {selectedExhibit.lastAnomaly 
                          ? new Date(selectedExhibit.lastAnomaly).toLocaleString() 
                          : 'No anomalies detected'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold text-text-primary mb-3">Sensor Configuration</h4>
                  <div className="space-y-2">
                    {selectedExhibit.sensors && selectedExhibit.sensors.length > 0 ? (
                      selectedExhibit.sensors.map((sensor, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full bg-green-500`}></div>
                            <div>
                              <p className="font-medium text-text-primary text-sm">{sensor.type}</p>
                              <p className="text-text-secondary text-xs">{sensor.model}</p>
                            </div>
                          </div>
                          <div className="text-green-600 text-xs font-medium bg-green-100 px-2 py-1 rounded-full">
                            Active
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center text-text-secondary py-8">
                        <svg className="w-8 h-8 mx-auto mb-2 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                        </svg>
                        <p className="text-sm">No sensors configured</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-border">
                <Button 
                  variant="outline" 
                  onClick={closeModal}
                  className="flex-1 sm:flex-none"
                >
                  Close
                </Button>
                <Button 
                  variant="default" 
                  onClick={() => {
                    closeModal()
                    handleEditExhibit(selectedExhibit)
                  }}
                  className="flex-1 sm:flex-none"
                >
                  Edit Exhibit
                </Button>
                <Button 
                  variant="secondary" 
                  onClick={() => {
                    handleStatusChange(
                      selectedExhibit.id, 
                      selectedExhibit.status === 'Active' ? 'Maintenance' : 'Active'
                    )
                    closeModal()
                  }}
                  className="flex-1 sm:flex-none"
                >
                  {selectedExhibit.status === 'Active' ? 'Set to Maintenance' : 'Set to Active'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Edit Exhibit Modal */}
      {isEditModalOpen && editingExhibit && (
        <div className="fixed inset-0 z-1100 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={!isSaving ? closeEditModal : undefined}></div>
          <div className="relative bg-card rounded-lg border border-border shadow-modal w-full max-w-3xl max-h-[90vh] overflow-y-auto z-1100">
            <div className="sticky top-0 bg-card rounded-t-lg px-6 py-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-text-primary">Edit Exhibit</h3>
                  <p className="text-text-secondary text-sm">{editingExhibit.id}</p>
                </div>
                <button 
                  onClick={closeEditModal} 
                  className="text-text-secondary hover:text-text-primary transition-colors p-2 hover:bg-muted rounded-md"
                  aria-label="Close edit modal"
                  disabled={isSaving}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleSaveExhibit(); }}>
                {/* Basic Information */}
                <div>
                  <h4 className="text-lg font-semibold text-text-primary mb-4">Basic Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Exhibit Name *</label>
                      <input
                        type="text"
                        name="name"
                        value={editForm.name || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder="Enter exhibit name"
                        disabled={isSaving}
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Category</label>
                      <select
                        name="category"
                        value={editForm.category || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        disabled={isSaving}
                      >
                        {exhibitCategories.map(category => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Status</label>
                      <select
                        name="status"
                        value={editForm.status || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        disabled={isSaving}
                      >
                        {statusOptions.map(status => (
                          <option key={status} value={status}>{status}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Maintenance Schedule</label>
                      <select
                        name="maintenanceSchedule"
                        value={editForm.maintenanceSchedule || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        disabled={isSaving}
                      >
                        {maintenanceOptions.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
                
                {/* Location Information */}
                <div>
                  <h4 className="text-lg font-semibold text-text-primary mb-4">Location & Installation</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Location *</label>
                      <input
                        type="text"
                        name="location"
                        value={editForm.location || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder="Enter exhibit location"
                        disabled={isSaving}
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-text-secondary mb-2">Installation Date</label>
                      <input
                        type="text"
                        name="installationDate"
                        value={editForm.installationDate || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        placeholder="e.g., March 15, 2024"
                        disabled={isSaving}
                      />
                    </div>
                  </div>
                </div>
                
                {/* Current Sensors Display (Read-only) */}
                <div>
                  <h4 className="text-lg font-semibold text-text-primary mb-4">Current Sensors</h4>
                  <div className="bg-muted rounded-lg p-4">
                    {editingExhibit.sensors && editingExhibit.sensors.length > 0 ? (
                      <div className="space-y-2">
                        {editingExhibit.sensors.map((sensor, index) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-card rounded border">
                            <div>
                              <span className="font-medium text-text-primary text-sm">{sensor.type}</span>
                              <span className="text-text-secondary text-xs ml-2">({sensor.model})</span>
                            </div>
                            <span className="text-green-600 text-xs bg-green-100 px-2 py-1 rounded-full">
                              Active
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-text-secondary text-sm text-center py-4">No sensors configured</p>
                    )}
                    <p className="text-text-secondary text-xs mt-3">
                      Note: Sensor configuration requires technical support. Contact IT to modify sensors.
                    </p>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-border">
                  <Button 
                    type="button"
                    variant="outline" 
                    onClick={closeEditModal}
                    disabled={isSaving}
                    className="flex-1 sm:flex-none"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit"
                    variant="default" 
                    disabled={isSaving || !editForm.name || !editForm.location}
                    loading={isSaving}
                    className="flex-1 sm:flex-none"
                  >
                    {isSaving ? 'Saving Changes...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {isDeleteModalOpen && deletingExhibit && (
        <div className="fixed inset-0 z-1100 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={!isDeleting ? closeDeleteModal : undefined}></div>
          <div className="relative bg-card rounded-lg border border-border shadow-modal w-full max-w-md z-1100">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-text-primary">Delete Exhibit</h3>
                  <p className="text-text-secondary text-sm mt-1">This action cannot be undone</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-text-primary">
                  Are you sure you want to delete <strong>{deletingExhibit.name}</strong>?
                </p>
                <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="text-sm text-red-800">
                    <p className="font-medium mb-1">This will permanently remove:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>All exhibit information and history</li>
                      <li>Sensor configurations and data</li>
                      <li>Associated anomaly records</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-3">
                <Button 
                  variant="outline" 
                  onClick={closeDeleteModal}
                  disabled={isDeleting}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button 
                  variant="destructive" 
                  onClick={confirmDeleteExhibit}
                  disabled={isDeleting}
                  loading={isDeleting}
                  className="flex-1"
                >
                  {isDeleting ? 'Deleting...' : 'Delete Exhibit'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="pt-16">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-text-primary mb-2">Exhibit Management</h1>
              <p className="text-text-secondary">
                Monitor and manage all museum exhibits and their operational status
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <Link to="/add-new-exhibit">
                <Button variant="default" iconName="Plus" iconPosition="left">
                  Add New Exhibit
                </Button>
              </Link>
            </div>
          </div>

          {/* Summary Cards */}
          <ExhibitSummaryCards exhibits={exhibits} />

          {/* Exhibits Table */}
          <div className="bg-card rounded-lg border border-border shadow-card">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Exhibits</h3>
              <p className="text-text-secondary text-sm">Manage your museum exhibits</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Location</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Last Anomaly</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-card divide-y divide-border">
                  {exhibits.length > 0 ? exhibits.map((exhibit) => (
                    <tr key={exhibit.id} className="hover:bg-muted/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-text-primary">{exhibit.name}</div>
                          <div className="text-sm text-text-secondary">{exhibit.id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {exhibit.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(exhibit.status)}`}>
                          {exhibit.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                        {exhibit.location}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                        {exhibit.lastAnomaly ? new Date(exhibit.lastAnomaly).toLocaleString() : 'None'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button 
                          onClick={() => handleViewExhibit(exhibit)}
                          className="text-primary hover:text-primary/80 transition-colors"
                        >
                          View
                        </button>
                        <button 
                          onClick={() => handleEditExhibit(exhibit)}
                          className="text-text-secondary hover:text-text-primary transition-colors"
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => handleDeleteExhibit(exhibit)}
                          className="text-red-600 hover:text-red-800 transition-colors font-medium"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center">
                        <div className="text-center">
                          <svg className="w-12 h-12 mx-auto text-text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                          </svg>
                          <h3 className="text-lg font-medium text-text-primary mb-2">No exhibits found</h3>
                          <p className="text-text-secondary mb-4">Get started by adding your first exhibit to the system.</p>
                          <Link to="/add-new-exhibit">
                            <Button variant="default">Add New Exhibit</Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExhibitManagement