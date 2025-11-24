import React from 'react'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface-primary flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-medium text-gemini-gradient mb-4">404</h1>
          <h2 className="text-2xl font-medium text-content-primary mb-2">Page Not Found</h2>
          <p className="text-content-secondary">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to="/"
            className="inline-flex items-center px-6 py-3 rounded-gemini-full bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target"
          >
            <Home className="w-4 h-4 mr-2" />
            Go Home
          </Link>
          
          <div>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center px-6 py-3 rounded-gemini-full border border-surface bg-surface-secondary text-content-primary hover:bg-surface-tertiary transition-colors touch-target"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </button>
          </div>
        </div>

        <div className="mt-8 text-sm text-content-tertiary">
          <p>
            If you believe this is an error, please{' '}
            <Link to="/support" className="text-gemini-gradient-start hover:opacity-80 transition-opacity">
              contact support
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}