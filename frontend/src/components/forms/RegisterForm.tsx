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
        <h1 className={cn("text-3xl font-bold mb-2", darkMode ? "text-white" : "text-gray-900")}>
          Create your account
        </h1>
        <p className={cn(darkMode ? "text-gray-300" : "text-gray-600")}>
          Join PharmGPT to access AI-powered pharmacology assistance
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Name Fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="first_name" className={cn("block text-sm font-medium mb-2", darkMode ? "text-gray-200" : "text-gray-700")}>
              First name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className={cn("h-5 w-5", darkMode ? "text-gray-500" : "text-gray-400")} />
              </div>
              <input
                {...register('first_name')}
                type="text"
                id="first_name"
                autoComplete="given-name"
                className={cn(
                  'input pl-10',
                  darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
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
            <label htmlFor="last_name" className={cn("block text-sm font-medium mb-2", darkMode ? "text-gray-200" : "text-gray-700")}>
              Last name
            </label>
            <input
              {...register('last_name')}
              type="text"
              id="last_name"
              autoComplete="family-name"
              className={cn(
                'input',
                darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
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
              autoComplete="new-password"
              className={cn(
                'input pl-10 pr-10',
                darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
                errors.password && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Create a password"
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
          <label htmlFor="confirmPassword" className={cn("block text-sm font-medium mb-2", darkMode ? "text-gray-200" : "text-gray-700")}>
            Confirm password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className={cn("h-5 w-5", darkMode ? "text-gray-500" : "text-gray-400")} />
            </div>
            <input
              {...register('confirmPassword')}
              type={showConfirmPassword ? 'text' : 'password'}
              id="confirmPassword"
              autoComplete="new-password"
              className={cn(
                'input pl-10 pr-10',
                darkMode && 'bg-gray-800 border-gray-700 text-white placeholder-gray-500',
                errors.confirmPassword && 'border-red-500 focus:ring-red-500'
              )}
              placeholder="Confirm your password"
              disabled={isFormLoading}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              disabled={isFormLoading}
            >
              {showConfirmPassword ? (
                <EyeOff className={cn("h-5 w-5", darkMode ? "text-gray-500 hover:text-gray-400" : "text-gray-400 hover:text-gray-600")} />
              ) : (
                <Eye className={cn("h-5 w-5", darkMode ? "text-gray-500 hover:text-gray-400" : "text-gray-400 hover:text-gray-600")} />
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
            'btn-primary w-full btn-md',
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
        <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>
          Already have an account?{' '}
          <Link
            to="/login"
            className={cn("font-medium transition-colors", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}
          >
            Sign in
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

      {/* Terms */}
      <div className="mt-6 text-center">
        <p className={cn("text-xs", darkMode ? "text-gray-400" : "text-gray-500")}>
          By creating an account, you agree to our{' '}
          <a href="#" className={cn(darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}>
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="#" className={cn(darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}>
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  )
}
