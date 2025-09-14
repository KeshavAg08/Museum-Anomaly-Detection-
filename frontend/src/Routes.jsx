import React from 'react'
import { BrowserRouter, Routes as RouterRoutes, Route } from 'react-router-dom'
import AnomalyDashboard from './pages/AnomalyDashboard'
import ExhibitManagement from './pages/ExhibitManagement'
import { ExhibitMonitor } from './pages/ExhibitManagement'
import AddNewExhibit from './pages/AddNewExhibit'
import NotFound from './pages/NotFound'

// Import necessary hooks and components
import { useParams, useNavigate } from 'react-router-dom';
import Header from './components/ui/Header';
import Button from './components/ui/Button';

// Individual Exhibit Monitor Page Component
const ExhibitDetailPage = () => {
  const { id } = useParams();
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ExhibitMonitor exhibitId={parseInt(id)} />
        </div>
      </main>
    </div>
  );
};

const Routes = () => {
  return (
    <BrowserRouter>
      <RouterRoutes>
        {/* Main Dashboard */}
        <Route path="/" element={<AnomalyDashboard />} />
        <Route path="/anomaly-dashboard" element={<AnomalyDashboard />} />
        
        {/* Exhibit Management */}
        <Route path="/exhibit-management" element={<ExhibitManagement />} />
        
        {/* Add New Exhibit - Fixed route to match your ExhibitManagement navigation */}
        <Route path="/add-exhibit" element={<AddNewExhibit />} />
        <Route path="/add-new-exhibit" element={<AddNewExhibit />} />
        
        {/* Individual Exhibit Monitoring */}
        <Route path="/exhibits/:id" element={<ExhibitDetailPage />} />
        <Route path="/exhibits/:id/monitor" element={<ExhibitDetailPage />} />
        
        {/* Individual Exhibit Edit (placeholder for future implementation) */}
        <Route path="/exhibits/:id/edit" element={<AddNewExhibit />} />
        
        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </RouterRoutes>
    </BrowserRouter>
  )
}

export default Routes