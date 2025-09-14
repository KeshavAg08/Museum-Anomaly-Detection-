import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Header from '../components/ui/Header';
import Button from '../components/ui/Button';

const ExhibitManagement = () => {
  const navigate = useNavigate();
  const [exhibits, setExhibits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState({});
  const [selectedExhibit, setSelectedExhibit] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [editLoading, setEditLoading] = useState(false);

  // API Base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Fetch all exhibits from backend
  const fetchExhibits = async () => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/exhibits`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setExhibits(data.exhibits || []);
      
    } catch (err) {
      console.error('Fetch exhibits error:', err);
      setError(`Failed to fetch exhibits: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Update exhibit function
  const updateExhibit = async (exhibitId, updateData) => {
    try {
      setEditLoading(true);
      
      const response = await fetch(`${API_BASE_URL}/exhibits/${exhibitId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const updatedExhibit = await response.json();
      
      // Update the exhibit in local state
      setExhibits(prev => prev.map(exhibit => 
        exhibit.id === exhibitId ? updatedExhibit : exhibit
      ));
      
      alert('Exhibit updated successfully!');
      setShowEditModal(false);
      setSelectedExhibit(null);
      setEditForm({});
      
    } catch (err) {
      console.error('Update exhibit error:', err);
      alert(`Failed to update exhibit: ${err.message}`);
    } finally {
      setEditLoading(false);
    }
  };

  // Delete exhibit function
  const deleteExhibit = async (exhibitId) => {
    try {
      setDeleteLoading(prev => ({ ...prev, [exhibitId]: true }));
      
      const response = await fetch(`${API_BASE_URL}/exhibits/${exhibitId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
      }
      
      const result = await response.json();
      
      // Remove the exhibit from the local state
      setExhibits(prev => prev.filter(exhibit => exhibit.id !== exhibitId));
      
      // Show success message
      alert(`Successfully deleted: ${result.message}`);
      
    } catch (err) {
      console.error('Delete exhibit error:', err);
      alert(`Failed to delete exhibit: ${err.message}`);
    } finally {
      setDeleteLoading(prev => ({ ...prev, [exhibitId]: false }));
      setShowDeleteModal(false);
      setSelectedExhibit(null);
    }
  };

  // Handle delete button click
  const handleDeleteClick = (exhibit) => {
    setSelectedExhibit(exhibit);
    setShowDeleteModal(true);
  };

  // Handle edit button click
  const handleEditClick = (exhibit) => {
    setSelectedExhibit(exhibit);
    setEditForm({
      name: exhibit.name,
      description: exhibit.description || '',
      location: exhibit.location,
      temperature_min: exhibit.temperature_min,
      temperature_max: exhibit.temperature_max,
      humidity_min: exhibit.humidity_min,
      humidity_max: exhibit.humidity_max,
      vibration_max: exhibit.vibration_max
    });
    setShowEditModal(true);
  };

  // Handle edit form change
  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditForm(prev => ({
      ...prev,
      [name]: name.includes('temperature') || name.includes('humidity') || name.includes('vibration') 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  // Handle edit form submit
  const handleEditSubmit = (e) => {
    e.preventDefault();
    if (selectedExhibit) {
      updateExhibit(selectedExhibit.id, editForm);
    }
  };

  // Handle cancel delete
  const handleCancelDelete = () => {
    setShowDeleteModal(false);
    setSelectedExhibit(null);
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setShowEditModal(false);
    setSelectedExhibit(null);
    setEditForm({});
  };

  // Handle confirm delete
  const handleConfirmDelete = () => {
    if (selectedExhibit) {
      deleteExhibit(selectedExhibit.id);
    }
  };

  // Navigate to add exhibit page
  const handleAddExhibit = () => {
    navigate('/add-exhibit');
  };

  // Navigate to exhibit details/monitoring
  const handleViewExhibit = (exhibitId) => {
    navigate(`/exhibits/${exhibitId}`);
  };

  useEffect(() => {
    fetchExhibits();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="pt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <span className="ml-4 text-lg text-gray-600">Loading exhibits...</span>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Edit Modal */}
      {showEditModal && selectedExhibit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Edit Exhibit</h2>
                <button
                  onClick={handleCancelEdit}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <form onSubmit={handleEditSubmit} className="space-y-6">
                {/* Basic Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Exhibit Name *
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={editForm.name || ''}
                      onChange={handleEditFormChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location *
                    </label>
                    <input
                      type="text"
                      name="location"
                      value={editForm.location || ''}
                      onChange={handleEditFormChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    name="description"
                    value={editForm.description || ''}
                    onChange={handleEditFormChange}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* Environmental Thresholds */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Environmental Thresholds</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Min Temperature (°C)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="temperature_min"
                        value={editForm.temperature_min || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Max Temperature (°C)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="temperature_max"
                        value={editForm.temperature_max || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Min Humidity (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="humidity_min"
                        value={editForm.humidity_min || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Max Humidity (%)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="humidity_max"
                        value={editForm.humidity_max || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Max Vibration
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        name="vibration_max"
                        value={editForm.vibration_max || ''}
                        onChange={handleEditFormChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end space-x-3 pt-6 border-t">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancelEdit}
                    disabled={editLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="default"
                    loading={editLoading}
                    disabled={editLoading}
                  >
                    {editLoading ? 'Updating...' : 'Update Exhibit'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedExhibit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-red-100 rounded-full">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">Delete Exhibit</h3>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-700">
                Are you sure you want to delete <strong>"{selectedExhibit.name}"</strong>?
              </p>
              <p className="text-sm text-gray-600 mt-2">
                This will also delete all associated sensor readings and historical data.
              </p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={handleCancelDelete}
                disabled={deleteLoading[selectedExhibit.id]}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleConfirmDelete}
                loading={deleteLoading[selectedExhibit.id]}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {deleteLoading[selectedExhibit.id] ? 'Deleting...' : 'Delete Exhibit'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Exhibit Management</h1>
                <p className="text-gray-600 mt-1">
                  Manage and monitor all museum exhibits
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                <Button
                  onClick={() => fetchExhibits()}
                  variant="outline"
                  iconName="RefreshCw"
                  iconPosition="left"
                  disabled={loading}
                  className="flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </Button>
                
                <Button
                  onClick={handleAddExhibit}
                  variant="default"
                  iconName="Plus"
                  iconPosition="left"
                  className="flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add New Exhibit
                </Button>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <p className="font-medium text-red-800">Connection Error</p>
                  <p className="text-red-700 text-sm mt-1">{error}</p>
                  <p className="text-red-600 text-xs mt-2">
                    Make sure your backend server is running on {API_BASE_URL}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Exhibits Grid */}
          {exhibits.length === 0 ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No exhibits found</h3>
              <p className="text-gray-600 mb-6">Get started by adding your first exhibit to the monitoring system.</p>
              <Button onClick={handleAddExhibit} variant="default">
                Add First Exhibit
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {exhibits.map((exhibit) => (
                <div key={exhibit.id} className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="p-6">
                    {/* Exhibit Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {exhibit.name}
                        </h3>
                        <p className="text-sm text-gray-600 mb-2">
                          ID: {exhibit.id} • {exhibit.location}
                        </p>
                        <p className="text-sm text-gray-700">
                          {exhibit.description || 'No description available'}
                        </p>
                      </div>
                      
                      {/* Status Indicator */}
                      <div className="flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="ml-2 text-sm text-green-600">Active</span>
                      </div>
                    </div>

                    {/* Thresholds Summary */}
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Monitoring Thresholds</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">Temperature:</span>
                          <br />
                          <span className="font-mono">{exhibit.temperature_min}°C - {exhibit.temperature_max}°C</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Humidity:</span>
                          <br />
                          <span className="font-mono">{exhibit.humidity_min}% - {exhibit.humidity_max}%</span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-600">Max Vibration:</span>
                          <span className="ml-2 font-mono">{exhibit.vibration_max}</span>
                        </div>
                      </div>
                    </div>

                    {/* Timestamps */}
                    <div className="text-xs text-gray-500 mb-4 space-y-1">
                      <div>Created: {new Date(exhibit.created_at).toLocaleDateString()}</div>
                      {exhibit.updated_at !== exhibit.created_at && (
                        <div>Updated: {new Date(exhibit.updated_at).toLocaleDateString()}</div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col space-y-2">
                      <Button
                        onClick={() => handleViewExhibit(exhibit.id)}
                        variant="default"
                        className="w-full flex items-center justify-center"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        View Monitor
                      </Button>
                      
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => handleEditClick(exhibit)}
                          variant="outline"
                          className="flex-1 flex items-center justify-center"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Edit
                        </Button>
                        
                        <Button
                          onClick={() => handleDeleteClick(exhibit)}
                          variant="outline"
                          disabled={deleteLoading[exhibit.id]}
                          className="flex-1 flex items-center justify-center text-red-600 border-red-300 hover:bg-red-50"
                        >
                          {deleteLoading[exhibit.id] ? (
                            <div className="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-red-600 border-t-transparent"></div>
                          ) : (
                            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                          Delete
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Summary Stats */}
          {exhibits.length > 0 && (
            <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Overview</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{exhibits.length}</div>
                  <div className="text-sm text-gray-600">Total Exhibits</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{exhibits.length}</div>
                  <div className="text-sm text-gray-600">Active Exhibits</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">0</div>
                  <div className="text-sm text-gray-600">Maintenance</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">0</div>
                  <div className="text-sm text-gray-600">Offline</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

// Exhibit Monitor Component (for individual exhibit monitoring) - FIXED BACK NAVIGATION
const ExhibitMonitor = ({ exhibitId }) => {
  const navigate = useNavigate(); // Add this hook
  const [sensorData, setSensorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Make sure to set the correct API base URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Fixed back to management function
  const handleBackToManagement = () => {
    navigate('/exhibit-management');
  };

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
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Exhibit Monitor</h2>
            <p className="text-gray-600">Loading exhibit {exhibitId} data...</p>
          </div>
          <Button
            variant="outline"
            onClick={handleBackToManagement}
            className="flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Management
          </Button>
        </div>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading exhibit data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Exhibit Monitor</h2>
            <p className="text-gray-600">Error loading exhibit {exhibitId}</p>
          </div>
          <Button
            variant="outline"
            onClick={handleBackToManagement}
            className="flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Management
          </Button>
        </div>
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
      </div>
    );
  }

  if (!sensorData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Exhibit Monitor</h2>
            <p className="text-gray-600">Exhibit {exhibitId}</p>
          </div>
          <Button
            variant="outline"
            onClick={handleBackToManagement}
            className="flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Management
          </Button>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">No sensor data available for exhibit {exhibitId}</p>
        </div>
      </div>
    );
  }

  const isRealData = sensorData?.sensor_data?.is_real_data;
  const dataSource = sensorData?.sensor_data?.data_source;

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Exhibit Monitor</h2>
          <p className="text-gray-600">Real-time monitoring for Exhibit {exhibitId}</p>
        </div>
        <Button
          variant="outline"
          onClick={handleBackToManagement}
          className="flex items-center"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Management
        </Button>
      </div>

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

export default ExhibitManagement;
export { ExhibitMonitor };