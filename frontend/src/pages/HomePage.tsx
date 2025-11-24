import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, MessageSquare, FileText, Zap } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Hero Section - Orchestrated Animation */}
      <section className="section-spacing">
        <div className="container-spa">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            
            {/* Logo - First to appear */}
            <div className="flex justify-center mb-8 animate-fade-in">
              <div className="relative">
                <img 
                  src="/PharmGPT.png" 
                  alt="PharmGPT" 
                  className="w-20 h-20" 
                />
              </div>
            </div>
            
            {/* Headline - Second */}
            <div className="space-y-6 animate-fade-in-delay">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif font-semibold text-balance" 
                  style={{ 
                    color: 'var(--text-primary)',
                    fontFamily: "'Cormorant Garamond', Georgia, serif"
                  }}>
                Pharmaceutical Intelligence,
                <br />
                <span style={{ color: 'var(--accent)' }}>Reimagined</span>
              </h1>
              
              <p className="text-lg md:text-xl max-w-2xl mx-auto leading-relaxed" 
                 style={{ color: 'var(--text-secondary)' }}>
                Advanced AI assistant for pharmacology research. Get instant insights on drug interactions, 
                mechanisms of action, and clinical applications.
              </p>
            </div>
            
            {/* CTA - Third */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-fade-in-delay-2">
              {isAuthenticated ? (
                <Link to="/chat" className="btn-spa btn-primary group">
                  <span>Open Chat</span>
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn-spa btn-primary group">
                    <span>Get Started</span>
                    <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                  </Link>
                  <Link to="/login" className="btn-spa btn-secondary">
                    <span>Sign In</span>
                  </Link>
                </>
              )}
            </div>

            {/* Demo credentials */}
            {!isAuthenticated && (
              <div className="inline-block px-6 py-3 rounded-spa animate-fade-in-delay-2" 
                   style={{ 
                     background: 'var(--bg-secondary)', 
                     border: '1px solid var(--border)' 
                   }}>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>Demo:</span> admin@pharmgpt.com / admin123
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Grid - Perfect Spacing */}
      <section className="pb-24 md:pb-32">
        <div className="container-spa">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            
            {/* Feature 1 */}
            <div className="card-spa group">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6 transition-transform group-hover:scale-110" 
                   style={{ background: 'var(--accent)' }}>
                <MessageSquare size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                Interactive Chat
              </h3>
              <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                Natural conversations about pharmaceutical topics with context-aware AI responses
              </p>
            </div>

            {/* Feature 2 */}
            <div className="card-spa group">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6 transition-transform group-hover:scale-110" 
                   style={{ background: 'var(--success)' }}>
                <FileText size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                Document Analysis
              </h3>
              <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                Upload research papers and clinical documents for intelligent Q&A
              </p>
            </div>

            {/* Feature 3 */}
            <div className="card-spa group">
              <div className="w-12 h-12 rounded-spa flex items-center justify-center mb-6 transition-transform group-hover:scale-110" 
                   style={{ background: 'var(--accent)' }}>
                <Zap size={24} style={{ color: 'var(--bg-primary)' }} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                Fast & Detailed Modes
              </h3>
              <p className="leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                Choose between quick answers or comprehensive analysis for your queries
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
