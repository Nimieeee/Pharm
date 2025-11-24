import React from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function SupportPage() {
  const { darkMode } = useTheme()
  
  return (
    <div className="min-h-screen py-12 bg-surface-primary">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-medium mb-4 text-content-primary">
            Get Support
          </h1>
          <p className="text-xl text-content-secondary">
            We're here to help with any questions or issues you may have
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="p-6 text-center rounded-gemini border border-surface bg-surface-secondary shadow-gemini">
            <div className="w-12 h-12 rounded-xl bg-gemini-gradient flex items-center justify-center mx-auto mb-4">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-medium mb-2 text-content-primary">Email Support</h3>
            <p className="text-sm mb-4 text-content-secondary">
              Get help via email within 24 hours
            </p>
            <a
              href="mailto:support@pharmgpt.com"
              className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity"
            >
              support@pharmgpt.com
            </a>
          </div>

          <div className="p-6 text-center rounded-gemini border border-surface bg-surface-secondary shadow-gemini">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-medium mb-2 text-content-primary">Live Chat</h3>
            <p className="text-sm mb-4 text-content-secondary">
              Chat with our support team
            </p>
            <button className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity touch-target">
              Start Chat
            </button>
          </div>

          <div className="p-6 text-center rounded-gemini border border-surface bg-surface-secondary shadow-gemini">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
              <Phone className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-lg font-medium mb-2 text-content-primary">Phone Support</h3>
            <p className="text-sm mb-4 text-content-secondary">
              Call us during business hours
            </p>
            <a
              href="tel:+1-555-PHARMGPT"
              className="font-medium text-gemini-gradient-start hover:opacity-80 transition-opacity"
            >
              +1 (555) PHARM-GPT
            </a>
          </div>
        </div>

        {/* Support Form Placeholder */}
        <div className="p-8 rounded-gemini border border-surface bg-surface-secondary shadow-gemini">
          <h2 className="text-2xl font-medium mb-6 text-content-primary">Send us a message</h2>
          <div className="rounded-gemini p-6 border border-surface bg-surface-tertiary">
            <p className="mb-2 font-medium text-content-primary">
              Support form coming soon!
            </p>
            <p className="text-sm text-content-secondary">
              The contact form will be implemented in the next phase. 
              For now, please use the email or phone contact methods above.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}