import React, { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface AdminRouteProps {
  children: ReactNode
  redirectTo?: string
}

export default function AdminRoute({ 
  children, 
  redirectTo = '/dashboard' 
}: AdminRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-secondary-600">Verifying admin access...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location }} 
        replace 
      />
    )
  }

  // Redirect to dashboard if not admin
  if (!user?.is_admin) {
    return (
      <Navigate 
        to={redirectTo} 
        replace 
      />
    )
  }

  // Render admin content
  return <>{children}</>
}