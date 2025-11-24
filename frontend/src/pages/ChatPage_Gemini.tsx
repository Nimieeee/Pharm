import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, Plus, Trash2, Loader2, Paperclip, Menu, X, Zap, Brain, Sun, Moon, Check, Sparkles, Mic } from 'lucide-react'
import { Streamdown } from 'streamdown'
import { useTheme } from '@/contexts/ThemeContext'
import { chatAPI, Conversation, Message, ConversationWithMessages } from '@/lib/api'
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<ConversationWithMessages | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768)
  const [mode, setMode] = useState<'fast' | 'detailed'>('fast')
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])

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
      setIsLoading(true)
      const data = await chatAPI.getConversation(id)
      setCurrentConversation(data)
      setMessages(data.messages || [])
    } catch (error) {
      toast.error('Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }

  const createNewConversation = async () => {
    try {
      const newConv = await chatAPI.createConversation({ title: 'New Chat' })
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
    if (!inputMessage.trim() || !conversationId) return
    
    const userMessage: Message = {
      id: Date.now().toString(),
      conversation_id: conversationId,
      role: 'user',
      content: inputMessage,
      created_at: new Date().toISOString(),
      metadata: uploadingFiles.filter(f => f.status === 'complete').length > 0 
        ? { attachedFiles: uploadingFiles.filter(f => f.status === 'complete') }
        : undefined
    }
    
    setMessages([...messages, userMessage])
    setInputMessage('')
    setUploadingFiles([])
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    
    try {
      const response = await chatAPI.sendMessage(conversationId, {
        message: inputMessage,
        mode: mode,
        document_ids: uploadingFiles.filter(f => f.status === 'complete').map(f => f.id)
      })
      
      setMessages(prev => [...prev, response])
      loadConversations()
    } catch (error) {
      toast.error('Failed to send message')
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
        const formData = new FormData()
        formData.append('file', file)
        formData.append('conversation_id', conversationId)
        
        const result = await chatAPI.uploadDocument(formData, (progress) => {
          setUploadingFiles(prev => prev.map(f => 
            f.id === uploadingFile.id ? { ...f, progress } : f
          ))
        })
        
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id 
            ? { ...f, id: result.id, status: 'complete', progress: 100 }
            : f
        ))
        
        toast.success(`${file.name} uploaded successfully`)
      } catch (error) {
        setUploadingFiles(prev => prev.map(f => 
          f.id === uploadingFile.id ? { ...f, status: 'error' } : f
        ))
        toast.error(`Failed to upload ${file.name}`)
      }
    })
    
    e.target.value = ''
  }

  const removeUploadingFile = (id: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== id))
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)
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
          'w-[260px] flex flex-col border-r border-surface',
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
            onClick={createNewConversation}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-gemini bg-gemini-gradient text-white hover:opacity-90 transition-opacity touch-target"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">New Chat</span>
          </button>
        </div>

        {/* Mode Toggle */}
        <div className="px-3 pb-3 flex gap-2">
          <button
            onClick={() => setMode('fast')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl transition-all touch-target text-sm',
              mode === 'fast'
                ? 'bg-surface-tertiary text-content-primary'
                : 'text-content-secondary hover:bg-surface-tertiary hover:text-content-primary'
            )}
          >
            <Zap className="w-4 h-4" />
            <span>Fast</span>
          </button>
          <button
            onClick={() => setMode('detailed')}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-xl transition-all touch-target text-sm',
              mode === 'detailed'
                ? 'bg-surface-tertiary text-content-primary'
                : 'text-content-secondary hover:bg-surface-tertiary hover:text-content-primary'
            )}
          >
            <Brain className="w-4 h-4" />
            <span>Detailed</span>
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-3 space-y-2">
          {conversations.map((conv) => (
            <div key={conv.id} className="relative group">
              <button
                onClick={() => {
                  navigate(`/chat/${conv.id}`)
                  if (window.innerWidth < 768) setSidebarOpen(false)
                }}
                className={cn(
                  'w-full text-left px-4 py-3 rounded-xl transition-colors touch-target',
                  conversationId === conv.id
                    ? 'bg-surface-tertiary text-content-primary'
                    : 'text-content-secondary hover:bg-surface-tertiary hover:text-content-primary'
                )}
              >
                <div className="font-medium text-sm truncate pr-8">{conv.title}</div>
                {conv.last_message && (
                  <div className="text-xs text-content-tertiary truncate mt-1">
                    {conv.last_message}
                  </div>
                )}
              </button>
              <button
                onClick={(e) => deleteConversation(conv.id, e)}
                className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-2 text-content-tertiary hover:text-red-500 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
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
          <h1 className="text-lg font-medium text-content-primary">
            {currentConversation?.title || 'PharmGPT'}
          </h1>
          {currentConversation?.document_count > 0 && (
            <span className="text-xs text-content-tertiary">
              {currentConversation.document_count} docs
            </span>
          )}
        </header>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-4 md:px-0">
          <div className="max-w-chat mx-auto py-8">
            {!conversationId ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-20">
                <div className="relative mb-6">
                  <Sparkles className="w-16 h-16 text-gemini-gradient" />
                  <div className="absolute -inset-4 bg-gemini-gradient opacity-20 blur-2xl rounded-full" />
                </div>
                <h2 className="text-2xl md:text-3xl font-medium text-content-primary mb-3">
                  Hello, how can I help you today?
                </h2>
                <p className="text-content-secondary">
                  Ask me anything about pharmacology, drug interactions, or clinical applications
                </p>
              </div>
            ) : isLoading && messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="ai-loader"></div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message, idx) => (
                  <div
                    key={message.id || idx}
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
                      {message.metadata?.attachedFiles && message.metadata.attachedFiles.length > 0 && (
                        <div className="mb-3 space-y-2">
                          {message.metadata.attachedFiles.map((file: any) => (
                            <div key={file.id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-secondary">
                              <Paperclip className="w-3 h-3 shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium truncate">{file.name}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      
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
        {conversationId && (
          <div className="border-t border-surface bg-surface-primary safe-bottom">
            <div className="max-w-chat mx-auto px-4 py-4">
              {/* Uploading Files */}
              {uploadingFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {uploadingFiles.map(file => (
                    <div
                      key={file.id}
                      className="flex items-center gap-2 px-3 py-2 text-xs rounded-xl border border-surface bg-surface-secondary"
                    >
                      <div
                        className={cn(
                          'w-6 h-6 rounded-full flex items-center justify-center shrink-0',
                          file.status === 'complete' ? 'bg-emerald-500' :
                          file.status === 'error' ? 'bg-red-500' :
                          'bg-blue-500'
                        )}
                      >
                        {file.status === 'complete' ? (
                          <Check className="w-3 h-3 text-white" />
                        ) : file.status === 'error' ? (
                          <X className="w-3 h-3 text-white" />
                        ) : (
                          <Loader2 className="w-3 h-3 text-white animate-spin" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate text-content-primary">{file.name}</div>
                        <div className="text-xs text-content-tertiary">
                          {file.status === 'complete' ? 'Ready' :
                           file.status === 'error' ? 'Failed' :
                           `${file.progress}%`}
                        </div>
                      </div>
                      <button
                        onClick={() => removeUploadingFile(file.id)}
                        className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
                      >
                        <X className="w-3 h-3 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Input Area */}
              <div className="relative flex items-end gap-2 bg-surface-secondary rounded-gemini-full px-4 py-2 border border-surface shadow-gemini">
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.txt,.pptx,.ppt,.xlsx,.csv,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp,.md"
                  className="hidden"
                />
                
                {/* Attachment Button */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingFiles.some(f => f.status === 'uploading')}
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
                  style={{ minHeight: '24px', fontSize: '16px' }}
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
        )}
      </main>
    </div>
  )
}
