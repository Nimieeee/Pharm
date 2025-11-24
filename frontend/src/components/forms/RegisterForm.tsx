import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock, User } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn, validatePassword } from '@/lib/utils'

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
}).refine((data) => validatePassword(data.password).isValid, {
  message: "Password must contain uppercase, lowercase, and number",
  path: ["password"],
})

type RegisterFormData = z.infer<typeof registerSchema>

interface RegisterFormProps {
  className?: string
}

export default function RegisterForm({ className }: RegisterFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const { register: registerUser, isLoading } = useAuth()
  const { darkMode } = useTheme()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const password = watch('password')
  const passwordValidation = password ? validatePassword(password) : { isValid: false, errors: [] }

  const onSubmit = async (data: RegisterFormData) => {
    try {
      const { confirmPassword, ...registerData } = data
      await registerUser(registerData)
    } catch (error) {
      // Error handling is done in the AuthContext
    }
  }

  const isFormLoading = isLoading || isSubmitting

  return (
    <div className={cn('w-full max-w-md mx-auto', className)}>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-medium mb-2 text-content-primary">
          Create your account
        </h1>
        <p className="text-content-secondary">
          Join PharmGPT to access AI-powered pharmacology assistance
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Name Fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium mb-2 text-content-primary">
              First name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-content-tertiary" />
              </div>
              <input
                {...register('first_name')}
                type="text"
                id="first_name"
                autoComplete="given-name"
                className={cn(
                  'gemini-input w-full pl-10',
                  errors.first_name && 'border-red-500 focus:ring-red-500'
                )}
                placeholder="First name"
                disabled={isFormLoading}
              />
            </div>
            {errors.first_name && (
              <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="last_name" className="block text-sm font-medium mb-2 text-content-primary">
              Last name
            </label>
            <input
              {...register('last_name')}
              type="text"
              id="last_name"
              autoComplete="family-name"
              className={cn(
                'gemini-input w-full',
                errors.last_name && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Last name"
              disabled={isFormLoading}
            />
            {errors.last_name && (
              <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
            )}
          </div>
        </div>

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
              autoComplete="new-password"
              className={cn(
                'gemini-input w-full pl-10 pr-10',
                errors.password && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Create a password"
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
          
          {/* Password Requirements */}
          {password && (
            <div className="mt-2 space-y-1">
              {passwordValidation.errors.map((error, index) => (
                <p key={index} className="text-xs text-red-600 flex items-center">
                  <span className="w-1 h-1 bg-red-600 rounded-full mr-2"></span>
                  {error}
                </p>
              ))}
              {passwordValidation.isValid && (
                <p className="text-xs text-green-600 flex items-center">
                  <span className="w-1 h-1 bg-green-600 rounded-full mr-2"></span>
                  Password meets all requirements
                </p>
              )}
            </div>
          )}
          
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>

        {/* Confirm Password Field */}
        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium mb-2 text-content-primary">
            Confirm password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-content-tertiary" />
            </div>
            <input
              {...register('confirmPassword')}
              type={showConfirmPassword ? 'text' : 'password'}
              id="confirmPassword"
              autoComplete="new-password"
              className={cn(
                'gemini-input w-full pl-10 pr-10',
                errors.confirmPassword && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Confirm your password"
              disabled={isFormLoading}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center touch-target"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              disabled={isFormLoading}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5 text-content-tertiary hover:text-content-secondary" />
              ) : (
                <Eye className="h-5 w-5 text-content-tertiary hover:text-content-secondary" />
              )}
            </button>
          </div>
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
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
              Creating account...
            </div>
          ) : (
            'Create account'
          )}
        </button>
      </form>

      {/* Links */}
      <div className="mt-6 text-center space-y-2">
        <p className="text-sm text-content-secondary">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity"
          >
            Sign in
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

      {/* Terms */}
      <div className="mt-6 text-center">
        <p className="text-xs text-content-tertiary">
          By creating an account, you agree to our{' '}
          <a href="#" className="text-gemini-gradient-start hover:opacity-80 transition-opacity">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className="text-gemini-gradient-start hover:opacity-80 transition-opacity">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  )
}
