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

// Response interceptor for token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = tokenManager.getRefreshToken()
        if (!refreshToken) {
          throw new Error('No refresh token')
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token } = response.data
        tokenManager.setToken(access_token)
        tokenManager.setRefreshToken(refresh_token)

        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
        tokenManager.clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.')
    } else if (error.response?.status === 403) {
      toast.error('Access denied. You do not have permission for this action.')
    } else if (error.response?.data?.detail) {
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
  
  sendMessage: (data: ChatRequest): Promise<ChatResponse> =>
    api.post('/ai/chat', data).then(res => res.data),
  
  uploadDocument: (conversationId: string, file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/chat/conversations/${conversationId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data)
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