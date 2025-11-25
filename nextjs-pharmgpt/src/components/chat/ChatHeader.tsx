'use client'

import { ChevronDown, Users, Clock } from 'lucide-react'

interface ChatHeaderProps {
  onToggleSidebar: () => void
}

export default function ChatHeader({ onToggleSidebar }: ChatHeaderProps) {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur-lg">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Model Selector */}
        <button className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors">
          <span className="font-semibold">PharmGPT</span>
          <ChevronDown size={16} />
        </button>

        {/* Right Actions */}
        <div className="flex items-center space-x-2">
          <button
            className="p-2 rounded-lg hover:bg-card transition-colors"
            title="Start group chat"
          >
            <Users size={18} />
          </button>
          <button
            className="p-2 rounded-lg hover:bg-card transition-colors"
            title="Temporary chat"
          >
            <Clock size={18} />
          </button>
        </div>
      </div>
    </header>
  )
}
