import React from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function SupportPage() {
  const { darkMode } = useTheme()
  
  return (
    <div className={cn("min-h-screen py-12", darkMode ? "bg-[#212121]" : "bg-gray-50")}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className={cn("text-3xl font-bold mb-4", darkMode ? "text-white" : "text-gray-900")}>
            Get Support
          </h1>
          <p className={cn("text-xl", darkMode ? "text-gray-300" : "text-gray-600")}>
            We're here to help with any questions or issues you may have
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className={cn("p-6 text-center rounded-2xl shadow-sm", darkMode ? "bg-gray-800" : "bg-white")}>
            <Mail className={cn("w-8 h-8 mx-auto mb-4", darkMode ? "text-blue-400" : "text-primary-600")} />
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-gray-900")}>Email Support</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-gray-300" : "text-gray-600")}>
              Get help via email within 24 hours
            </p>
            <a
              href="mailto:support@pharmgpt.com"
              className={cn("font-medium", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}
            >
              support@pharmgpt.com
            </a>
          </div>

          <div className={cn("p-6 text-center rounded-2xl shadow-sm", darkMode ? "bg-gray-800" : "bg-white")}>
            <MessageSquare className={cn("w-8 h-8 mx-auto mb-4", darkMode ? "text-blue-400" : "text-primary-600")} />
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-gray-900")}>Live Chat</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-gray-300" : "text-gray-600")}>
              Chat with our support team
            </p>
            <button className={cn("font-medium", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}>
              Start Chat
            </button>
          </div>

          <div className={cn("p-6 text-center rounded-2xl shadow-sm", darkMode ? "bg-gray-800" : "bg-white")}>
            <Phone className={cn("w-8 h-8 mx-auto mb-4", darkMode ? "text-blue-400" : "text-primary-600")} />
            <h3 className={cn("text-lg font-semibold mb-2", darkMode ? "text-white" : "text-gray-900")}>Phone Support</h3>
            <p className={cn("text-sm mb-4", darkMode ? "text-gray-300" : "text-gray-600")}>
              Call us during business hours
            </p>
            <a
              href="tel:+1-555-PHARMGPT"
              className={cn("font-medium", darkMode ? "text-blue-400 hover:text-blue-300" : "text-primary-600 hover:text-primary-500")}
            >
              +1 (555) PHARM-GPT
            </a>
          </div>
        </div>

        {/* Support Form Placeholder */}
        <div className={cn("p-8 rounded-2xl shadow-sm", darkMode ? "bg-gray-800" : "bg-white")}>
          <h2 className={cn("text-2xl font-bold mb-6", darkMode ? "text-white" : "text-gray-900")}>Send us a message</h2>
          <div className={cn("rounded-lg p-6 border", darkMode ? "bg-blue-900/30 border-blue-800" : "bg-blue-50 border-blue-200")}>
            <p className={cn("mb-2", darkMode ? "text-blue-200" : "text-blue-700")}>
              <strong>Support form coming soon!</strong>
            </p>
            <p className={cn("text-sm", darkMode ? "text-blue-300" : "text-blue-600")}>
              The contact form will be implemented in the next phase. 
              For now, please use the email or phone contact methods above.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}