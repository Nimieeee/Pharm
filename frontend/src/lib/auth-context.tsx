'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  is_admin: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  checkUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  refreshToken: async () => false,
  checkUser: async () => {},
});

export const useAuth = () => useContext(AuthContext);

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? '' // Use relative path (proxied by Vercel rewrites)
  : 'http://localhost:8000';

// Helper to decode JWT and check expiration
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    // Consider token expired if less than 5 minutes remaining
    return Date.now() > exp - 5 * 60 * 1000;
  } catch {
    return true;
  }
}

// Helper to get token expiration time
function getTokenExpiration(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshTimer, setRefreshTimer] = useState<NodeJS.Timeout | null>(null);

  // Refresh the access token using the refresh token
  const refreshToken = useCallback(async (): Promise<boolean> => {
    const refreshTokenValue = localStorage.getItem('refresh_token');
    if (!refreshTokenValue) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token);
        }
        setToken(data.access_token);
        scheduleTokenRefresh(data.access_token);
        return true;
      } else {
        // Refresh token is invalid, logout
        logout();
        return false;
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
      return false;
    }
  }, []);

  // Schedule automatic token refresh before expiration
  const scheduleTokenRefresh = useCallback((accessToken: string) => {
    // Clear any existing timer
    if (refreshTimer) {
      clearTimeout(refreshTimer);
    }

    const expiration = getTokenExpiration(accessToken);
    if (!expiration) return;

    // Refresh 5 minutes before expiration
    const refreshTime = expiration - Date.now() - 5 * 60 * 1000;
    
    if (refreshTime > 0) {
      const timer = setTimeout(async () => {
        console.log('Auto-refreshing token...');
        await refreshToken();
      }, refreshTime);
      setRefreshTimer(timer);
    }
  }, [refreshTimer, refreshToken]);

  const fetchUser = useCallback(async (authToken: string) => {
    try {
      // Check if token is expired before making request
      if (isTokenExpired(authToken)) {
        const refreshed = await refreshToken();
        if (!refreshed) {
          setIsLoading(false);
          return;
        }
        authToken = localStorage.getItem('token') || authToken;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        scheduleTokenRefresh(authToken);
      } else if (response.status === 401) {
        // Token might be expired, try to refresh
        const refreshed = await refreshToken();
        if (refreshed) {
          // Retry fetching user with new token
          const newToken = localStorage.getItem('token');
          if (newToken) {
            const retryResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
              headers: {
                'Authorization': `Bearer ${newToken}`,
              },
            });
            if (retryResponse.ok) {
              const userData = await retryResponse.json();
              setUser(userData);
              return;
            }
          }
        }
        // If refresh failed, clear auth state
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        setToken(null);
        setUser(null);
      } else {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        setToken(null);
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setIsLoading(false);
    }
  }, [refreshToken, scheduleTokenRefresh]);

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
      fetchUser(savedToken);
    } else {
      setIsLoading(false);
    }

    // Cleanup timer on unmount
    return () => {
      if (refreshTimer) {
        clearTimeout(refreshTimer);
      }
    };
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setToken(data.access_token);
    await fetchUser(data.access_token);
  };

  const register = async (email: string, password: string, firstName?: string, lastName?: string) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    // Auto-login after registration
    // await login(email, password);
  };

  const logout = useCallback(() => {
    if (refreshTimer) {
      clearTimeout(refreshTimer);
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  }, [refreshTimer]);

  const checkUser = useCallback(async () => {
    const currentToken = localStorage.getItem('token');
    if (currentToken) {
      await fetchUser(currentToken);
    }
  }, [fetchUser]);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, refreshToken, checkUser }}>
      {children}
    </AuthContext.Provider>
  );
}
