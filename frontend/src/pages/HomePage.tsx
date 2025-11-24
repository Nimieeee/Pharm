import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, MessageSquare, FileText, Zap, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const { darkMode } = useTheme()

  return (
    <div className="min-h-screen relative bg-surface-primary">
      {/* Hero Section */}
      <section className="relative pt-20 pb-32 px-4 overflow-hidden">
        <div className="max-w-6xl mx-auto">
          {/* Logo */}
          <div className="flex justify-center mb-12 animate-fade-in">
            <div className="relative">
              <img 
                src="/PharmGPT.png" 
                alt="PharmGPT" 
                className="w-16 h-16 drop-shadow-lg" 
              />
              <div className="absolute -inset-4 bg-gemini-gradient opacity-20 rounded-full blur-2xl -z-10"></div>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="text-center space-y-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-gemini-full bg-surface-secondary text-content-primary text-sm font-medium border border-surface">
              <Sparkles className="w-4 h-4 text-gemini-gradient" />
              AI-Powered Pharmaceutical Intelligence
            </div>
            
            <h1 className="text-5xl md:text-7xl font-medium tracking-tight text-content-primary">
              Pharm<span className="text-gemini-gradient">GPT</span>
            </h1>
            
            <p className="text-lg md:text-xl max-w-2xl mx-auto leading-relaxed text-content-secondary">
              Advanced AI assistant for pharmacology research. Get instant insights on drug interactions, 
              mechanisms of action, and clinical applications.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              {isAuthenticated ? (
                <Link
                  to="/chat"
                  className="btn-primary btn-lg group"
                >
                  Open Chat
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    className="btn-primary btn-lg group"
                  >
                    Get Started
                    <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </Link>
                  <Link
                    to="/login"
                    className="btn-outline btn-lg"
                  >
                    Sign In
                  </Link>
                </>
              )}
            </div>

            {/* Demo credentials */}
            {!isAuthenticated && (
              <div className="inline-block px-4 py-3 rounded-gemini animate-fade-in bg-surface-secondary border border-surface" style={{ animationDelay: '0.3s' }}>
                <p className="text-sm text-content-secondary">
                  <span className="font-medium text-content-primary">Demo:</span> admin@pharmgpt.com / admin123
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative pb-32 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="group p-8 rounded-gemini transition-all duration-300 hover:scale-[1.02] animate-fade-in bg-surface-secondary border border-surface shadow-gemini hover:shadow-gemini-lg" style={{ animationDelay: '0.4s' }}>
              <div className="w-12 h-12 rounded-xl bg-gemini-gradient flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-medium mb-3 text-content-primary">
                Interactive Chat
              </h3>
              <p className="leading-relaxed text-content-secondary">
                Natural conversations about pharmaceutical topics with context-aware AI responses
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group p-8 rounded-gemini transition-all duration-300 hover:scale-[1.02] animate-fade-in bg-surface-secondary border border-surface shadow-gemini hover:shadow-gemini-lg" style={{ animationDelay: '0.5s' }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-medium mb-3 text-content-primary">
                Document Analysis
              </h3>
              <p className="leading-relaxed text-content-secondary">
                Upload research papers and clinical documents for intelligent Q&A
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group p-8 rounded-gemini transition-all duration-300 hover:scale-[1.02] animate-fade-in bg-surface-secondary border border-surface shadow-gemini hover:shadow-gemini-lg" style={{ animationDelay: '0.6s' }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-medium mb-3 text-content-primary">
                Fast & Detailed Modes
              </h3>
              <p className="leading-relaxed text-content-secondary">
                Choose between quick answers or comprehensive analysis for your queries
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
