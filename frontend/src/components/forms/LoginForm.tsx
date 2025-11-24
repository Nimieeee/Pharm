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
    <div className={cn('w-full', className)}>
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-semibold mb-3" 
            style={{ 
              color: 'var(--text-primary)',
              fontFamily: "'Cormorant Garamond', Georgia, serif"
            }}>
          Welcome back
        </h1>
        <p className="text-base" style={{ color: 'var(--text-secondary)' }}>
          Sign in to your PharmGPT account
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Mail size={20} strokeWidth={2} style={{ color: 'var(--text-tertiary)' }} />
            </div>
            <input
              {...register('email')}
              type="email"
              id="email"
              autoComplete="email"
              className={cn(
                'input-spa pl-12',
                errors.email && 'border-red-500'
              )}
              placeholder="you@example.com"
              disabled={isFormLoading}
            />
          </div>
          {errors.email && (
            <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>

        {/* Password Field */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock size={20} strokeWidth={2} style={{ color: 'var(--text-tertiary)' }} />
            </div>
            <input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              className={cn(
                'input-spa pl-12 pr-12',
                errors.password && 'border-red-500'
              )}
              placeholder="Enter your password"
              disabled={isFormLoading}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-4 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isFormLoading}
              style={{ minWidth: '44px', minHeight: '44px' }}
            >
              {showPassword ? (
                <EyeOff size={20} strokeWidth={2} style={{ color: 'var(--text-tertiary)' }} />
              ) : (
                <Eye size={20} strokeWidth={2} style={{ color: 'var(--text-tertiary)' }} />
              )}
            </button>
          </div>
          {errors.password && (
            <p className="mt-2 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isFormLoading}
          className={cn(
            'btn-spa btn-primary w-full',
            isFormLoading && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isFormLoading ? (
            <>
              <div className="spinner-spa"></div>
              <span>Signing in...</span>
            </>
          ) : (
            <span>Sign in</span>
          )}
        </button>
      </form>

      {/* Links */}
      <div className="mt-8 text-center space-y-3">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-medium transition-spa"
            style={{ color: 'var(--accent)' }}
          >
            Sign up
          </Link>
        </p>
        
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          <Link
            to="/"
            className="font-medium transition-spa"
            style={{ color: 'var(--accent)' }}
          >
            Back to home
          </Link>
        </p>
      </div>

      {/* Info Boxes */}
      <div className="mt-8 space-y-4">
        {/* Demo Credentials */}
        <div className="p-4 rounded-spa" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
          <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Demo Credentials</h3>
          <div className="text-sm space-y-1" style={{ color: 'var(--text-secondary)' }}>
            <p><strong>Admin:</strong> admin@pharmgpt.com / admin123</p>
            <p><strong>User:</strong> Create a new account</p>
          </div>
        </div>
        
        {/* Cold Start Notice */}
        <div className="p-4 rounded-spa" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            <strong>Note:</strong> First login may take 30-60 seconds as the server wakes up.
          </p>
        </div>
      </div>
    </div>
  )
}