import React, { useState, useRef, useEffect } from 'react'
import { Menu, X, Send, Sparkles, Plus, Sun, Moon, Paperclip, Mic } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'
import { Streamdown } from 'streamdown'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
}

export default function GeminiChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768)
  const [inputMessage, setInputMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'Drug Interactions',
      lastMessage: 'What are the interactions between...',
      timestamp: new Date(),
    },
  ])
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  
  const { darkMode, toggleDarkMode } = useTheme()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }

  // Handle send message
  const sendMessage = () => {
    if (!inputMessage.trim()) return
    
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    }
    
    setMessages([...messages, newMessage])
    setInputMessage('')
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    
    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'This is a simulated response from PharmGPT. The actual AI integration will provide detailed pharmaceutical information.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMessage])
    }, 1000)
  }

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false)
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const startNewChat = () => {
    setMessages([])
    setCurrentConversationId(null)
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-surface-primary">
      {/* Sidebar Overlay for Mobile */}
      {sidebarOpen && window.innerWidth < 768 && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed md:relative top-0 left-0 h-full bg-surface-secondary z-50 transition-transform duration-300 ease-in-out',
          'w-[260px] flex flex-col',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-surface">
          <div className="flex items-center gap-2">
            <img src="/PharmGPT.png" alt="PharmGPT" className="w-8 h-8" />
            <span className="font-medium text-content-primary">PharmGPT</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden touch-target text-content-secondary hover:text-content-primary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={startNewChat}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-gemini bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">New Chat</span>
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-3 space-y-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => {
                setCurrentConversationId(conv.id)
                if (window.innerWidth < 768) {
                  setSidebarOpen(false)
                }
              }}
              className={cn(
                'w-full text-left px-4 py-3 rounded-xl transition-colors touch-target',
                currentConversationId === conv.id
                  ? 'bg-surface-tertiary text-content-primary'
                  : 'text-content-secondary hover:bg-surface-tertiary hover:text-content-primary'
              )}
            >
              <div className="font-medium text-sm truncate">{conv.title}</div>
              <div className="text-xs text-content-tertiary truncate mt-1">
                {conv.lastMessage}
              </div>
            </button>
          ))}
        </div>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-surface">
          <button
            onClick={toggleDarkMode}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-content-secondary hover:bg-surface-tertiary hover:text-content-primary transition-colors touch-target"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            <span className="text-sm">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-surface bg-surface-primary">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="touch-target text-content-secondary hover:text-content-primary transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-medium text-content-primary">PharmGPT</h1>
        </header>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-4 md:px-0">
          <div className="max-w-chat mx-auto py-8">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <div className="relative mb-6">
                  <Sparkles className="w-16 h-16 text-gemini-gradient-start" />
                  <div className="absolute -inset-4 bg-gemini-gradient opacity-20 blur-2xl rounded-full" />
                </div>
                <h2 className="text-2xl md:text-3xl font-medium text-content-primary mb-3">
                  Hello, how can I help you today?
                </h2>
                <p className="text-content-secondary">
                  Ask me anything about pharmacology, drug interactions, or clinical applications
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex gap-4',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-gemini-gradient flex items-center justify-center">
                          <Sparkles className="w-4 h-4 text-white" />
                        </div>
                      </div>
                    )}
                    
                    <div
                      className={cn(
                        message.role === 'user'
                          ? 'message-user'
                          : 'message-ai'
                      )}
                    >
                      {message.role === 'assistant' ? (
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <Streamdown>{message.content}</Streamdown>
                        </div>
                      ) : (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input Container - Fixed at Bottom */}
        <div className="border-t border-surface bg-surface-primary safe-bottom">
          <div className="max-w-chat mx-auto px-4 py-4">
            <div className="relative flex items-end gap-2 bg-surface-secondary rounded-gemini-full px-4 py-2 border border-surface shadow-gemini">
              {/* Attachment Button */}
              <button
                className="touch-target text-content-secondary hover:text-content-primary transition-colors flex-shrink-0"
                title="Attach file"
              >
                <Paperclip className="w-5 h-5" />
              </button>

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Message PharmGPT..."
                className="flex-1 bg-transparent border-none outline-none resize-none text-content-primary placeholder:text-content-tertiary text-base py-2 max-h-[200px]"
                rows={1}
                style={{ minHeight: '24px' }}
              />

              {/* Voice Button */}
              <button
                className="touch-target text-content-secondary hover:text-content-primary transition-colors flex-shrink-0"
                title="Voice input"
              >
                <Mic className="w-5 h-5" />
              </button>

              {/* Send Button */}
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim()}
                className={cn(
                  'touch-target rounded-full transition-all flex-shrink-0',
                  inputMessage.trim()
                    ? 'bg-gemini-gradient text-white hover:opacity-90'
                    : 'text-content-tertiary cursor-not-allowed'
                )}
                title="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            
            {/* Disclaimer */}
            <p className="text-xs text-content-tertiary text-center mt-3">
              PharmGPT can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
