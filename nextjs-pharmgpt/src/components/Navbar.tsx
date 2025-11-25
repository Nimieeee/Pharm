'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, Search, X } from 'lucide-react'

export default function Navbar() {
  const [searchOpen, setSearchOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            <span className="text-xl font-semibold">PharmGPT</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/research" className="hover:text-accent transition-colors">
              Research
            </Link>
            <Link href="/safety" className="hover:text-accent transition-colors">
              Safety
            </Link>
            <Link href="/api" className="hover:text-accent transition-colors">
              API
            </Link>
            <Link href="/about" className="hover:text-accent transition-colors">
              About
            </Link>
          </div>

          {/* Right Actions */}
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="p-2 hover:bg-card rounded-lg transition-colors"
              aria-label="Search"
            >
              {searchOpen ? <X size={20} /> : <Search size={20} />}
            </button>
            
            <Link
              href="/login"
              className="hidden md:block px-4 py-2 bg-card hover:bg-card-hover rounded-lg transition-colors"
            >
              Log in
            </Link>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 hover:bg-card rounded-lg transition-colors"
              aria-label="Menu"
            >
              <Menu size={20} />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        {searchOpen && (
          <div className="py-4 animate-fade-in">
            <input
              type="text"
              placeholder="Search PharmGPT..."
              className="w-full px-4 py-3 bg-card rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              autoFocus
            />
          </div>
        )}
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-background animate-fade-in">
          <div className="px-6 py-4 space-y-4">
            <Link href="/research" className="block hover:text-accent transition-colors">
              Research
            </Link>
            <Link href="/safety" className="block hover:text-accent transition-colors">
              Safety
            </Link>
            <Link href="/api" className="block hover:text-accent transition-colors">
              API
            </Link>
            <Link href="/about" className="block hover:text-accent transition-colors">
              About
            </Link>
            <Link
              href="/login"
              className="block px-4 py-2 bg-card hover:bg-card-hover rounded-lg transition-colors text-center"
            >
              Log in
            </Link>
          </div>
        </div>
      )}
    </nav>
  )
}
