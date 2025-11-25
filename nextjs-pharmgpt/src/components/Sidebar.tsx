'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronRight, FileText, Shield, Building2, Code, Newspaper } from 'lucide-react'

export default function Sidebar() {
  const [isOpen, setIsOpen] = useState(false)

  const menuItems = [
    { icon: FileText, label: 'Research', href: '/research' },
    { icon: Shield, label: 'Safety', href: '/safety' },
    { icon: Building2, label: 'For Business', href: '/business' },
    { icon: Code, label: 'For Developers', href: '/api' },
    { icon: Newspaper, label: 'News', href: '/news' },
  ]

  return (
    <>
      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-6 top-24 z-40 p-2 bg-card hover:bg-card-hover rounded-lg transition-all"
        aria-label="Toggle sidebar"
      >
        <ChevronRight
          size={20}
          className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-16 bottom-0 w-64 bg-background border-r border-border z-30 transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <nav className="p-6 space-y-2">
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-card transition-colors group"
            >
              <item.icon size={20} className="text-gray-400 group-hover:text-accent" />
              <span className="group-hover:text-accent transition-colors">{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      {/* Overlay */}
      {isOpen && (
        <div
          onClick={() => setIsOpen(false)}
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
        />
      )}
    </>
  )
}
