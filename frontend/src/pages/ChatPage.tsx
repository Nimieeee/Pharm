import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Send, 
  Upload, 
  Plus, 
  MessageSquare, 
  FileText, 
  Trash2, 
  Edit2,
  Zap,
  Brain,
  Loader2,
  Menu,
  X,
  Sun,
  Moon
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { chatAPI, Conversation, Message, ConversationWithMessages } from '@/lib/api'
import { cn } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<ConversationWithMessages | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [mode, setMode] = useState<'fast' | 'detailed'>('fast')
  const [useRAG, setUseRAG] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [])

  // Load specific conversation when ID changes
  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId)
    }
  }, [conversationId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversations = async () => {
    try {
      const data = await chatAPI.getConversations()
      setConversations(data)
      
      // If no conversation selected and conversations exist, select first one
      if (!conversationId && data.length > 0) {
        navigate(`/chat/${data[0].id}`)
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
      toast.error('Failed to load conversations')
    }
  }

  const loadConversation = async (id: string) => {
    setIsLoading(true)
    try {
      const data = await chatAPI.getConversation(id)
      setCurrentConversation(data)
      setMessages(data.messages || [])
    } catch (error) {
      console.error('Failed to load conversation:', error)
      toast.error('Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }

  const createNewConversation = async () => {
    try {
      const newConv = await chatAPI.createConversation('New Conversation')
      setConversations([newConv, ...conversations])
      navigate(`/chat/${newConv.id}`)
      toast.success('New conversation created')
    } catch (error) {
      console.error('Failed to create conversation:', error)
      toast.error('Failed to create conversation')
    }
  }

  const deleteConversation = async (id: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return
    
    try {
      await chatAPI.deleteConversation(id)
      setConversations(conversations.filter(c => c.id !== id))
      
      if (conversationId === id) {
        const remaining = conversations.filter(c => c.id !== id)
        if (remaining.length > 0) {
          navigate(`/chat/${remaining[0].id}`)
        } else {
          navigate('/chat')
        }
      }
      
      toast.success('Conversation deleted')
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      toast.error('Failed to delete conversation')
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || !conversationId || isSending) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setIsSending(true)

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    // Add loading message for AI response
    const loadingMessage: Message = {
      id: 'loading-' + Date.now(),
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, loadingMessage])
    setIsStreaming(true)

    try {
      const response = await chatAPI.sendMessage({
        message: userMessage,
        conversation_id: conversationId,
        mode,
        use_rag: useRAG
      })

      // Format the response with proper line breaks and structure
      const formattedResponse = formatAIResponse(response.response)

      // Replace loading message with actual response
      const assistantMessage: Message = {
        id: 'temp-' + Date.now() + 1,
        conversation_id: conversationId,
        role: 'assistant',
        content: formattedResponse,
        metadata: { mode: response.mode, context_used: response.context_used },
        created_at: new Date().toISOString()
      }
      
      setMessages(prev => prev.filter(m => m.id !== loadingMessage.id).concat(assistantMessage))

      // Reload conversation to get updated message count
      await loadConversation(conversationId)
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error('Failed to send message')
      // Remove the temporary messages on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id && m.id !== loadingMessage.id))
    } finally {
      setIsSending(false)
      setIsStreaming(false)
    }
  }

  const formatAIResponse = (text: string): string => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '**$1**') // Keep bold formatting
      .replace(/(\d+)\.\s\*\*(.*?)\*\*:/g, '\n$1. **$2**:') // Format numbered lists with bold headers
      .replace(/(\d+)\.\s/g, '\n$1. ') // Format numbered lists
      .replace(/\n\s*\n/g, '\n\n') // Clean up multiple newlines
      .trim()
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !conversationId) return

    setIsUploading(true)
    try {
      await chatAPI.uploadDocument(conversationId, file)
      toast.success(`Document "${file.name}" uploaded successfully`)
      await loadConversation(conversationId)
    } catch (error) {
      console.error('Failed to upload document:', error)
      toast.error('Failed to upload document')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={`flex h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-secondary-50'}`}>
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Conversations List */}
      <div className={cn(
        "fixed lg:relative z-50 lg:z-auto flex flex-col transition-transform duration-300 ease-in-out",
        "w-80 h-full border-r",
        darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-secondary-200",
        sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        !sidebarOpen && "lg:w-0 lg:border-r-0"
      )}>
        <div className={cn("p-4 border-b", darkMode ? "border-gray-700" : "border-secondary-200")}>
          <div className="flex items-center justify-between mb-4">
            <h2 className={cn("font-semibold", darkMode ? "text-white" : "text-secondary-900")}>
              Conversations
            </h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded hover:bg-secondary-100 dark:hover:bg-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <button
            onClick={createNewConversation}
            className="btn btn-primary w-full flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className={cn("p-4 text-center", darkMode ? "text-gray-400" : "text-secondary-500")}>
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
            </div>
          ) : (
            <div className="p-2">
              {conversations.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => {
                    navigate(`/chat/${conv.id}`)
                    setSidebarOpen(false) // Close sidebar on mobile after selection
                  }}
                  className={cn(
                    'w-full text-left p-3 rounded-lg mb-2 transition-colors group',
                    conversationId === conv.id
                      ? darkMode 
                        ? 'bg-gray-700 border border-gray-600' 
                        : 'bg-primary-50 border border-primary-200'
                      : darkMode
                        ? 'hover:bg-gray-700 border border-transparent'
                        : 'hover:bg-secondary-50 border border-transparent'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className={cn("font-medium truncate", darkMode ? "text-white" : "text-secondary-900")}>
                        {conv.title}
                      </h3>
                      <p className={cn("text-xs mt-1", darkMode ? "text-gray-400" : "text-secondary-500")}>
                        {conv.message_count} messages • {conv.document_count} docs
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteConversation(conv.id)
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-opacity"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {!conversationId ? (
          <div className="flex-1 flex items-center justify-center p-4">
            <div className="text-center">
              <MessageSquare className={cn("w-16 h-16 mx-auto mb-4", darkMode ? "text-gray-400" : "text-secondary-400")} />
              <h2 className={cn("text-2xl font-bold mb-2", darkMode ? "text-white" : "text-secondary-900")}>
                Welcome to PharmGPT Chat
              </h2>
              <p className={cn("mb-4", darkMode ? "text-gray-300" : "text-secondary-600")}>
                Select a conversation or create a new one to get started
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className={cn("border-b p-4", darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-secondary-200")}>
              <div className="flex items-center justify-between">
                {/* Mobile menu button and title */}
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className={cn(
                      "lg:hidden p-2 rounded-lg transition-colors",
                      darkMode ? "hover:bg-gray-700" : "hover:bg-secondary-100"
                    )}
                  >
                    <Menu className="w-5 h-5" />
                  </button>
                  <div className="min-w-0 flex-1">
                    <h2 className={cn("text-lg font-semibold truncate", darkMode ? "text-white" : "text-secondary-900")}>
                      {currentConversation?.title || 'Loading...'}
                    </h2>
                    <p className={cn("text-sm", darkMode ? "text-gray-400" : "text-secondary-500")}>
                      {currentConversation?.document_count || 0} documents uploaded
                    </p>
                  </div>
                </div>
                
                {/* Controls */}
                <div className="flex items-center gap-2">
                  {/* Dark mode toggle */}
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className={cn(
                      "p-2 rounded-lg transition-colors",
                      darkMode ? "hover:bg-gray-700 text-yellow-400" : "hover:bg-secondary-100 text-secondary-600"
                    )}
                  >
                    {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                  </button>
                  
                  {/* Mode selector - hidden on small screens */}
                  <div className="hidden sm:flex items-center gap-2">
                    <button
                      onClick={() => setMode('fast')}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1',
                        mode === 'fast'
                          ? darkMode 
                            ? 'bg-blue-900 text-blue-300' 
                            : 'bg-primary-100 text-primary-700'
                          : darkMode
                            ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                      )}
                    >
                      <Zap className="w-4 h-4" />
                      <span className="hidden sm:inline">Fast</span>
                    </button>
                    <button
                      onClick={() => setMode('detailed')}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1',
                        mode === 'detailed'
                          ? darkMode 
                            ? 'bg-blue-900 text-blue-300' 
                            : 'bg-primary-100 text-primary-700'
                          : darkMode
                            ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                            : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                      )}
                    >
                      <Brain className="w-4 h-4" />
                      <span className="hidden sm:inline">Detailed</span>
                    </button>
                    
                    <label className="hidden md:flex items-center gap-2 ml-4">
                      <input
                        type="checkbox"
                        checked={useRAG}
                        onChange={(e) => setUseRAG(e.target.checked)}
                        className="rounded"
                      />
                      <span className={cn("text-sm", darkMode ? "text-gray-300" : "text-secondary-700")}>
                        Use Documents
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className={cn("w-8 h-8 animate-spin", darkMode ? "text-blue-400" : "text-primary-600")} />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <MessageSquare className={cn("w-12 h-12 mx-auto mb-2", darkMode ? "text-gray-400" : "text-secondary-400")} />
                    <p className={cn(darkMode ? "text-gray-300" : "text-secondary-600")}>
                      No messages yet. Start the conversation!
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={cn(
                        'max-w-3xl rounded-lg p-4 relative',
                        message.role === 'user'
                          ? darkMode
                            ? 'bg-blue-600 text-white'
                            : 'bg-primary-600 text-white'
                          : darkMode
                            ? 'bg-gray-700 border border-gray-600 text-white'
                            : 'bg-white border border-secondary-200'
                      )}
                    >
                      {/* Loading state for AI messages */}
                      {message.role === 'assistant' && !message.content && isStreaming ? (
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm opacity-75">Thinking...</span>
                        </div>
                      ) : (
                        <>
                          <div className="prose prose-sm max-w-none">
                            {message.content.split('\n').map((line, index) => {
                              if (line.trim().match(/^\d+\.\s\*\*(.*?)\*\*:/)) {
                                // Numbered list with bold header
                                const match = line.match(/^(\d+)\.\s\*\*(.*?)\*\*:\s*(.*)/)
                                if (match) {
                                  return (
                                    <div key={index} className="mb-3">
                                      <div className="font-semibold text-blue-600 dark:text-blue-400">
                                        {match[1]}. {match[2]}:
                                      </div>
                                      {match[3] && <div className="ml-4 mt-1">{match[3]}</div>}
                                    </div>
                                  )
                                }
                              } else if (line.trim().match(/^\d+\.\s/)) {
                                // Regular numbered list
                                return <div key={index} className="mb-2">{line}</div>
                              } else if (line.trim().match(/^\*\*(.*?)\*\*/)) {
                                // Bold text
                                const boldText = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                return <div key={index} className="mb-2" dangerouslySetInnerHTML={{ __html: boldText }} />
                              } else if (line.trim()) {
                                return <div key={index} className="mb-2">{line}</div>
                              } else {
                                return <div key={index} className="mb-2"></div>
                              }
                            })}
                          </div>
                          {message.metadata?.context_used && (
                            <div className="text-xs mt-3 pt-2 border-t border-opacity-20 opacity-75">
                              📚 Used document context
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className={cn("border-t p-4", darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-secondary-200")}>
              {/* Mobile RAG toggle */}
              <div className="md:hidden mb-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={useRAG}
                    onChange={(e) => setUseRAG(e.target.checked)}
                    className="rounded"
                  />
                  <span className={cn("text-sm", darkMode ? "text-gray-300" : "text-secondary-700")}>
                    Use Documents
                  </span>
                </label>
              </div>

              <div className="flex items-end gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className={cn(
                    "btn btn-outline p-3 shrink-0",
                    darkMode ? "border-gray-600 hover:bg-gray-700" : ""
                  )}
                  title="Upload document"
                >
                  {isUploading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Upload className="w-5 h-5" />
                  )}
                </button>
                
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message... (Shift+Enter for new line)"
                  className={cn(
                    "input flex-1 resize-none min-h-[48px] max-h-32",
                    darkMode ? "bg-gray-700 border-gray-600 text-white placeholder-gray-400" : ""
                  )}
                  rows={1}
                  disabled={isSending}
                />
                
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isSending}
                  className="btn btn-primary p-3 shrink-0"
                >
                  {isSending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
              <p className={cn("text-xs mt-2", darkMode ? "text-gray-400" : "text-secondary-500")}>
                Mode: <span className="font-medium">{mode === 'fast' ? 'Fast Response' : 'Detailed Analysis'}</span>
                {useRAG && ' • Using uploaded documents'}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
