import React from 'react'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-md w-full text-center animate-fade-in">
        <div className="mb-8">
          <h1 className="text-9xl font-semibold mb-4 text-gradient">
            404
          </h1>
          <h2 className="text-2xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
            Page Not Found
          </h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/" className="btn-spa btn-primary">
            <Home size={20} strokeWidth={2} />
            <span>Go Home</span>
          </Link>
          
          <button
            onClick={() => window.history.back()}
            className="btn-spa btn-secondary"
          >
            <ArrowLeft size={20} strokeWidth={2} />
            <span>Go Back</span>
          </button>
        </div>

        <div className="mt-8 text-sm" style={{ color: 'var(--text-tertiary)' }}>
          <p>
            If you believe this is an error, please{' '}
            <Link to="/support" className="font-medium transition-spa" style={{ color: 'var(--accent)' }}>
              contact support
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
