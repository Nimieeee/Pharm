import React from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, FileText, Clock, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function DashboardPage() {
  const { user } = useAuth()
  const { darkMode } = useTheme()

  return (
    <div className={cn("min-h-screen py-8", darkMode ? "bg-[#212121]" : "bg-gray-50")}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className={cn("text-3xl font-bold", darkMode ? "text-white" : "text-gray-900")}>
            Welcome back, {user?.first_name || 'User'}!
          </h1>
          <p className={cn("mt-2", darkMode ? "text-gray-300" : "text-gray-600")}>
            Continue your pharmaceutical research and conversations
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link
            to="/chat"
            className={cn("p-6 rounded-2xl hover:shadow-lg transition-shadow cursor-pointer", darkMode ? "bg-gray-800 hover:bg-gray-750" : "bg-white")}
          >
            <div className="flex items-center">
              <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mr-4", darkMode ? "bg-blue-900/30" : "bg-primary-100")}>
                <MessageSquare className={cn("w-6 h-6", darkMode ? "text-blue-400" : "text-primary-600")} />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-gray-900")}>Start New Chat</h3>
                <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>Begin a new conversation</p>
              </div>
            </div>
          </Link>

          <Link
            to="/support"
            className={cn("p-6 rounded-2xl hover:shadow-lg transition-shadow cursor-pointer", darkMode ? "bg-gray-800 hover:bg-gray-750" : "bg-white")}
          >
            <div className="flex items-center">
              <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mr-4", darkMode ? "bg-green-900/30" : "bg-green-100")}>
                <FileText className={cn("w-6 h-6", darkMode ? "text-green-400" : "text-green-600")} />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-gray-900")}>Get Support</h3>
                <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>Contact our support team</p>
              </div>
            </div>
          </Link>

          <div className={cn("p-6 rounded-2xl", darkMode ? "bg-gray-800" : "bg-white")}>
            <div className="flex items-center">
              <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center mr-4", darkMode ? "bg-orange-900/30" : "bg-orange-100")}>
                <Clock className={cn("w-6 h-6", darkMode ? "text-orange-400" : "text-orange-600")} />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-gray-900")}>Recent Activity</h3>
                <p className={cn("text-sm", darkMode ? "text-gray-300" : "text-gray-600")}>View your recent conversations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations Placeholder */}
        <div className={cn("p-6 rounded-2xl", darkMode ? "bg-gray-800" : "bg-white")}>
          <h2 className={cn("text-xl font-semibold mb-4", darkMode ? "text-white" : "text-gray-900")}>Recent Conversations</h2>
          <div className="text-center py-8">
            <MessageSquare className={cn("w-12 h-12 mx-auto mb-4", darkMode ? "text-gray-600" : "text-gray-400")} />
            <p className={cn("mb-4", darkMode ? "text-gray-400" : "text-gray-500")}>No conversations yet</p>
            <Link to="/chat" className="btn-primary btn-md inline-flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              Start Your First Conversation
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}