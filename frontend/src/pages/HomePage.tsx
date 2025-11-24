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
    <div className={cn(
      "min-h-screen relative",
      darkMode ? "dark bg-slate-950" : "bg-slate-50"
    )}>
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
              <div className="absolute -inset-4 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-full blur-2xl -z-10"></div>
            </div>
          </div>
          
          {/* Main Content */}
          <div className="text-center space-y-8 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-100 text-emerald-700 text-sm font-medium dark:bg-emerald-900/30 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
              AI-Powered Pharmaceutical Intelligence
            </div>
            
            <h1 className={cn(
              "text-5xl md:text-7xl font-bold tracking-tight",
              darkMode ? "text-white" : "text-slate-900"
            )}>
              Pharm<span className="gradient-text">GPT</span>
            </h1>
            
            <p className={cn(
              "text-lg md:text-xl max-w-2xl mx-auto leading-relaxed",
              darkMode ? "text-slate-300" : "text-slate-600"
            )}>
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
              <div className={cn(
                "inline-block px-4 py-3 rounded-xl animate-fade-in",
                darkMode 
                  ? "bg-slate-900/50 border border-slate-800" 
                  : "bg-white/50 border border-slate-200"
              )} style={{ animationDelay: '0.3s' }}>
                <p className={cn("text-sm", darkMode ? "text-slate-400" : "text-slate-600")}>
                  <span className="font-semibold">Demo:</span> admin@pharmgpt.com / admin123
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
            <div className={cn(
              "group p-8 rounded-2xl transition-all duration-300 hover:scale-[1.02] animate-fade-in",
              darkMode 
                ? "bg-slate-900/50 border border-slate-800 hover:border-emerald-500/50" 
                : "bg-white/50 border border-slate-200 hover:border-emerald-500/50 hover:shadow-xl"
            )} style={{ animationDelay: '0.4s' }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <h3 className={cn(
                "text-xl font-semibold mb-3",
                darkMode ? "text-white" : "text-slate-900"
              )}>
                Interactive Chat
              </h3>
              <p className={cn(
                "leading-relaxed",
                darkMode ? "text-slate-400" : "text-slate-600"
              )}>
                Natural conversations about pharmaceutical topics with context-aware AI responses
              </p>
            </div>

            {/* Feature 2 */}
            <div className={cn(
              "group p-8 rounded-2xl transition-all duration-300 hover:scale-[1.02] animate-fade-in",
              darkMode 
                ? "bg-slate-900/50 border border-slate-800 hover:border-emerald-500/50" 
                : "bg-white/50 border border-slate-200 hover:border-emerald-500/50 hover:shadow-xl"
            )} style={{ animationDelay: '0.5s' }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className={cn(
                "text-xl font-semibold mb-3",
                darkMode ? "text-white" : "text-slate-900"
              )}>
                Document Analysis
              </h3>
              <p className={cn(
                "leading-relaxed",
                darkMode ? "text-slate-400" : "text-slate-600"
              )}>
                Upload research papers and clinical documents for intelligent Q&A
              </p>
            </div>

            {/* Feature 3 */}
            <div className={cn(
              "group p-8 rounded-2xl transition-all duration-300 hover:scale-[1.02] animate-fade-in",
              darkMode 
                ? "bg-slate-900/50 border border-slate-800 hover:border-emerald-500/50" 
                : "bg-white/50 border border-slate-200 hover:border-emerald-500/50 hover:shadow-xl"
            )} style={{ animationDelay: '0.6s' }}>
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className={cn(
                "text-xl font-semibold mb-3",
                darkMode ? "text-white" : "text-slate-900"
              )}>
                Fast & Detailed Modes
              </h3>
              <p className={cn(
                "leading-relaxed",
                darkMode ? "text-slate-400" : "text-slate-600"
              )}>
                Choose between quick answers or comprehensive analysis for your queries
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
