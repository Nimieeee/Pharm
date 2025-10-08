import axios, { AxiosResponse } from 'axios'
import toast from 'react-hot-toast'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management
const TOKEN_KEY = 'pharmgpt_token'
const REFRESH_TOKEN_KEY = 'pharmgpt_refresh_token'

export const tokenManager = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setRefreshToken: (token: string) => localStorage.setItem(REFRESH_TOKEN_KEY, token),
  clearTokens: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Track if we're currently refreshing to prevent multiple refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (reason?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Response interceptor for token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 errors with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = tokenManager.getRefreshToken()
      
      if (!refreshToken) {
        // No refresh token, clear everything and redirect
        isRefreshing = false
        tokenManager.clearTokens()
        processQueue(error, null)
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          toast.error('Please login to continue')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }

      try {
        // Attempt to refresh the token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: new_refresh_token } = response.data
        
        // Store new tokens
        tokenManager.setToken(access_token)
        if (new_refresh_token) {
          tokenManager.setRefreshToken(new_refresh_token)
        }

        // Update authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        // Process queued requests
        processQueue(null, access_token)
        isRefreshing = false

        // Retry original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect
        processQueue(refreshError, null)
        isRefreshing = false
        tokenManager.clearTokens()
        
        // Only show toast and redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          toast.error('Session expired. Please login again.')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1000)
        }
        
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.response?.status === 403) {
      toast.error('Access denied. You do not have permission for this action.')
    } else if (error.response?.status === 404) {
      // Don't show toast for 404s, let the component handle it
    } else if (error.response?.data?.detail && !originalRequest._retry) {
      // Only show detail errors if not a retry (to avoid duplicate toasts)
      toast.error(error.response.data.detail)
    } else if (error.message === 'Network Error') {
      toast.error('Network error. Please check your connection.')
    }

    return Promise.reject(error)
  }
)

// API Types
export interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
  is_admin: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  document_count: number
  last_activity?: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, any>
  created_at: string
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[]
}

export interface ChatRequest {
  message: string
  conversation_id: string
  mode?: 'fast' | 'detailed'
  use_rag?: boolean
  metadata?: Record<string, any>
}

export interface ChatResponse {
  response: string
  conversation_id: string
  mode: string
  context_used: boolean
}

export interface SupportRequest {
  id: string
  user_id?: string
  email: string
  subject: string
  message: string
  status: 'open' | 'in_progress' | 'resolved' | 'closed'
  admin_response?: string
  created_at: string
  updated_at: string
}

// API Functions
export const authAPI = {
  login: (data: LoginRequest): Promise<TokenResponse> =>
    api.post('/auth/login', data).then(res => res.data),
  
  register: (data: RegisterRequest): Promise<User> =>
    api.post('/auth/register', data).then(res => res.data),
  
  getCurrentUser: (): Promise<User> =>
    api.get('/auth/me').then(res => res.data),
  
  logout: (): Promise<void> =>
    api.post('/auth/logout').then(() => {
      tokenManager.clearTokens()
    }),
}

export const chatAPI = {
  getConversations: (): Promise<Conversation[]> =>
    api.get('/chat/conversations').then(res => res.data),
  
  createConversation: (title: string): Promise<Conversation> =>
    api.post('/chat/conversations', { title }).then(res => res.data),
  
  getConversation: (id: string): Promise<ConversationWithMessages> =>
    api.get(`/chat/conversations/${id}`).then(res => res.data),
  
  updateConversation: (id: string, title: string): Promise<Conversation> =>
    api.put(`/chat/conversations/${id}`, { title }).then(res => res.data),
  
  deleteConversation: (id: string): Promise<void> =>
    api.delete(`/chat/conversations/${id}`).then(res => res.data),
  
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    // Retry logic for Render cold starts (free tier spins down after inactivity)
    const maxRetries = 2
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await api.post('/ai/chat', data, {
          timeout: 240000 // 4 minutes to handle detailed mode with large documents
        })
        return response.data
      } catch (error: any) {
        lastError = error
        
        // Retry on 520 errors (Render cold start) or network errors
        const is520Error = error.response?.status === 520
        const isNetworkError = error.code === 'ERR_NETWORK' || error.code === 'ERR_FAILED'
        
        if ((is520Error || isNetworkError) && attempt < maxRetries) {
          console.log(`Backend is waking up (attempt ${attempt + 1}/${maxRetries + 1})...`)
          // Wait longer on first retry (cold start takes ~30-60s)
          await new Promise(resolve => setTimeout(resolve, attempt === 0 ? 45000 : 15000))
          continue
        }
        
        throw error
      }
    }
    
    throw lastError
  },
  
  uploadDocument: async (conversationId: string, file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    
    // Retry logic for Render cold starts (free tier spins down after inactivity)
    const maxRetries = 2
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await api.post(`/chat/conversations/${conversationId}/documents`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 120000 // 2 minutes timeout for document uploads (rate limiting = 1 req/sec)
        })
        return response.data
      } catch (error: any) {
        lastError = error
        
        // Retry on 520 errors (Render cold start) or network errors
        const is520Error = error.response?.status === 520
        const isNetworkError = error.code === 'ERR_NETWORK' || error.code === 'ERR_FAILED'
        
        if ((is520Error || isNetworkError) && attempt < maxRetries) {
          console.log(`Backend is waking up (attempt ${attempt + 1}/${maxRetries + 1})...`)
          // Wait longer on first retry (cold start takes ~30-60s)
          await new Promise(resolve => setTimeout(resolve, attempt === 0 ? 45000 : 15000))
          continue
        }
        
        throw error
      }
    }
    
    throw lastError
  },
}

export const supportAPI = {
  createRequest: (data: Omit<SupportRequest, 'id' | 'created_at' | 'updated_at' | 'status' | 'user_id'>): Promise<SupportRequest> =>
    api.post('/support/requests', data).then(res => res.data),
  
  getUserRequests: (): Promise<SupportRequest[]> =>
    api.get('/support/requests').then(res => res.data),
  
  getRequest: (id: string): Promise<SupportRequest> =>
    api.get(`/support/requests/${id}`).then(res => res.data),
}

export const adminAPI = {
  getStats: (): Promise<any> =>
    api.get('/admin/stats').then(res => res.data),
  
  getUsers: (params?: { limit?: number; offset?: number; search?: string }): Promise<User[]> =>
    api.get('/admin/users', { params }).then(res => res.data),
  
  updateUserStatus: (userId: string, isActive: boolean): Promise<void> =>
    api.put(`/admin/users/${userId}/status`, null, { params: { is_active: isActive } }).then(res => res.data),
  
  deleteUser: (userId: string): Promise<void> =>
    api.delete(`/admin/users/${userId}`).then(res => res.data),
  
  getSupportRequests: (params?: { status?: string; limit?: number; offset?: number }): Promise<any[]> =>
    api.get('/support/admin/requests', { params }).then(res => res.data),
  
  respondToSupport: (requestId: string, response: string, status: string = 'resolved'): Promise<SupportRequest> =>
    api.post(`/support/admin/requests/${requestId}/respond`, null, { 
      params: { response, status_update: status }
    }).then(res => res.data),
  
  getSystemHealth: (): Promise<any> =>
    api.get('/admin/system-health').then(res => res.data),
}

export default api