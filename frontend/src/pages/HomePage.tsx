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
      "min-h-screen relative",
      darkMode 
        ? "dark bg-[#1a1a1a] text-white" 
        : "bg-white text-neutral-900"
    )}>
      {/* Brutalist grid background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 50px, currentColor 50px, currentColor 51px), repeating-linear-gradient(90deg, transparent, transparent 50px, currentColor 50px, currentColor 51px)'
        }} />
      </div>

      {/* Hero Section */}
      <section className="relative pt-16 pb-24 px-4">
        <div className="max-w-6xl mx-auto">
          {/* Header stamp */}
          <div className="mb-12 animate-stamp">
            <div className="inline-block">
              <div className={cn(
                "px-6 py-3 border-4 transform -rotate-3 font-bold uppercase tracking-widest text-sm",
                darkMode ? "border-primary-500 text-primary-500" : "border-primary-600 text-primary-600"
              )}>
                Pharmaceutical AI System
              </div>
            </div>
          </div>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <h1 className={cn(
                "text-7xl md:text-8xl font-display font-black leading-none animate-fade-in",
                darkMode ? "text-white" : "text-neutral-900"
              )} style={{ animationDelay: '0.1s' }}>
                Pharm<span className="text-accent-600">GPT</span>
              </h1>
              
              <div className={cn(
                "border-l-4 pl-6 animate-fade-in",
                darkMode ? "border-white" : "border-neutral-900"
              )} style={{ animationDelay: '0.2s' }}>
                <p className="text-lg md:text-xl font-sans leading-relaxed">
                  Advanced pharmacology intelligence system. Query drug interactions, 
                  mechanisms of action, and clinical applications with precision.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 animate-fade-in" style={{ animationDelay: '0.3s' }}>
                {isAuthenticated ? (
                  <Link
                    to="/chat"
                    className="btn-primary btn-lg group"
                  >
                    Access System
                    <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </Link>
                ) : (
                  <>
                    <Link
                      to="/register"
                      className="btn-primary btn-lg group"
                    >
                      Initialize
                      <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </Link>
                    <Link
                      to="/login"
                      className="btn-outline btn-lg"
                    >
                      Login
                    </Link>
                  </>
                )}
              </div>

              {/* Demo credentials */}
              {!isAuthenticated && (
                <div className={cn(
                  "inline-block p-4 border-3 animate-fade-in",
                  darkMode ? "border-neutral-700 bg-neutral-800" : "border-neutral-300 bg-neutral-50"
                )} style={{ animationDelay: '0.4s' }}>
                  <p className="text-xs font-sans uppercase tracking-wider">
                    <span className="font-bold">Test Access:</span> admin@pharmgpt.com / admin123
                  </p>
                </div>
              )}
            </div>

            {/* Right side - Feature blocks */}
            <div className="space-y-4">
              <div className={cn(
                "p-6 border-4 animate-slide-in-right",
                darkMode ? "border-white bg-neutral-900" : "border-neutral-900 bg-white"
              )} style={{ animationDelay: '0.2s' }}>
                <div className="label mb-3">01</div>
                <h3 className="text-2xl font-display font-bold mb-2">Document Processing</h3>
                <p className="font-sans text-sm">PDF, DOCX, XLSX, SDF, TXT, PPTX support with intelligent extraction</p>
              </div>

              <div className={cn(
                "p-6 border-4 animate-slide-in-right",
                darkMode ? "border-white bg-neutral-900" : "border-neutral-900 bg-white"
              )} style={{ animationDelay: '0.3s' }}>
                <div className="label mb-3">02</div>
                <h3 className="text-2xl font-display font-bold mb-2">RAG Architecture</h3>
                <p className="font-sans text-sm">Context-aware responses powered by retrieval-augmented generation</p>
              </div>

              <div className={cn(
                "p-6 border-4 animate-slide-in-right",
                darkMode ? "border-white bg-neutral-900" : "border-neutral-900 bg-white"
              )} style={{ animationDelay: '0.4s' }}>
                <div className="label mb-3">03</div>
                <h3 className="text-2xl font-display font-bold mb-2">Dual Mode Operation</h3>
                <p className="font-sans text-sm">Fast responses or detailed analysis - optimized for your workflow</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities Grid */}
      <section className="relative pb-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className={cn(
            "mb-12 pb-6 border-b-4",
            darkMode ? "border-white" : "border-neutral-900"
          )}>
            <h2 className="text-4xl md:text-5xl font-display font-black">
              System Capabilities
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className={cn(
              "p-8 border-4 transition-all duration-200 hover:translate-x-1 hover:translate-y-1 animate-fade-in",
              darkMode 
                ? "border-white bg-neutral-900 shadow-[8px_8px_0px_0px_rgba(255,255,255,1)] hover:shadow-[4px_4px_0px_0px_rgba(255,255,255,1)]" 
                : "border-neutral-900 bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
            )} style={{ animationDelay: '0.5s' }}>
              <MessageSquare className="w-12 h-12 mb-4" />
              <h3 className="text-2xl font-display font-bold mb-3">
                Interactive Query
              </h3>
              <p className="font-sans text-sm leading-relaxed">
                Natural language processing for pharmaceutical inquiries with contextual understanding
              </p>
            </div>

            <div className={cn(
              "p-8 border-4 transition-all duration-200 hover:translate-x-1 hover:translate-y-1 animate-fade-in",
              darkMode 
                ? "border-white bg-neutral-900 shadow-[8px_8px_0px_0px_rgba(255,255,255,1)] hover:shadow-[4px_4px_0px_0px_rgba(255,255,255,1)]" 
                : "border-neutral-900 bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
            )} style={{ animationDelay: '0.6s' }}>
              <FileText className="w-12 h-12 mb-4" />
              <h3 className="text-2xl font-display font-bold mb-3">
                Multi-Format Ingestion
              </h3>
              <p className="font-sans text-sm leading-relaxed">
                Process research papers, clinical data, and molecular structures across multiple file formats
              </p>
            </div>

            <div className={cn(
              "p-8 border-4 transition-all duration-200 hover:translate-x-1 hover:translate-y-1 animate-fade-in",
              darkMode 
                ? "border-white bg-neutral-900 shadow-[8px_8px_0px_0px_rgba(255,255,255,1)] hover:shadow-[4px_4px_0px_0px_rgba(255,255,255,1)]" 
                : "border-neutral-900 bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
            )} style={{ animationDelay: '0.7s' }}>
              <Zap className="w-12 h-12 mb-4" />
              <h3 className="text-2xl font-display font-bold mb-3">
                Adaptive Processing
              </h3>
              <p className="font-sans text-sm leading-relaxed">
                Toggle between rapid response and comprehensive analysis modes based on query complexity
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}