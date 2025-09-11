import React from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/ui/Header'
import Button from '../components/ui/Button'

const NotFound = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="pt-16">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <h1 className="text-6xl font-bold text-text-primary mb-4">404</h1>
            <p className="text-xl text-text-secondary mb-8">Page not found</p>
            <Link to="/">
              <Button variant="default" iconName="ArrowLeft" iconPosition="left">
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFound
