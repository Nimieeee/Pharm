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
    <div className="min-h-screen py-8 bg-surface-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-medium text-content-primary">
            Welcome back, {user?.first_name || 'User'}!
          </h1>
          <p className="mt-2 text-content-secondary">
            Continue your pharmaceutical research and conversations
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link
            to="/chat"
            className="p-6 rounded-gemini border border-surface hover:shadow-gemini-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer bg-surface-secondary touch-target"
          >
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gemini-gradient flex items-center justify-center mr-4">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-content-primary">Start New Chat</h3>
                <p className="text-sm text-content-secondary">Begin a new conversation</p>
              </div>
            </div>
          </Link>

          <Link
            to="/support"
            className="p-6 rounded-gemini border border-surface hover:shadow-gemini-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer bg-surface-secondary touch-target"
          >
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mr-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-content-primary">Get Support</h3>
                <p className="text-sm text-content-secondary">Contact our support team</p>
              </div>
            </div>
          </Link>

          <div className="p-6 rounded-gemini border border-surface bg-surface-secondary">
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mr-4">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-content-primary">Recent Activity</h3>
                <p className="text-sm text-content-secondary">View your recent conversations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations Placeholder */}
        <div className="p-6 rounded-gemini border border-surface bg-surface-secondary shadow-gemini">
          <h2 className="text-xl font-medium mb-4 text-content-primary">Recent Conversations</h2>
          <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-content-tertiary" />
            <p className="mb-4 text-content-secondary">No conversations yet</p>
            <Link to="/chat" className="inline-flex items-center px-6 py-3 rounded-gemini-full bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target">
              <Plus className="w-4 h-4 mr-2" />
              Start Your First Conversation
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}