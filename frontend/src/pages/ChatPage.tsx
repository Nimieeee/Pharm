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
  Loader2
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

    try {
      const response = await chatAPI.sendMessage({
        message: userMessage,
        conversation_id: conversationId,
        mode,
        use_rag: useRAG
      })

      // Add assistant response
      const assistantMessage: Message = {
        id: 'temp-' + Date.now() + 1,
        conversation_id: conversationId,
        role: 'assistant',
        content: response.response,
        metadata: { mode: response.mode, context_used: response.context_used },
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])

      // Reload conversation to get updated message count
      await loadConversation(conversationId)
    } catch (error) {
      console.error('Failed to send message:', error)
      toast.error('Failed to send message')
      // Remove the temporary user message on error
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id))
    } finally {
      setIsSending(false)
    }
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
    <div className="flex h-screen bg-secondary-50">
      {/* Sidebar - Conversations List */}
      <div className="w-80 bg-white border-r border-secondary-200 flex flex-col">
        <div className="p-4 border-b border-secondary-200">
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
            <div className="p-4 text-center text-secondary-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
            </div>
          ) : (
            <div className="p-2">
              {conversations.map(conv => (
                <button
                  key={conv.id}
                  onClick={() => navigate(`/chat/${conv.id}`)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg mb-2 transition-colors group',
                    conversationId === conv.id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-secondary-50 border border-transparent'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-secondary-900 truncate">
                        {conv.title}
                      </h3>
                      <p className="text-xs text-secondary-500 mt-1">
                        {conv.message_count} messages • {conv.document_count} docs
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteConversation(conv.id)
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-opacity"
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
      <div className="flex-1 flex flex-col">
        {!conversationId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 text-secondary-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-secondary-900 mb-2">
                Welcome to PharmGPT Chat
              </h2>
              <p className="text-secondary-600 mb-4">
                Select a conversation or create a new one to get started
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-secondary-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-secondary-900">
                    {currentConversation?.title || 'Loading...'}
                  </h2>
                  <p className="text-sm text-secondary-500">
                    {currentConversation?.document_count || 0} documents uploaded
                  </p>
                </div>
                
                {/* Mode Selector */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setMode('fast')}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1',
                      mode === 'fast'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                    )}
                  >
                    <Zap className="w-4 h-4" />
                    Fast
                  </button>
                  <button
                    onClick={() => setMode('detailed')}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1',
                      mode === 'detailed'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
                    )}
                  >
                    <Brain className="w-4 h-4" />
                    Detailed
                  </button>
                  
                  <label className="flex items-center gap-2 ml-4">
                    <input
                      type="checkbox"
                      checked={useRAG}
                      onChange={(e) => setUseRAG(e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm text-secondary-700">Use Documents</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <MessageSquare className="w-12 h-12 text-secondary-400 mx-auto mb-2" />
                    <p className="text-secondary-600">No messages yet. Start the conversation!</p>
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
                        'max-w-3xl rounded-lg p-4',
                        message.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-white border border-secondary-200'
                      )}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      {message.metadata?.context_used && (
                        <p className="text-xs mt-2 opacity-75">
                          📚 Used document context
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-secondary-200 p-4">
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
                  className="btn btn-outline p-3"
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
                  className="input flex-1 resize-none"
                  rows={3}
                  disabled={isSending}
                />
                
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim() || isSending}
                  className="btn btn-primary p-3"
                >
                  {isSending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
              <p className="text-xs text-secondary-500 mt-2">
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
