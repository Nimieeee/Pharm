import React from 'react'
import { useRedirectIfAuthenticated } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'
import RegisterForm from '@/components/forms/RegisterForm'

export default function RegisterPage() {
  const { isLoading } = useRedirectIfAuthenticated()
  const { darkMode } = useTheme()

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
          <RegisterForm />
        </div>
      </div>
    </div>
  )
}