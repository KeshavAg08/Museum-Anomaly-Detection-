import React from 'react'
import { BrowserRouter, Routes as RouterRoutes, Route } from 'react-router-dom'
import AnomalyDashboard from './pages/AnomalyDashboard'
import ExhibitManagement from './pages/ExhibitManagement'
import AddNewExhibit from './pages/AddNewExhibit'
import NotFound from './pages/NotFound'

const Routes = () => {
  return (
    <BrowserRouter>
      <RouterRoutes>
        <Route path="/" element={<AnomalyDashboard />} />
        <Route path="/anomaly-dashboard" element={<AnomalyDashboard />} />
        <Route path="/exhibit-management" element={<ExhibitManagement />} />
        <Route path="/add-new-exhibit" element={<AddNewExhibit />} />
        <Route path="*" element={<NotFound />} />
      </RouterRoutes>
    </BrowserRouter>
  )
}

export default Routes
