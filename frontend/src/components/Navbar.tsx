import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Menu, X, User, LogOut, Home, Shield, MessageSquare } from 'lucide-react'
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
    <nav className="sticky top-0 z-50 border-b border-surface backdrop-blur-xl bg-surface-primary/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3 group">
              <img 
                src="/PharmGPT.png" 
                alt="PharmGPT" 
                className="w-8 h-8 transition-transform group-hover:scale-110" 
              />
              <span className="text-lg font-medium transition-colors text-content-primary">
                PharmGPT
              </span>
            </Link>
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActivePath(item.href)
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 touch-target',
                    active
                      ? 'bg-surface-tertiary text-content-primary'
                      : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
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
                  className="flex items-center space-x-2 px-3 py-2 rounded-xl transition-all duration-200 text-content-secondary hover:text-content-primary hover:bg-surface-secondary touch-target"
                >
                  <div className="w-8 h-8 rounded-full bg-gemini-gradient flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span className="text-sm font-medium">
                    {user?.first_name || user?.email}
                  </span>
                </button>

                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-gemini shadow-gemini-lg py-2 z-50 border border-surface backdrop-blur-xl bg-surface-secondary/95">
                    <div className="px-4 py-3 text-sm border-b border-surface text-content-secondary">
                      {user?.email}
                      {user?.is_admin && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gemini-gradient text-white">
                          Admin
                        </span>
                      )}
                    </div>
                    
                    <Link
                      to="/"
                      className="flex items-center space-x-2 px-4 py-2 text-sm transition-colors text-content-secondary hover:bg-surface-tertiary hover:text-content-primary touch-target"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Home className="w-4 h-4" />
                      <span>Home</span>
                    </Link>
                    
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 px-4 py-2 text-sm w-full transition-colors text-content-secondary hover:bg-surface-tertiary hover:text-content-primary touch-target"
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
                  className="px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 text-content-secondary hover:text-content-primary hover:bg-surface-secondary touch-target"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-gemini text-sm font-medium bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target"
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
              className="p-2 rounded-xl transition-colors text-content-secondary hover:text-content-primary hover:bg-surface-secondary touch-target"
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
        <div className="md:hidden border-t border-surface backdrop-blur-xl">
          <div className="px-4 py-3 space-y-2 bg-surface-primary/95">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActivePath(item.href)
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium transition-all duration-200 touch-target',
                    active
                      ? 'bg-surface-tertiary text-content-primary'
                      : 'text-content-secondary hover:text-content-primary hover:bg-surface-secondary'
                  )}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
            
            {isAuthenticated ? (
              <div className="border-t border-surface pt-4 mt-4">
                <div className="px-4 py-3 text-sm rounded-xl mb-2 text-content-secondary bg-surface-secondary">
                  {user?.email}
                  {user?.is_admin && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gemini-gradient text-white">
                      Admin
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium w-full transition-all duration-200 text-content-secondary hover:text-content-primary hover:bg-surface-secondary touch-target"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <div className="border-t border-surface pt-4 mt-4 space-y-2">
                <Link
                  to="/login"
                  className="block px-4 py-3 rounded-xl text-base font-medium transition-all duration-200 text-content-secondary hover:text-content-primary hover:bg-surface-secondary touch-target"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="block px-4 py-3 rounded-gemini text-base font-medium text-white bg-gemini-gradient hover:opacity-90 transition-opacity touch-target"
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
