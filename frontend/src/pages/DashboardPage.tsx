import React from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, FileText, Clock, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.first_name || 'User'}!
          </h1>
          <p className="text-gray-600 mt-2">
            Continue your pharmaceutical research and conversations
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link
            to="/chat"
            className="card p-6 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mr-4">
                <MessageSquare className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Start New Chat</h3>
                <p className="text-gray-600 text-sm">Begin a new conversation</p>
              </div>
            </div>
          </Link>

          <Link
            to="/support"
            className="card p-6 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                <FileText className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Get Support</h3>
                <p className="text-gray-600 text-sm">Contact our support team</p>
              </div>
            </div>
          </Link>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mr-4">
                <Clock className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                <p className="text-gray-600 text-sm">View your recent conversations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations Placeholder */}
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Conversations</h2>
          <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No conversations yet</p>
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