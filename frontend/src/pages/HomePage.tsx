import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, MessageSquare, FileText, Zap } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { isAuthenticated, user } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-8">
            <img src="/PharmGPT.png" alt="PharmGPT" className="w-20 h-20 mx-auto mb-6" />
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6">
            PharmGPT
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Your AI-powered pharmacology assistant. Get expert insights on drug interactions, 
            mechanisms of action, and clinical applications.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            {isAuthenticated ? (
              <Link
                to="/chat"
                className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-blue-600 rounded-full hover:bg-blue-700 transition-colors"
              >
                Open Chat
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white bg-blue-600 rounded-full hover:bg-blue-700 transition-colors"
                >
                  Get Started
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-gray-700 bg-white border-2 border-gray-300 rounded-full hover:border-gray-400 transition-colors"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>

          {/* Demo credentials */}
          {!isAuthenticated && (
            <div className="inline-block p-4 bg-blue-50 rounded-2xl border border-blue-200">
              <p className="text-sm text-blue-900">
                <strong>Demo:</strong> admin@pharmgpt.com / admin123
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="pb-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-8 bg-white rounded-3xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Interactive Chat
              </h3>
              <p className="text-gray-600">
                Natural conversations about pharmaceutical topics with context-aware AI responses
              </p>
            </div>

            <div className="text-center p-8 bg-white rounded-3xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <FileText className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Document Analysis
              </h3>
              <p className="text-gray-600">
                Upload research papers and clinical documents for intelligent Q&A
              </p>
            </div>

            <div className="text-center p-8 bg-white rounded-3xl shadow-sm hover:shadow-md transition-shadow">
              <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Fast & Detailed Modes
              </h3>
              <p className="text-gray-600">
                Choose between quick answers or comprehensive analysis for your queries
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}