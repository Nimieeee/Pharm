import React from 'react'
import { useRedirectIfAuthenticated } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'
import LoginForm from '@/components/forms/LoginForm'

export default function LoginPage() {
  const { isLoading } = useRedirectIfAuthenticated()
  const { darkMode } = useTheme()

  if (isLoading) {
    return (
      <div className={cn("min-h-screen flex items-center justify-center", darkMode ? "bg-[#212121]" : "bg-white")}>
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8", darkMode ? "bg-[#212121]" : "bg-gradient-to-br from-primary-50 to-secondary-50")}>
      <div className="w-full max-w-md">
        <div className={cn("rounded-lg shadow-xl p-8", darkMode ? "bg-gray-800" : "bg-white")}>
          <LoginForm />
        </div>
      </div>
    </div>
  )
}