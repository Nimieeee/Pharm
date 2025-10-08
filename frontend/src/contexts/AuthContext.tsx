import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

import { authAPI, tokenManager, User, LoginRequest, RegisterRequest } from '@/lib/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const isAuthenticated = !!user

  // Initialize auth state
  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    try {
      const token = tokenManager.getToken()
      if (!token) {
        setIsLoading(false)
        return
      }

      // Verify token and get user data
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error) {
      // Token is invalid, clear it
      tokenManager.clearTokens()
      console.error('Auth initialization failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: LoginRequest) => {
    const maxRetries = 2
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        setIsLoading(true)
        
        // Login and get tokens
        const tokenResponse = await authAPI.login(credentials)
        
        // Store tokens
        tokenManager.setToken(tokenResponse.access_token)
        tokenManager.setRefreshToken(tokenResponse.refresh_token)
        
        // Get user data
        const userData = await authAPI.getCurrentUser()
        setUser(userData)
        
        toast.success('Welcome back!')
        
        // Redirect based on user role
        if (userData.is_admin) {
          navigate('/admin')
        } else {
          navigate('/chat')
        }
        
        return // Success, exit function
        
      } catch (error: any) {
        lastError = error
        console.error(`Login attempt ${attempt + 1} failed:`, error)
        
        // Check if it's a cold start error (network error or timeout)
        const isNetworkError = error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED' || !error.response
        const is520Error = error.response?.status === 520
        
        // Retry on cold start errors
        if ((isNetworkError || is520Error) && attempt < maxRetries) {
          console.log(`Retrying login (attempt ${attempt + 2}/${maxRetries + 1})...`)
          // Wait before retry (longer on first retry for cold start)
          await new Promise(resolve => setTimeout(resolve, attempt === 0 ? 45000 : 15000))
          continue
        }
        
        // Not a cold start error or out of retries
        // Handle specific error cases
        if (error.response?.status === 401) {
          toast.error('Invalid email or password')
        } else if (error.response?.data?.detail) {
          toast.error(error.response.data.detail)
        } else if (isNetworkError) {
          toast.error('Cannot connect to server. Please check your connection or try again in a moment.')
        } else {
          toast.error('Login failed. Please try again.')
        }
        
        throw error
      } finally {
        setIsLoading(false)
      }
    }
    
    // If we get here, all retries failed
    throw lastError
  }

  const register = async (userData: RegisterRequest) => {
    const maxRetries = 2
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        setIsLoading(true)
        
        // Register user
        await authAPI.register(userData)
        
        toast.success('Registration successful! Please log in.')
        navigate('/login')
        return // Success
        
      } catch (error: any) {
        lastError = error
        console.error(`Registration attempt ${attempt + 1} failed:`, error)
        
        // Check if it's a cold start error
        const isNetworkError = error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED' || !error.response
        const is520Error = error.response?.status === 520
        
        // Retry on cold start errors
        if ((isNetworkError || is520Error) && attempt < maxRetries) {
          console.log(`Retrying registration (attempt ${attempt + 2}/${maxRetries + 1})...`)
          await new Promise(resolve => setTimeout(resolve, attempt === 0 ? 45000 : 15000))
          continue
        }
        
        // Not a cold start error or out of retries
        // Handle specific error cases
        if (error.response?.status === 400) {
          const detail = error.response.data?.detail
          if (detail?.includes('already registered')) {
            toast.error('Email is already registered')
          } else {
            toast.error(detail || 'Registration failed')
          }
        } else if (isNetworkError) {
          toast.error('Cannot connect to server. Please check your connection or try again in a moment.')
        } else {
          toast.error('Registration failed. Please try again.')
        }
        
        throw error
      } finally {
        setIsLoading(false)
      }
    }
    
    // If we get here, all retries failed
    throw lastError
  }

  const logout = async () => {
    try {
      // Call logout endpoint (optional, since JWT is stateless)
      await authAPI.logout()
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      // Clear local state regardless of API call result
      setUser(null)
      tokenManager.clearTokens()
      toast.success('Logged out successfully')
      navigate('/')
    }
  }

  const refreshUser = async () => {
    try {
      if (!isAuthenticated) return
      
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user data:', error)
      // If refresh fails, user might need to re-login
      logout()
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Additional hooks for specific use cases
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, isLoading, navigate])

  return { isAuthenticated, isLoading }
}

export function useRequireAdmin() {
  const { user, isAuthenticated, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        navigate('/login')
      } else if (!user?.is_admin) {
        navigate('/chat')
        toast.error('Admin access required')
      }
    }
  }, [user, isAuthenticated, isLoading, navigate])

  return { user, isAuthenticated, isLoading, isAdmin: user?.is_admin || false }
}

export function useRedirectIfAuthenticated() {
  const { isAuthenticated, user, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      if (user?.is_admin) {
        navigate('/admin')
      } else {
        navigate('/chat')
      }
    }
  }, [isAuthenticated, user, isLoading, navigate])

  return { isAuthenticated, isLoading }
}