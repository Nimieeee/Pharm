import React from 'react'
import { MessageSquare } from 'lucide-react'

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Chat Interface</h2>
        <p className="text-gray-600 mb-4">
          The chat interface will be implemented in the next phase
        </p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-sm text-blue-700">
            This page will include the full chat interface with:
          </p>
          <ul className="text-sm text-blue-700 mt-2 space-y-1 text-left">
            <li>• Real-time messaging</li>
            <li>• Document upload</li>
            <li>• Conversation management</li>
            <li>• AI response modes</li>
          </ul>
        </div>
      </div>
    </div>
  )
}