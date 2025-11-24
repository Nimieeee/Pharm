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
      <div className={cn("min-h-screen flex items-center justify-center", darkMode ? "bg-slate-950" : "bg-slate-50")}>
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  return (
    <div className={cn("min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8", darkMode ? "bg-slate-950" : "bg-slate-50")}>
      <div className="w-full max-w-md">
        <div className={cn("rounded-2xl shadow-xl p-8 border backdrop-blur-sm", darkMode ? "bg-slate-900/80 border-slate-800" : "bg-white/80 border-slate-200")}>
          <LoginForm />
        </div>
      </div>
    </div>
  )
}