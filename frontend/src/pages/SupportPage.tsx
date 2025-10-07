import React from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'

export default function SupportPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Get Support
          </h1>
          <p className="text-xl text-gray-600">
            We're here to help with any questions or issues you may have
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="card p-6 text-center">
            <Mail className="w-8 h-8 text-primary-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Email Support</h3>
            <p className="text-gray-600 text-sm mb-4">
              Get help via email within 24 hours
            </p>
            <a
              href="mailto:support@pharmgpt.com"
              className="text-primary-600 hover:text-primary-500 font-medium"
            >
              support@pharmgpt.com
            </a>
          </div>

          <div className="card p-6 text-center">
            <MessageSquare className="w-8 h-8 text-primary-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Live Chat</h3>
            <p className="text-gray-600 text-sm mb-4">
              Chat with our support team
            </p>
            <button className="text-primary-600 hover:text-primary-500 font-medium">
              Start Chat
            </button>
          </div>

          <div className="card p-6 text-center">
            <Phone className="w-8 h-8 text-primary-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Phone Support</h3>
            <p className="text-gray-600 text-sm mb-4">
              Call us during business hours
            </p>
            <a
              href="tel:+1-555-PHARMGPT"
              className="text-primary-600 hover:text-primary-500 font-medium"
            >
              +1 (555) PHARM-GPT
            </a>
          </div>
        </div>

        {/* Support Form Placeholder */}
        <div className="card p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Send us a message</h2>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <p className="text-blue-700 mb-2">
              <strong>Support form coming soon!</strong>
            </p>
            <p className="text-blue-600 text-sm">
              The contact form will be implemented in the next phase. 
              For now, please use the email or phone contact methods above.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}