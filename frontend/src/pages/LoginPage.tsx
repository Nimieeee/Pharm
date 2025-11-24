import React from 'react'
import { useRedirectIfAuthenticated } from '@/contexts/AuthContext'
import LoginForm from '@/components/forms/LoginForm'

export default function LoginPage() {
  const { isLoading } = useRedirectIfAuthenticated()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="spinner-spa"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4" style={{ background: 'var(--bg-primary)' }}>
      <div className="w-full max-w-md animate-fade-in">
        <div className="card-spa p-8 md:p-10">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}