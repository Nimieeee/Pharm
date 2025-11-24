import React from 'react'
import { useStreamingChat } from '@/hooks/useStreamingChat'
import { StreamingMessage } from '@/components/StreamingMessage'
import { Send, StopCircle } from 'lucide-react'

/**
 * Test page for streaming chat functionality
 * This demonstrates the useStreamingChat hook and StreamingMessage component
 */
export default function StreamingTestPage() {
  const {
    messages,
    input,
    handleInputChange,
    isLoading,
    sendMessage,
    stop
  } = useStreamingChat({
    conversationId: 'test-conversation-id', // Replace with actual conversation ID
    mode: 'fast',
    onNewMessage: (message) => {
      console.log('New message received:', message)
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      sendMessage(input)
    }
  }

  return (
    <div className="min-h-screen p-8" style={{ background: 'var(--bg-primary)' }}>
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-8" style={{ color: 'var(--text-primary)' }}>
          Streaming Chat Test
        </h1>

        {/* Messages */}
        <div className="space-y-6 mb-8 p-6 rounded-spa" style={{ background: 'var(--bg-secondary)' }}>
          {messages.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)' }}>
              No messages yet. Send a message to test streaming!
            </p>
          ) : (
            messages.map((message, idx) => (
              <StreamingMessage
                key={message.id}
                message={message}
                isStreaming={isLoading && idx === messages.length - 1}
              />
            ))
          )}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <textarea
            value={input}
            onChange={handleInputChange}
            placeholder="Type a message..."
            className="flex-1 p-4 rounded-spa resize-none"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)'
            }}
            rows={3}
            disabled={isLoading}
          />
          
          <div className="flex flex-col gap-2">
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="p-4 rounded-spa transition-spa"
              style={{
                background: input.trim() && !isLoading ? 'var(--accent)' : 'var(--bg-tertiary)',
                color: input.trim() && !isLoading ? 'var(--bg-primary)' : 'var(--text-tertiary)',
                opacity: input.trim() && !isLoading ? 1 : 0.5
              }}
            >
              <Send size={20} />
            </button>

            {isLoading && (
              <button
                type="button"
                onClick={stop}
                className="p-4 rounded-spa transition-spa"
                style={{
                  background: '#ef4444',
                  color: 'white'
                }}
              >
                <StopCircle size={20} />
              </button>
            )}
          </div>
        </form>

        {/* Status */}
        <div className="mt-4 text-sm" style={{ color: 'var(--text-tertiary)' }}>
          {isLoading ? 'Streaming response...' : 'Ready'}
        </div>
      </div>
    </div>
  )
}
