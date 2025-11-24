import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, MessageSquare, FileText, Zap } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'

export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const { darkMode } = useTheme()

  return (
    <div className={cn(
      "min-h-screen relative overflow-hidden",
      darkMode 
        ? "dark bg-[#0a1f1c] text-teal-50" 
        : "bg-white"
    )}>
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={cn(
          "absolute inset-0",
          darkMode 
            ? "bg-gradient-to-br from-teal-950 via-[#0a1f1c] to-teal-900" 
            : "bg-gradient-to-br from-teal-50 via-white to-accent-50"
        )} />
        <div className={cn(
          "absolute inset-0 bg-grid-pattern bg-grid opacity-30",
          darkMode ? "opacity-20" : "opacity-30"
        )} />
        <div className="absolute top-20 left-10 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '0s' }} />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      {/* Hero Section */}
      <section className="relative pt-24 pb-40 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="mb-10 animate-fade-in">
            <img 
              src="/PharmGPT.png" 
              alt="PharmGPT" 
              className="w-24 h-24 mx-auto mb-8 drop-shadow-2xl animate-float" 
            />
          </div>
          
          <h1 className={cn(
            "text-6xl md:text-8xl font-display font-black mb-8 animate-fade-in",
            darkMode ? "text-teal-50" : "text-teal-900"
          )} style={{ animationDelay: '0.1s' }}>
            PharmGPT
          </h1>
          
          <p className={cn(
            "text-lg md:text-xl mb-14 max-w-3xl mx-auto leading-relaxed animate-fade-in",
            darkMode ? "text-teal-200" : "text-teal-800"
          )} style={{ animationDelay: '0.2s' }}>
            Your AI-powered pharmacology assistant. Get expert insights on drug interactions, 
            mechanisms of action, and clinical applications—backed by cutting-edge research.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-5 justify-center mb-16 animate-fade-in" style={{ animationDelay: '0.3s' }}>
            {isAuthenticated ? (
              <Link
                to="/chat"
                className="group inline-flex items-center justify-center px-10 py-5 text-lg font-semibold text-white bg-gradient-to-r from-teal-600 to-teal-500 rounded-2xl hover:from-teal-700 hover:to-teal-600 transition-all duration-300 shadow-2xl shadow-teal-500/40 hover:shadow-teal-500/60 hover:scale-105"
              >
                Open Chat
                <ArrowRight className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="group inline-flex items-center justify-center px-10 py-5 text-lg font-semibold text-white bg-gradient-to-r from-teal-600 to-teal-500 rounded-2xl hover:from-teal-700 hover:to-teal-600 transition-all duration-300 shadow-2xl shadow-teal-500/40 hover:shadow-teal-500/60 hover:scale-105"
                >
                  Get Started
                  <ArrowRight className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/login"
                  className={cn(
                    "inline-flex items-center justify-center px-10 py-5 text-lg font-semibold rounded-2xl border-2 transition-all duration-300 hover:scale-105", 
                    darkMode 
                      ? "text-teal-300 bg-teal-950/50 border-teal-600 hover:bg-teal-950 hover:border-teal-500 shadow-xl shadow-teal-900/30" 
                      : "text-teal-700 bg-white border-teal-400 hover:bg-teal-50 hover:border-teal-500 shadow-xl shadow-teal-500/20"
                  )}
                >
                  Sign In
                </Link>
              </>
            )}
          </div>

          {/* Demo credentials */}
          {!isAuthenticated && (
            <div className={cn(
              "inline-block p-5 rounded-2xl border-2 backdrop-blur-sm animate-fade-in",
              darkMode 
                ? "bg-teal-950/50 border-teal-700 shadow-xl shadow-teal-900/30" 
                : "bg-teal-50/80 border-teal-300 shadow-xl shadow-teal-500/20"
            )} style={{ animationDelay: '0.4s' }}>
              <p className={cn("text-sm font-medium", darkMode ? "text-teal-200" : "text-teal-900")}>
                <strong className="font-bold">Demo:</strong> admin@pharmgpt.com / admin123
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="relative pb-32 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className={cn(
              "group text-center p-10 rounded-3xl border-2 transition-all duration-500 hover:scale-105 animate-fade-in backdrop-blur-sm",
              darkMode 
                ? "bg-teal-950/40 border-teal-800 hover:border-teal-600 shadow-2xl shadow-teal-900/30 hover:shadow-teal-700/40" 
                : "bg-white/80 border-teal-200 hover:border-teal-400 shadow-2xl shadow-teal-500/20 hover:shadow-teal-500/30"
            )} style={{ animationDelay: '0.5s' }}>
              <div className={cn(
                "w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6",
                darkMode ? "bg-teal-900/50" : "bg-teal-100"
              )}>
                <MessageSquare className={cn("w-10 h-10", darkMode ? "text-teal-400" : "text-teal-600")} />
              </div>
              <h3 className={cn("text-2xl font-display font-bold mb-4", darkMode ? "text-teal-50" : "text-teal-900")}>
                Interactive Chat
              </h3>
              <p className={cn("leading-relaxed", darkMode ? "text-teal-300" : "text-teal-700")}>
                Natural conversations about pharmaceutical topics with context-aware AI responses
              </p>
            </div>

            <div className={cn(
              "group text-center p-10 rounded-3xl border-2 transition-all duration-500 hover:scale-105 animate-fade-in backdrop-blur-sm",
              darkMode 
                ? "bg-teal-950/40 border-teal-800 hover:border-teal-600 shadow-2xl shadow-teal-900/30 hover:shadow-teal-700/40" 
                : "bg-white/80 border-teal-200 hover:border-teal-400 shadow-2xl shadow-teal-500/20 hover:shadow-teal-500/30"
            )} style={{ animationDelay: '0.6s' }}>
              <div className={cn(
                "w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6",
                darkMode ? "bg-accent-900/50" : "bg-accent-100"
              )}>
                <FileText className={cn("w-10 h-10", darkMode ? "text-accent-400" : "text-accent-600")} />
              </div>
              <h3 className={cn("text-2xl font-display font-bold mb-4", darkMode ? "text-teal-50" : "text-teal-900")}>
                Document Analysis
              </h3>
              <p className={cn("leading-relaxed", darkMode ? "text-teal-300" : "text-teal-700")}>
                Upload research papers and clinical documents for intelligent Q&A
              </p>
            </div>

            <div className={cn(
              "group text-center p-10 rounded-3xl border-2 transition-all duration-500 hover:scale-105 animate-fade-in backdrop-blur-sm",
              darkMode 
                ? "bg-teal-950/40 border-teal-800 hover:border-teal-600 shadow-2xl shadow-teal-900/30 hover:shadow-teal-700/40" 
                : "bg-white/80 border-teal-200 hover:border-teal-400 shadow-2xl shadow-teal-500/20 hover:shadow-teal-500/30"
            )} style={{ animationDelay: '0.7s' }}>
              <div className={cn(
                "w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6 transition-all duration-500 group-hover:scale-110 group-hover:rotate-6",
                darkMode ? "bg-teal-900/50" : "bg-teal-100"
              )}>
                <Zap className={cn("w-10 h-10", darkMode ? "text-teal-400" : "text-teal-600")} />
              </div>
              <h3 className={cn("text-2xl font-display font-bold mb-4", darkMode ? "text-teal-50" : "text-teal-900")}>
                Fast & Detailed Modes
              </h3>
              <p className={cn("leading-relaxed", darkMode ? "text-teal-300" : "text-teal-700")}>
                Choose between quick answers or comprehensive analysis for your queries
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}