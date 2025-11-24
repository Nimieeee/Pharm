import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, Plus, MessageSquare, Trash2, Paperclip, Menu, X, Zap, Brain, Sun, Moon, Check, Loader2, User, LogOut, Home } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { useAuth } from '@/contexts/AuthContext'
import { chatAPI, Conversation, ConversationWithMessages } from '@/lib/api'
import { useStreamingChat } from '@/hooks/useStreamingChat'
import { StreamingMessage } from '@/components/StreamingMessage'
import { cn } from '@/lib/utils'
import toast from 'react-hot-toast'

interface UploadingFile {
  name: string
  id: string
  progress: number
  status: 'uploading' | 'processing' | 'complete' | 'error'
}

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const { darkMode, toggleDarkMode } = useTheme()
  const { user, logout } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<ConversationWithMessages | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768)
  const [mode, setMode] = useState<'fast' | 'detailed'>('fast')
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  // Use streaming chat hook
  const {
    messages,
    input,
    handleInputChange,
    isLoading,
    sendMessage: sendStreamingMessage,
    uploadFile,
    stop,
    setMessages
  } = useStreamingChat({
    conversationId,
    mode,
    onNewMessage: () => {
      loadConversations()
    }
  })

  useEffect(() => { loadConversations() }, [])
  useEffect(() => { if (conversationId) loadConversation(conversationId) }, [conversationId])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) setSidebarOpen(false)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const loadConversations = async () => {
    try {
      const data = await chatAPI.getConversations()
      setConversations(data)
      if (!conversationId && data.length > 0) navigate(`/chat/${data[0].id}`)
    } catch (error) {
      toast.error('Failed to load conversations')
    }
  }

  const loadConversation = async (id: string) => {
    try {
      const data = await chatAPI.getConversation(id)
      setCurrentConversation(data)
      setMessages(data.messages || [])
    } catch (error) {
      toast.error('Failed to load conversation')
    }
  }

  const createNewConversation = async () => {
    try {
      const newConv = await chatAPI.createConversation('New Conversation')
      setConversations([newConv, ...conversations])
      navigate(`/chat/${newConv.id}`)
      if (window.innerWidth < 768) setSidebarOpen(false)
    } catch (error) {
      toast.error('Failed to create conversation')
    }
  }

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return
    try {
      await chatAPI.deleteConversation(id)
      setConversations(conversations.filter(c => c.id !== id))
      if (conversationId === id) {
        const remaining = conversations.filter(c => c.id !== id)
        if (remaining.length > 0) navigate(`/chat/${remaining[0].id}`)
        else navigate('/chat')
      }
      toast.success('Conversation deleted')
    } catch (error) {
      toast.error('Failed to delete conversation')
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || !conversationId || isLoading) return
    
    const attachedDocs = uploadingFiles.filter(f => f.status === 'complete').map(f => f.id)
    
    // Send with streaming
    await sendStreamingMessage(input.trim(), attachedDocs)
    
    // Clear files and reset textarea
    setUploadingFiles([])
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || !conversationId) return
    
    Array.from(files).forEach(async (file) => {
      const uploadingFile: UploadingFile = {
        name: file.name,
        id: Date.now().toString(),
        progress: 0,
        status: 'uploading'
      }
      
      setUploadingFiles(prev => [...prev, uploadingFile])
      
      try {
        const fileId = await uploadFile(file)
        
        if (fileId) {
          setUploadingFiles(prev => prev.map(f => 
            f.id === uploadingFile.id 
              ? { ...f, id: fileId, status: 'complete', progress: 100 }
              : f
          ))
        } else {
          setUploadingFiles(prev => prev.map(f => 
            f.id === uploadingFile.id ? { ...f, status: 'error' } : f
          ))
        }
      } catch (error) {
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { ...f, status: 'error' } : f
        ))
      }
    })
    
    e.target.value = ''
  }

  const removeUploadingFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id))
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    handleInputChange(e)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
      {/* Sidebar Overlay */}
      {sidebarOpen && window.innerWidth < 768 && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          style={{ background: 'rgba(0, 0, 0, 0.5)' }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Collapsible on all screens */}
      <aside
        className={cn(
          'fixed top-0 left-0 h-full z-50 transition-all duration-300 ease-in-out flex flex-col',
          sidebarOpen ? 'w-[280px]' : 'w-0'
        )}
        style={{ 
          background: 'var(--bg-secondary)', 
          borderRight: sidebarOpen ? '1px solid var(--border)' : 'none'
        }}
      >
        <div className={cn('h-full flex flex-col', sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none')}>
          {/* Sidebar Header */}
          <div className="flex items-center justify-between p-4" style={{ borderBottom: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2">
              <img src="/PharmGPT.png" alt="PharmGPT" className="w-8 h-8" />
              <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>PharmGPT</span>
            </div>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={createNewConversation}
              className="btn-spa btn-primary w-full"
            >
              <Plus size={20} strokeWidth={2} />
              <span>New Chat</span>
            </button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto px-4 space-y-2">
            {conversations.map((conv) => (
              <div key={conv.id} className="relative group">
                <button
                  onClick={() => {
                    navigate(`/chat/${conv.id}`)
                    if (window.innerWidth < 768) setSidebarOpen(false)
                  }}
                  className={cn(
                    'w-full text-left px-4 py-3 rounded-lg transition-all',
                    conversationId === conv.id ? 'active' : ''
                  )}
                  style={conversationId === conv.id ? {
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)'
                  } : {
                    color: 'var(--text-secondary)'
                  }}
                >
                  <div className="font-medium text-sm truncate pr-8">{conv.title}</div>
                </button>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-2 transition-all"
                  style={{ color: 'var(--text-tertiary)' }}
                >
                  <Trash2 size={16} strokeWidth={2} />
                </button>
              </div>
            ))}
          </div>

          {/* User Menu at Bottom */}
          <div className="p-4" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all hover:bg-opacity-50"
                style={{ color: 'var(--text-secondary)', background: userMenuOpen ? 'var(--bg-tertiary)' : 'transparent' }}
              >
                <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'var(--accent)' }}>
                  <User size={16} style={{ color: 'white' }} strokeWidth={2} />
                </div>
                <span className="text-sm font-medium flex-1 truncate">{user?.first_name || user?.email || 'User'}</span>
              </button>

              {userMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                  <div className="absolute bottom-full left-0 right-0 mb-2 rounded-lg shadow-lg py-2 z-50"
                       style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                    <button
                      onClick={() => {
                        navigate('/')
                        setUserMenuOpen(false)
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm transition-all"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      <Home size={16} strokeWidth={2} />
                      <span>Home</span>
                    </button>
                    <button
                      onClick={() => {
                        logout()
                        navigate('/login')
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm transition-all"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      <LogOut size={16} strokeWidth={2} />
                      <span>Sign out</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Bar with Controls */}
        <header className="flex items-center justify-between gap-3 px-4 py-3" style={{ borderBottom: '1px solid var(--border)' }}>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-spa transition-spa hover:bg-opacity-10"
              style={{ color: 'var(--text-secondary)' }}
              title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              <Menu size={20} strokeWidth={2} />
            </button>
            <h1 className="text-lg font-semibold hidden sm:block" style={{ color: 'var(--text-primary)' }}>
              {currentConversation?.title || 'PharmGPT'}
            </h1>
            {currentConversation?.document_count > 0 && (
              <span className="text-xs hidden sm:inline" style={{ color: 'var(--text-tertiary)' }}>
                {currentConversation.document_count} docs
              </span>
            )}
          </div>

          {/* Right Side Controls */}
          <div className="flex items-center gap-2">
            {/* Mode Toggle */}
            <div className="flex gap-1 p-1 rounded-spa" style={{ background: 'var(--bg-secondary)' }}>
              <button
                onClick={() => setMode('fast')}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-spa text-xs font-medium transition-spa',
                )}
                style={mode === 'fast' ? { 
                  background: 'var(--accent)', 
                  color: 'var(--bg-primary)' 
                } : { 
                  color: 'var(--text-secondary)' 
                }}
                title="Fast mode - Quick responses"
              >
                <Zap size={14} strokeWidth={2} />
                <span className="hidden sm:inline">Fast</span>
              </button>
              <button
                onClick={() => setMode('detailed')}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-spa text-xs font-medium transition-spa',
                )}
                style={mode === 'detailed' ? { 
                  background: 'var(--accent)', 
                  color: 'var(--bg-primary)' 
                } : { 
                  color: 'var(--text-secondary)' 
                }}
                title="Detailed mode - Comprehensive responses"
              >
                <Brain size={14} strokeWidth={2} />
                <span className="hidden sm:inline">Detailed</span>
              </button>
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-spa transition-spa"
              style={{ color: 'var(--text-secondary)' }}
              title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {darkMode ? <Sun size={20} strokeWidth={2} /> : <Moon size={20} strokeWidth={2} />}
            </button>
          </div>
        </header>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-4">
          <div className="max-w-[48rem] mx-auto py-8">
            {!conversationId ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <MessageSquare size={64} className="mb-6" style={{ color: 'var(--text-tertiary)' }} strokeWidth={2} />
                <h2 className="text-2xl md:text-3xl font-semibold mb-3" 
                    style={{ 
                      color: 'var(--text-primary)',
                      fontFamily: "'Cormorant Garamond', Georgia, serif"
                    }}>
                  Start a conversation
                </h2>
                <p style={{ color: 'var(--text-secondary)' }}>
                  Ask me anything about pharmacology
                </p>
              </div>
            ) : isLoading && messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="spinner-spa"></div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message, idx) => (
                  <StreamingMessage
                    key={message.id || idx}
                    message={message}
                    isStreaming={isLoading && idx === messages.length - 1}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Floating Input Container */}
        {conversationId && (
          <div className="sticky bottom-0 px-4 py-6" style={{ background: 'linear-gradient(to top, var(--bg-primary) 80%, transparent)' }}>
            <div className="max-w-[48rem] mx-auto">
              {/* Uploading Files */}
              {uploadingFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {uploadingFiles.map(file => (
                    <div
                      key={file.id}
                      className="flex items-center gap-2 px-3 py-2 text-xs rounded-full"
                      style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
                    >
                      <div
                        className="w-4 h-4 rounded-full flex items-center justify-center"
                        style={{
                          background: file.status === 'complete' ? 'var(--success)' :
                                     file.status === 'error' ? '#ef4444' : 'var(--accent)'
                        }}
                      >
                        {file.status === 'complete' ? (
                          <Check size={10} style={{ color: 'white' }} strokeWidth={2} />
                        ) : file.status === 'error' ? (
                          <X size={10} style={{ color: 'white' }} strokeWidth={2} />
                        ) : (
                          <Loader2 size={10} style={{ color: 'white' }} strokeWidth={2} className="animate-spin" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate" style={{ color: 'var(--text-primary)' }}>{file.name}</div>
                      </div>
                      <button
                        onClick={() => removeUploadingFile(file.id)}
                        className="p-1"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        <X size={12} strokeWidth={2} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Pill-shaped Floating Input */}
              <div className="flex items-center gap-2 px-4 py-2 rounded-full shadow-lg" 
                   style={{ 
                     background: 'var(--bg-secondary)', 
                     border: '1px solid var(--border)',
                     maxWidth: '100%'
                   }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.txt,.pptx,.ppt,.xlsx,.csv,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp,.md"
                  className="hidden"
                />
                
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingFiles.some(f => f.status === 'uploading')}
                  className="p-2 rounded-full transition-all hover:bg-opacity-10"
                  style={{ color: 'var(--text-secondary)' }}
                  title="Attach file"
                >
                  <Paperclip size={18} strokeWidth={2} />
                </button>

                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleTextareaChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Message PharmGPT..."
                  className="flex-1 bg-transparent border-none outline-none resize-none text-sm py-2"
                  rows={1}
                  style={{ 
                    minHeight: '20px',
                    maxHeight: '120px',
                    fontSize: '14px',
                    color: 'var(--text-primary)'
                  }}
                  disabled={isLoading}
                />

                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isLoading}
                  className="p-2 rounded-full transition-all"
                  style={{ 
                    background: input.trim() && !isLoading ? 'var(--accent)' : 'transparent',
                    color: input.trim() && !isLoading ? 'white' : 'var(--text-tertiary)',
                    opacity: input.trim() && !isLoading ? 1 : 0.4
                  }}
                  title="Send message"
                >
                  {isLoading ? (
                    <Loader2 size={18} strokeWidth={2} className="animate-spin" />
                  ) : (
                    <Send size={18} strokeWidth={2} />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
