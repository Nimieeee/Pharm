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
    <nav className={cn("shadow-sm border-b", darkMode ? "bg-[#171717] border-gray-800" : "bg-white border-gray-200")}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <img src="/PharmGPT.png" alt="PharmGPT" className="w-8 h-8" />
              <span className={cn("text-xl font-bold", darkMode ? "text-white" : "text-gray-900")}>PharmGPT</span>
            </Link>
          </div>
          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActivePath(item.href)
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>

          {/* User menu */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className={cn("flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-md p-2", 
                    darkMode ? "text-gray-300 hover:text-white" : "text-gray-700 hover:text-gray-900"
                  )}
                >
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                  <span className="text-sm font-medium">
                    {user?.first_name || user?.email}
                  </span>
                </button>

                {isUserMenuOpen && (
                  <div className={cn("absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 z-50 border", 
                    darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"
                  )}>
                    <div className={cn("px-4 py-2 text-sm border-b", darkMode ? "text-gray-400 border-gray-700" : "text-gray-500 border-gray-100")}>
                      {user?.email}
                      {user?.is_admin && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          Admin
                        </span>
                      )}
                    </div>
                    
                    <Link
                      to="/"
                      className={cn("block px-4 py-2 text-sm flex items-center space-x-2", 
                        darkMode ? "text-gray-300 hover:bg-gray-700" : "text-gray-700 hover:bg-gray-100"
                      )}
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Home className="w-4 h-4" />
                      <span>Home</span>
                    </Link>
                    
                    <button
                      onClick={handleLogout}
                      className={cn("block w-full text-left px-4 py-2 text-sm flex items-center space-x-2", 
                        darkMode ? "text-gray-300 hover:bg-gray-700" : "text-gray-700 hover:bg-gray-100"
                      )}
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  to="/login"
                  className={cn("px-3 py-2 rounded-md text-sm font-medium", 
                    darkMode ? "text-gray-300 hover:text-white" : "text-gray-700 hover:text-gray-900"
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
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-md p-2"
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
          <div className={cn("px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t", 
            darkMode ? "bg-[#171717] border-gray-800" : "bg-white border-gray-200"
          )}>
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium',
                    isActivePath(item.href)
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                  )}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
            
            {isAuthenticated ? (
              <div className={cn("border-t pt-4 mt-4", darkMode ? "border-gray-800" : "border-gray-200")}>
                <div className={cn("px-3 py-2 text-sm", darkMode ? "text-gray-400" : "text-gray-500")}>
                  {user?.email}
                  {user?.is_admin && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                      Admin
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className={cn("flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium w-full text-left", 
                    darkMode ? "text-gray-300 hover:text-white hover:bg-gray-800" : "text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                  )}
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <div className={cn("border-t pt-4 mt-4 space-y-1", darkMode ? "border-gray-800" : "border-gray-200")}>
                <Link
                  to="/login"
                  className={cn("block px-3 py-2 rounded-md text-base font-medium", 
                    darkMode ? "text-gray-300 hover:text-white hover:bg-gray-800" : "text-gray-700 hover:text-gray-900 hover:bg-gray-50"
                  )}
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="block px-3 py-2 rounded-md text-base font-medium text-white bg-primary-600 hover:bg-primary-700"
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