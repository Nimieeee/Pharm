import React from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function SupportPage() {
  const { darkMode } = useTheme()
  
  return (
    <div className={cn("min-h-screen py-12", darkMode ? "bg-slate-950" : "bg-slate-50")}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className={cn("text-3xl font-semibold mb-4", darkMode ? "text-white" : "text-slate-900")}>
            Get Support
          </h1>
          <p className={cn("text-xl", darkMode ? "text-slate-400" : "text-slate-600")}>
            We're here to help with any questions or issues you may have
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className={cn("p-6 text-center rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto mb-4">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-slate-900")}>Email Support</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-slate-400" : "text-slate-600")}>
              Get help via email within 24 hours
            </p>
            <a
              href="mailto:support@pharmgpt.com"
              className="font-medium text-emerald-500 hover:text-emerald-400 transition-colors"
            >
              support@pharmgpt.com
            </a>
          </div>

          <div className={cn("p-6 text-center rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-slate-900")}>Live Chat</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-slate-400" : "text-slate-600")}>
              Chat with our support team
            </p>
            <button className="font-medium text-emerald-500 hover:text-emerald-400 transition-colors">
              Start Chat
            </button>
          </div>

          <div className={cn("p-6 text-center rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
              <Phone className="w-6 h-6 text-white" />
            </div>
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-slate-900")}>Phone Support</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-slate-400" : "text-slate-600")}>
              Call us during business hours
            </p>
            <a
              href="tel:+1-555-PHARMGPT"
              className="font-medium text-emerald-500 hover:text-emerald-400 transition-colors"
            >
              +1 (555) PHARM-GPT
            </a>
          </div>
        </div>

        {/* Support Form Placeholder */}
        <div className={cn("p-8 rounded-2xl border", darkMode ? "bg-slate-900/50 border-slate-800" : "bg-white/50 border-slate-200")}>
          <h2 className={cn("text-2xl font-semibold mb-6", darkMode ? "text-white" : "text-slate-900")}>Send us a message</h2>
          <div className={cn("rounded-xl p-6 border", darkMode ? "bg-blue-500/10 border-blue-500/20" : "bg-blue-50 border-blue-200")}>
            <p className={cn("mb-2 font-medium", darkMode ? "text-blue-300" : "text-blue-700")}>
              Support form coming soon!
            </p>
            <p className={cn("text-sm", darkMode ? "text-blue-400" : "text-blue-600")}>
              The contact form will be implemented in the next phase. 
              For now, please use the email or phone contact methods above.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}