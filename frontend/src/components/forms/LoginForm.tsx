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
        <h1 className="text-3xl font-medium mb-2 text-content-primary">
          Welcome back
        </h1>
        <p className="text-content-secondary">
          Sign in to your PharmGPT account
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2 text-content-primary">
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-content-tertiary" />
            </div>
            <input
              {...register('email')}
              type="email"
              id="email"
              autoComplete="email"
              className={cn(
                'gemini-input w-full pl-10',
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
          <label htmlFor="password" className="block text-sm font-medium mb-2 text-content-primary">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-content-tertiary" />
            </div>
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              className={cn(
                'gemini-input w-full pl-10 pr-10',
                errors.password && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Enter your password"
              disabled={isFormLoading}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center touch-target"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isFormLoading}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-content-tertiary hover:text-content-secondary" />
              ) : (
                <Eye className="h-5 w-5 text-content-tertiary hover:text-content-secondary" />
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
            'w-full px-6 py-3 rounded-gemini-full text-base font-medium bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target',
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
        <p className="text-sm text-content-secondary">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity"
          >
            Sign up
          </Link>
        </p>
        
        <p className="text-sm text-content-secondary">
          <Link
            to="/"
            className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity"
          >
            Back to home
          </Link>
        </p>
      </div>

      {/* Info Boxes */}
      <div className="mt-8 space-y-3">
        {/* Demo Credentials */}
        <div className="p-4 rounded-gemini border border-surface bg-surface-tertiary">
          <h3 className="text-sm font-medium mb-2 text-content-primary">Demo Credentials</h3>
          <div className="text-xs space-y-1 text-content-secondary">
            <p><strong>Admin:</strong> admin@pharmgpt.com / admin123</p>
            <p><strong>User:</strong> Create a new account to test user features</p>
          </div>
        </div>
        
        {/* Cold Start Notice */}
        <div className="p-3 rounded-gemini border border-surface bg-surface-tertiary">
          <p className="text-xs text-content-secondary">
            ⏱️ <strong>First login may take 30-60 seconds</strong> as the server wakes up. Please be patient!
          </p>
        </div>
      </div>
    </div>
  )
}