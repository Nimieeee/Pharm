'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { Send, Paperclip, Mic, ArrowUp } from 'lucide-react'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string) => void
  isLoading: boolean
}

export default function ChatInput({ value, onChange, onSend, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = () => {
    if (value.trim() && !isLoading) {
      onSend(value)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const adjustHeight = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }
  }

  return (
    <div className="border-t border-border bg-background">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="relative bg-[#2f2f2f] rounded-3xl border border-border hover:border-gray-600 transition-colors">
          {/* Attachment Button */}
          <button
            className="absolute left-3 bottom-3 p-2 hover:bg-card rounded-lg transition-colors"
            title="Add files"
          >
            <Paperclip size={20} />
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              onChange(e.target.value)
              adjustHeight()
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            className="w-full bg-transparent px-14 py-3 focus:outline-none resize-none max-h-[200px]"
            rows={1}
            disabled={isLoading}
          />

          {/* Right Actions */}
          <div className="absolute right-3 bottom-3 flex items-center space-x-2">
            {!value.trim() && (
              <button
                className="p-2 hover:bg-card rounded-lg transition-colors"
                title="Voice input"
              >
                <Mic size={20} />
              </button>
            )}
            
            <button
              onClick={handleSubmit}
              disabled={!value.trim() || isLoading}
              className="p-2 bg-white text-black hover:bg-gray-200 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed rounded-lg transition-colors"
              title="Send message"
            >
              <ArrowUp size={20} />
            </button>
          </div>
        </div>

        {/* Footer Text */}
        <p className="text-center text-xs text-gray-500 mt-3">
          PharmGPT can make mistakes. Check important info.
        </p>
      </div>
    </div>
  )
}
