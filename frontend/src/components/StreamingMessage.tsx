import React from 'react'
import { Streamdown } from 'streamdown'
import { StreamingMessage as MessageType } from '@/hooks/useStreamingChat'

interface StreamingMessageProps {
  message: MessageType
  isStreaming?: boolean
}

export function StreamingMessage({ message, isStreaming }: StreamingMessageProps) {
  if (message.role === 'user') {
    return (
      <div className="max-w-[80%] px-4 py-3 rounded-spa ml-auto" 
           style={{ background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}>
        <p className="text-sm leading-relaxed">{message.content}</p>
      </div>
    )
  }

  return (
    <div className="flex gap-4 max-w-full">
      {/* AI Avatar */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-spa flex items-center justify-center" 
             style={{ background: 'var(--accent)' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" style={{ color: 'var(--bg-primary)' }} />
            <path d="M2 17l10 5 10-5" style={{ color: 'var(--bg-primary)' }} />
            <path d="M2 12l10 5 10-5" style={{ color: 'var(--bg-primary)' }} />
          </svg>
        </div>
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        {message.content ? (
          <div className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
            <Streamdown 
              className="streamdown-content"
              isAnimating={isStreaming}
            >
              {message.content}
            </Streamdown>
          </div>
        ) : (
          <div className="flex items-center gap-2 py-2">
            <div className="spinner-spa" />
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Thinking...</span>
          </div>
        )}
      </div>
    </div>
  )
}
