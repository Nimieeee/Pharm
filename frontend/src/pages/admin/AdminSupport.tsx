import React from 'react'
import { MessageSquare } from 'lucide-react'

export default function AdminSupport() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Support Management</h1>
          <p className="text-gray-600 mt-2">
            Manage support requests and customer communications
          </p>
        </div>

        <div className="card p-8 text-center">
          <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Support Management Interface
          </h2>
          <p className="text-gray-600 mb-6">
            The support management interface will be implemented in the next phase
          </p>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
            <p className="text-sm text-blue-700 mb-2">Features coming soon:</p>
            <ul className="text-sm text-blue-600 space-y-1 text-left">
              <li>• View all support requests</li>
              <li>• Respond to customer inquiries</li>
              <li>• Track request status</li>
              <li>• Support analytics</li>
              <li>• Automated responses</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}