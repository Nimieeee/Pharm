import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function ThemeToggle() {
  const { darkMode, toggleDarkMode } = useTheme()

  return (
    <button
      onClick={toggleDarkMode}
      className={cn(
        "fixed top-4 right-4 z-[100] p-3 rounded-full shadow-lg transition-colors",
        darkMode ? "bg-gray-800 hover:bg-gray-700 text-white" : "bg-white hover:bg-gray-100 text-gray-900"
      )}
      aria-label="Toggle dark mode"
    >
      {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  )
}
