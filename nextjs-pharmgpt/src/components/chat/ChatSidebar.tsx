'use client'

import Link from 'next/link'
import { 
  PanelLeft, 
  Plus, 
  Search, 
  Library, 
  Folder,
  MessageSquare,
  MoreHorizontal,
  User,
  Sparkles
} from 'lucide-react'

interface ChatSidebarProps {
  isOpen: boolean
  onToggle: () => void
}

export default function ChatSidebar({ isOpen, onToggle }: ChatSidebarProps) {
  const chatHistory = [
    { id: '1', title: 'Drug interactions with Metformin', date: 'Today' },
    { id: '2', title: 'Clinical trial analysis', date: 'Today' },
    { id: '3', title: 'Pharmacokinetics overview', date: 'Yesterday' },
    { id: '4', title: 'FDA approval guidelines', date: 'Yesterday' },
    { id: '5', title: 'Adverse effects monitoring', date: 'Last 7 days' },
  ]

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`${
          isOpen ? 'w-64' : 'w-0'
        } bg-[#171717] border-r border-border transition-all duration-300 overflow-hidden flex flex-col`}
      >
        {/* Top Actions */}
        <div className="p-2 space-y-1">
          <button
            onClick={onToggle}
            className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors"
          >
            <PanelLeft size={18} />
            <span className="text-sm">Close sidebar</span>
          </button>

          <Link
            href="/chat"
            className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors"
          >
            <Plus size={18} />
            <span className="text-sm">New chat</span>
          </Link>

          <button className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors">
            <Search size={18} />
            <span className="text-sm">Search chats</span>
          </button>

          <Link
            href="/library"
            className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors"
          >
            <Library size={18} />
            <span className="text-sm">Library</span>
          </Link>
        </div>

        {/* Projects Section */}
        <div className="px-2 py-4 border-t border-border">
          <div className="flex items-center justify-between px-3 mb-2">
            <h3 className="text-xs font-semibold text-gray-400 uppercase">Projects</h3>
          </div>
          <button className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-card transition-colors text-sm">
            <Folder size={16} />
            <span>Research Database</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-2">
          <div className="flex items-center justify-between px-3 mb-2">
            <h3 className="text-xs font-semibold text-gray-400 uppercase">Your chats</h3>
          </div>
          <div className="space-y-1">
            {chatHistory.map((chat) => (
              <Link
                key={chat.id}
                href={`/chat/${chat.id}`}
                className="group w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-card transition-colors"
              >
                <div className="flex items-center space-x-2 flex-1 min-w-0">
                  <MessageSquare size={16} className="flex-shrink-0" />
                  <span className="text-sm truncate">{chat.title}</span>
                </div>
                <button className="opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreHorizontal size={16} />
                </button>
              </Link>
            ))}
          </div>
        </div>

        {/* User Profile */}
        <div className="p-2 border-t border-border">
          <button className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-card transition-colors">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                <User size={16} />
              </div>
              <div className="text-left">
                <div className="text-sm font-medium">User</div>
                <div className="text-xs text-gray-400">Free Plan</div>
              </div>
            </div>
            <button className="px-3 py-1 bg-card hover:bg-card-hover rounded-md text-xs transition-colors">
              Upgrade
            </button>
          </button>
        </div>
      </aside>

      {/* Toggle Button (when closed) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed left-4 top-4 z-50 p-2 bg-card hover:bg-card-hover rounded-lg transition-colors"
        >
          <PanelLeft size={20} />
        </button>
      )}
    </>
  )
}
