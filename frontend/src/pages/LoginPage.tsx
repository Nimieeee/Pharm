import React from 'react'
import { useRedirectIfAuthenticated } from '@/contexts/AuthContext'
import LoginForm from '@/components/forms/LoginForm'

export default function LoginPage() {
  const { isLoading } = useRedirectIfAuthenticated()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}