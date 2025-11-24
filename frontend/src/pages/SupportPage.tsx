import React from 'react'
import { Mail, MessageSquare, Phone } from 'lucide-react'

export default function SupportPage() {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="section-spacing">
        <div className="container-spa max-w-4xl">
          {/* Header */}
          <div className="text-center mb-16 animate-fade-in">
            <h1 className="text-4xl md:text-5xl font-semibold mb-4" 
                style={{ 
                  color: 'var(--text-primary)',
                  fontFamily: "'Cormorant Garamond', Georgia, serif"
                }}>
              Get Support
            </h1>
            <p className="text-xl" style={{ color: 'var(--text-secondary)' }}>
              We're here to help with any questions or issues
            </p>
          </div>

          {/* Contact Methods */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-fade-in-delay">
            <div className="card-spa text-center">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mx-auto mb-6" 
                   style={{ background: 'var(--accent)' }}>
                <Mail size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Email Support
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                Get help via email within 24 hours
              </p>
              <a
                href="mailto:support@pharmgpt.com"
                className="font-medium transition-spa"
                style={{ color: 'var(--accent)' }}
              >
                support@pharmgpt.com
              </a>
            </div>

            <div className="card-spa text-center">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mx-auto mb-6" 
                   style={{ background: 'var(--success)' }}>
                <MessageSquare size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Live Chat
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                Chat with our support team
              </p>
              <button className="font-medium transition-spa" style={{ color: 'var(--accent)' }}>
                Start Chat
              </button>
            </div>

            <div className="card-spa text-center">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mx-auto mb-6" 
                   style={{ background: 'var(--accent)' }}>
                <Phone size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                Phone Support
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
                Call us during business hours
              </p>
              <a
                href="tel:+1-555-PHARMGPT"
                className="font-medium transition-spa"
                style={{ color: 'var(--accent)' }}
              >
                +1 (555) PHARM-GPT
              </a>
            </div>
          </div>

          {/* Contact Form Placeholder */}
          <div className="card-spa animate-fade-in-delay-2">
            <h2 className="text-2xl font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>
              Send us a message
            </h2>
            <div className="p-6 rounded-spa" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border)' }}>
              <p className="mb-2 font-semibold" style={{ color: 'var(--text-primary)' }}>
                Support form coming soon
              </p>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                For now, please use the email or phone contact methods above.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
