import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X, User, LogOut, Settings, MessageSquare, Home, Shield } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuth()
  const { darkMode } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    setIsUserMenuOpen(false)
  }

  const isActivePath = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  const publicNavItems = [
    { name: 'Home', href: '/', icon: Home },
  ]

  const userNavItems = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
  ]

  const adminNavItems = [
    { name: 'Admin', href: '/admin', icon: Shield },
    { name: 'Users', href: '/admin/users', icon: User },
  ]

  const getNavItems = () => {
    if (!isAuthenticated) return publicNavItems
    if (user?.is_admin) return [...userNavItems, ...adminNavItems]
    return userNavItems
  }

  const navItems = getNavItems()

  return (
    <nav className={cn(
      "shadow-xl border-b-2 backdrop-blur-xl relative z-50",
      darkMode ? "bg-teal-950/80 border-teal-800" : "bg-white/80 border-teal-200"
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3 group">
              <img src="/PharmGPT.png" alt="PharmGPT" className="w-9 h-9 drop-shadow-lg transition-transform duration-300 group-hover:scale-110" />
              <span className={cn(
                "text-xl font-display font-black transition-colors",
                darkMode ? "text-teal-50" : "text-teal-900"
              )}>
                PharmGPT
              </span>
            </Link>
          </div>
          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 hover:scale-105',
                    isActivePath(item.href)
                      ? (darkMode 
                          ? 'text-teal-50 bg-gradient-to-r from-teal-700 to-teal-600 shadow-lg shadow-teal-900/50' 
                          : 'text-white bg-gradient-to-r from-teal-500 to-teal-400 shadow-lg shadow-teal-500/30'
                        )
                      : (darkMode 
                          ? 'text-teal-300 hover:text-teal-50 hover:bg-teal-900' 
                          : 'text-teal-700 hover:text-teal-900 hover:bg-teal-50'
                        )
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>

          {/* User menu */}
          <div className="hidden md:flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className={cn(
                    "flex items-center space-x-3 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 rounded-xl p-2 transition-all duration-300 hover:scale-105", 
                    darkMode ? "text-teal-300 hover:text-teal-50 hover:bg-teal-900" : "text-teal-700 hover:text-teal-900 hover:bg-teal-50"
                  )}
                >
                  <div className={cn(
                    "w-9 h-9 rounded-xl flex items-center justify-center shadow-lg",
                    darkMode ? "bg-gradient-to-br from-teal-700 to-teal-600" : "bg-gradient-to-br from-teal-500 to-teal-400"
                  )}>
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm font-semibold">
                    {user?.first_name || user?.email}
                  </span>
                </button>

                {isUserMenuOpen && (
                  <div className={cn(
                    "absolute right-0 mt-3 w-56 rounded-2xl shadow-2xl py-2 z-50 border-2 backdrop-blur-xl", 
                    darkMode ? "bg-teal-950/90 border-teal-800" : "bg-white/90 border-teal-200"
                  )}>
                    <div className={cn(
                      "px-4 py-3 text-sm border-b-2 font-medium", 
                      darkMode ? "text-teal-300 border-teal-800" : "text-teal-700 border-teal-200"
                    )}>
                      {user?.email}
                      {user?.is_admin && (
                        <span className="ml-2 inline-flex items-center px-2 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-accent-500 to-accent-400 text-white shadow-lg">
                          Admin
                        </span>
                      )}
                    </div>
                    
                    <Link
                      to="/"
                      className={cn(
                        "block px-4 py-3 text-sm flex items-center space-x-3 font-medium transition-colors", 
                        darkMode ? "text-teal-300 hover:bg-teal-900 hover:text-teal-50" : "text-teal-700 hover:bg-teal-50 hover:text-teal-900"
                      )}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Home className="w-4 h-4" />
                      <span>Home</span>
                    </Link>
                    
                    <button
                      onClick={handleLogout}
                      className={cn(
                        "block w-full text-left px-4 py-3 text-sm flex items-center space-x-3 font-medium transition-colors", 
                        darkMode ? "text-teal-300 hover:bg-teal-900 hover:text-teal-50" : "text-teal-700 hover:bg-teal-50 hover:text-teal-900"
                      )}
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className={cn(
                    "px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-300 hover:scale-105", 
                    darkMode ? "text-teal-300 hover:text-teal-50 hover:bg-teal-900" : "text-teal-700 hover:text-teal-900 hover:bg-teal-50"
                  )}
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="btn-primary btn-sm"
                >
                  Sign up
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className={cn(
                "focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 rounded-xl p-2 transition-all duration-300 hover:scale-110",
                darkMode ? "text-teal-300 hover:text-teal-50 hover:bg-teal-900" : "text-teal-700 hover:text-teal-900 hover:bg-teal-50"
              )}
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className={cn(
            "px-3 pt-3 pb-4 space-y-2 sm:px-4 border-t-2 backdrop-blur-xl", 
            darkMode ? "bg-teal-950/90 border-teal-800" : "bg-white/90 border-teal-200"
          )}>
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-semibold transition-all duration-300',
                    isActivePath(item.href)
                      ? (darkMode 
                          ? 'text-teal-50 bg-gradient-to-r from-teal-700 to-teal-600 shadow-lg shadow-teal-900/50' 
                          : 'text-white bg-gradient-to-r from-teal-500 to-teal-400 shadow-lg shadow-teal-500/30'
                        )
                      : (darkMode 
                          ? 'text-teal-300 hover:text-teal-50 hover:bg-teal-900' 
                          : 'text-teal-700 hover:text-teal-900 hover:bg-teal-50'
                        )
                  )}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
            
            {isAuthenticated ? (
              <div className={cn("border-t-2 pt-4 mt-4", darkMode ? "border-teal-800" : "border-teal-200")}>
                <div className={cn(
                  "px-4 py-3 text-sm font-medium rounded-xl mb-2", 
                  darkMode ? "text-teal-300 bg-teal-900/50" : "text-teal-700 bg-teal-50"
                )}>
                  {user?.email}
                  {user?.is_admin && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-accent-500 to-accent-400 text-white shadow-lg">
                      Admin
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className={cn(
                    "flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-semibold w-full text-left transition-all duration-300", 
                    darkMode ? "text-teal-300 hover:text-teal-50 hover:bg-teal-900" : "text-teal-700 hover:text-teal-900 hover:bg-teal-50"
                  )}
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <div className={cn("border-t-2 pt-4 mt-4 space-y-2", darkMode ? "border-teal-800" : "border-teal-200")}>
                <Link
                  to="/login"
                  className={cn(
                    "block px-4 py-3 rounded-xl text-base font-semibold transition-all duration-300", 
                    darkMode ? "text-teal-300 hover:text-teal-50 hover:bg-teal-900" : "text-teal-700 hover:text-teal-900 hover:bg-teal-50"
                  )}
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="block px-4 py-3 rounded-xl text-base font-semibold text-white bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-700 hover:to-teal-600 shadow-lg shadow-teal-500/40 transition-all duration-300"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign up
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Overlay for user menu */}
      {isUserMenuOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsUserMenuOpen(false)}
        />
      )}
    </nav>
  )
}