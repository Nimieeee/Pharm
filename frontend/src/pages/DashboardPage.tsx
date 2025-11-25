import React from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, FileText, Clock, Plus } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="section-spacing">
        <div className="container-spa">
          {/* Header */}
          <div className="mb-12 animate-fade-in">
            <h1 className="text-3xl md:text-4xl font-semibold mb-3" 
                style={{ 
                  color: 'var(--text-primary)'
                }}>
              Welcome back, {user?.first_name || 'User'}
            </h1>
            <p className="text-lg" style={{ color: 'var(--text-secondary)' }}>
              Continue your pharmaceutical research and conversations
            </p>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-fade-in-delay">
            <Link to="/chat" className="card-spa group">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6 transition-transform group-hover:scale-110" 
                   style={{ background: 'var(--accent)' }}>
                <MessageSquare size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Start New Chat
              </h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Begin a new conversation
              </p>
            </Link>

            <Link to="/support" className="card-spa group">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6 transition-transform group-hover:scale-110" 
                   style={{ background: 'var(--success)' }}>
                <FileText size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Get Support
              </h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Contact our support team
              </p>
            </Link>

            <div className="card-spa">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6" 
                   style={{ background: 'var(--accent)' }}>
                <Clock size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Recent Activity
              </h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                View your recent conversations
              </p>
            </div>
          </div>

          {/* Recent Conversations */}
          <div className="card-spa animate-fade-in-delay-2">
            <h2 className="text-2xl font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>
              Recent Conversations
            </h2>
            <div className="text-center py-12">
              <MessageSquare size={48} className="mx-auto mb-4" style={{ color: 'var(--text-tertiary)' }} strokeWidth={2} />
              <p className="mb-6" style={{ color: 'var(--text-secondary)' }}>
                No conversations yet
              </p>
              <Link to="/chat" className="btn-spa btn-primary">
                <Plus size={20} strokeWidth={2} />
                <span>Start Your First Conversation</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
