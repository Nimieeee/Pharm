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
    <div className={cn("min-h-screen py-8", darkMode ? "bg-slate-950" : "bg-slate-50")}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className={cn("text-3xl font-semibold", darkMode ? "text-white" : "text-slate-900")}>
            Welcome back, {user?.first_name || 'User'}!
          </h1>
          <p className={cn("mt-2", darkMode ? "text-slate-400" : "text-slate-600")}>
            Continue your pharmaceutical research and conversations
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link
            to="/chat"
            className={cn("p-6 rounded-2xl border hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer", darkMode ? "bg-slate-900/50 border-slate-800 hover:border-emerald-500/50" : "bg-white/50 border-slate-200 hover:border-emerald-500/50")}
          >
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mr-4">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-slate-900")}>Start New Chat</h3>
                <p className={cn("text-sm", darkMode ? "text-slate-400" : "text-slate-600")}>Begin a new conversation</p>
              </div>
            </div>
          </Link>

          <Link
            to="/support"
            className={cn("p-6 rounded-2xl border hover:shadow-lg transition-all duration-300 hover:scale-[1.02] cursor-pointer", darkMode ? "bg-slate-900/50 border-slate-800 hover:border-emerald-500/50" : "bg-white/50 border-slate-200 hover:border-emerald-500/50")}
          >
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mr-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-slate-900")}>Get Support</h3>
                <p className={cn("text-sm", darkMode ? "text-slate-400" : "text-slate-600")}>Contact our support team</p>
              </div>
            </div>
          </Link>

          <div className={cn("p-6 rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mr-4">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className={cn("text-lg font-semibold", darkMode ? "text-white" : "text-slate-900")}>Recent Activity</h3>
                <p className={cn("text-sm", darkMode ? "text-slate-400" : "text-slate-600")}>View your recent conversations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations Placeholder */}
        <div className={cn("p-6 rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
          <h2 className={cn("text-xl font-semibold mb-4", darkMode ? "text-white" : "text-slate-900")}>Recent Conversations</h2>
          <div className="text-center py-8">
            <MessageSquare className={cn("w-12 h-12 mx-auto mb-4", darkMode ? "text-slate-600" : "text-slate-400")} />
            <p className={cn("mb-4", darkMode ? "text-slate-400" : "text-slate-500")}>No conversations yet</p>
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