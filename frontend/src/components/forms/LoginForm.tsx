import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormData = z.infer<typeof loginSchema>

interface LoginFormProps {
  className?: string
}

export default function LoginForm({ className }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading } = useAuth()
  const { darkMode } = useTheme()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data)
    } catch (error) {
      // Error handling is done in the AuthContext
    }
  }

  const isFormLoading = isLoading || isSubmitting

  return (
    <div className={cn('w-full max-w-md mx-auto', className)}>
      <div className="text-center mb-8">
        <h1 className={cn("text-3xl font-bold mb-2", darkMode ? "text-white" : "text-gray-900")}>
          Welcome back
        </h1>
        <p className={cn(darkMode ? "text-gray-300" : "text-gray-600")}>
          Sign in to your PharmGPT account
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className={cn("block text-sm font-medium mb-2", darkMode ? "text-gray-200" : "text-gray-700")}>
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className={cn("h-5 w-5", darkMode ? "text-gray-500" : "text-gray-400")} />
            </div>
            <input
              {...register('email')}
              type="email"
              id="email"
              autoComplete="email"
              className={cn(
                'input pl-10',
                darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
                errors.email && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Enter your email"
              disabled={isFormLoading}
            />
          </div>
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>

        {/* Password Field */}
        <div>
          <label htmlFor="password" className={cn("block text-sm font-medium mb-2", darkMode ? "text-gray-200" : "text-gray-700")}>
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className={cn("h-5 w-5", darkMode ? "text-gray-500" : "text-gray-400")} />
            </div>
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              className={cn(
                'input pl-10 pr-10',
                darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
                errors.password && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Enter your password"
              disabled={isFormLoading}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isFormLoading}
            >
              {showPassword ? (
                <EyeOff className={cn("h-5 w-5", darkMode ? "text-gray-500 hover:text-gray-400" : "text-gray-400 hover:text-gray-600")} />
              ) : (
                <Eye className={cn("h-5 w-5", darkMode ? "text-gray-500 hover:text-gray-400" : "text-gray-400 hover:text-gray-600")} />
              )}
            </button>
          </div>
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isFormLoading}
          className={cn(
            'btn-primary w-full btn-md',
            isFormLoading && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isFormLoading ? (
            <div className="flex items-center justify-center">
              <div className="spinner mr-2"></div>
              Signing in...
            </div>
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      {/* Links */}
      <div className="mt-6 text-center space-y-2">
        <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>
          Don't have an account?{' '}
          <Link
            to="/register"
            className={cn("font-medium transition-colors", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}
          >
            Sign up
          </Link>
        </p>
        
        <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>
          <Link
            to="/"
            className={cn("font-medium transition-colors", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}
          >
            Back to home
          </Link>
        </p>
      </div>

      {/* Info Boxes */}
      <div className="mt-8 space-y-3">
        {/* Demo Credentials */}
        <div className={cn("p-4 rounded-lg border", darkMode ? "bg-blue-900/30 border-blue-800" : "bg-blue-50 border-blue-200")}>
          <h3 className={cn("text-sm font-medium mb-2", darkMode ? "text-blue-200" : "text-blue-900")}>Demo Credentials</h3>
          <div className={cn("text-xs space-y-1", darkMode ? "text-blue-300" : "text-blue-700")}>
            <p><strong>Admin:</strong> admin@pharmgpt.com / admin123</p>
            <p><strong>User:</strong> Create a new account to test user features</p>
          </div>
        </div>
        
        {/* Cold Start Notice */}
        <div className={cn("p-3 rounded-lg border", darkMode ? "bg-yellow-900/30 border-yellow-800" : "bg-yellow-50 border-yellow-200")}>
          <p className={cn("text-xs", darkMode ? "text-yellow-300" : "text-yellow-700")}>
            ⏱️ <strong>First login may take 30-60 seconds</strong> as the server wakes up. Please be patient!
          </p>
        </div>
      </div>
    </div>
  )
}