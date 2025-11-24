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
      <div className="min-h-screen flex items-center justify-center bg-surface-primary">
        <div className="ai-loader"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-surface-primary">
      <div className="w-full max-w-md">
        <div className="rounded-gemini shadow-gemini-lg p-8 border border-surface backdrop-blur-sm bg-surface-secondary/80">
          <RegisterForm />
        </div>
      </div>
    </div>
  )
}