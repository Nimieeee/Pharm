import React from 'react'
import { Link } from 'react-router-dom'
import { 
  Brain, 
  FileText, 
  MessageSquare, 
  Shield, 
  Zap, 
  Users,
  ArrowRight,
  CheckCircle,
  Star
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const { isAuthenticated, user } = useAuth()

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced AI models specialized in pharmacology provide expert-level insights on drug interactions and mechanisms.'
    },
    {
      icon: FileText,
      title: 'Document Intelligence',
      description: 'Upload research papers, clinical protocols, and regulatory documents for intelligent analysis and Q&A.'
    },
    {
      icon: MessageSquare,
      title: 'Interactive Chat',
      description: 'Engage in natural conversations about pharmaceutical topics with context-aware responses.'
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Your conversations and documents are completely private and isolated from other users.'
    },
    {
      icon: Zap,
      title: 'Fast Responses',
      description: 'Choose between fast responses for quick queries or detailed analysis for complex questions.'
    },
    {
      icon: Users,
      title: 'Multi-User Support',
      description: 'Individual user accounts with separate conversation histories and document libraries.'
    }
  ]

  const useCases = [
    {
      title: 'Pharmaceutical Research',
      items: [
        'Drug interaction analysis',
        'Mechanism of action explanations',
        'Clinical trial information',
        'Regulatory guidance'
      ]
    },
    {
      title: 'Medical Education',
      items: [
        'Pharmacokinetics and pharmacodynamics',
        'Therapeutic classifications',
        'Adverse effect profiles',
        'Dosing guidelines'
      ]
    },
    {
      title: 'Document Analysis',
      items: [
        'Research paper analysis',
        'Clinical protocol review',
        'Regulatory document processing',
        'Literature synthesis'
      ]
    }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-secondary-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              AI-Powered
              <span className="text-primary-600 block">Pharmacology Assistant</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Get expert-level insights on drug interactions, mechanisms of action, and clinical applications. 
              Upload documents, ask questions, and receive intelligent responses powered by advanced AI.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {isAuthenticated ? (
                <Link
                  to={user?.is_admin ? '/admin' : '/dashboard'}
                  className="btn-primary btn-lg inline-flex items-center"
                >
                  Go to Dashboard
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    className="btn-primary btn-lg inline-flex items-center"
                  >
                    Get Started Free
                    <ArrowRight className="ml-2 w-5 h-5" />
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

            {/* Demo credentials for testing */}
            {!isAuthenticated && (
              <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200 max-w-md mx-auto">
                <h3 className="text-sm font-medium text-blue-900 mb-2">Try Demo Account</h3>
                <p className="text-xs text-blue-700">
                  <strong>Admin:</strong> admin@pharmgpt.com / admin123
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features for Pharmaceutical Excellence
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to accelerate your pharmaceutical research and education
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <div key={index} className="card p-6 hover:shadow-lg transition-shadow">
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Built for Every Pharmaceutical Need
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              From research to education, PharmGPT adapts to your specific requirements
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {useCases.map((useCase, index) => (
              <div key={index} className="card p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {useCase.title}
                </h3>
                <ul className="space-y-2">
                  {useCase.items.map((item, itemIndex) => (
                    <li key={itemIndex} className="flex items-start">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-600">{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Trusted by Pharmaceutical Professionals
            </h2>
            <p className="text-xl text-primary-100 mb-12 max-w-3xl mx-auto">
              Join the growing community of researchers, educators, and professionals using PharmGPT
            </p>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="text-4xl font-bold text-white mb-2">AI-Powered</div>
                <div className="text-primary-100">Advanced Models</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-white mb-2">Secure</div>
                <div className="text-primary-100">Private Conversations</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-white mb-2">Multi-Format</div>
                <div className="text-primary-100">Document Support</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-white mb-2">24/7</div>
                <div className="text-primary-100">Available</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Ready to Transform Your Pharmaceutical Work?
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Start using PharmGPT today and experience the power of AI-assisted pharmaceutical research and education.
          </p>
          
          {!isAuthenticated && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register"
                className="btn-primary btn-lg inline-flex items-center"
              >
                Start Free Today
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link
                to="/support"
                className="btn-outline btn-lg"
              >
                Contact Support
              </Link>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}