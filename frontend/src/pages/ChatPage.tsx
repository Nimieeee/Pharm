import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Send, Upload, Plus, MessageSquare, Trash2, Menu, X, Sun, Moon, Loader2, Paperclip, ChevronLeft
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
  const [isUploading, setIsUploading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(true)

  useEffect(() => { loadConversations() }, [])
  useEffect(() => { if (conversationId) loadConversation(conversationId) }, [conversationId])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

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
    setIsLoading(true)
    try {
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
      const newConv = await chatAPI.createConversation('New Conversation')
      setConversations([newConv, ...conversations])
      navigate(`/chat/${newConv.id}`)
    } catch (error) {
      toast.error('Failed to create conversation')
    }
  }

  const deleteConversation = async (id: string) => {
    if (!confirm('Delete this conversation?')) return
    try {
      await chatAPI.deleteConversation(id)
      setConversations(conversations.filter(c => c.id !== id))
      if (conversationId === id) {
        const remaining = conversations.filter(c => c.id !== id)
        if (remaining.length > 0) navigate(`/chat/${remaining[0].id}`)
        else navigate('/chat')
      }
    } catch (error) {
      toast.error('Failed to delete conversation')
    }
  }

  const sendMessage = async () => {
    if (!inputMessage.trim() || !conversationId || isSending) return
    const userMessage = inputMessage.trim()
    setInputMessage('')
    setIsSending(true)

    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(), conversation_id: conversationId, role: 'user',
      content: userMessage, created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, tempUserMessage])

    const streamingMessageId = 'streaming-' + Date.now()
    const streamingMessage: Message = {
      id: streamingMessageId, conversation_id: conversationId, role: 'assistant',
      content: '', created_at: new Date().toISOString()
    }
    setMessages(prev => [...prev, streamingMessage])

    try {
      const response = await chatAPI.sendMessage({
        message: userMessage, conversation_id: conversationId, mode: 'detailed', use_rag: true
      })
      
      // Simulate streaming effect
      const fullText = response.response
      let currentText = ''
      const words = fullText.split(' ')
      
      for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i]
        setMessages(prev => prev.map(m => 
          m.id === streamingMessageId 
            ? { ...m, content: currentText, metadata: { mode: response.mode, context_used: response.context_used } }
            : m
        ))
        await new Promise(resolve => setTimeout(resolve, 30)) // Adjust speed here
      }
      
      await loadConversation(conversationId)
    } catch (error) {
      toast.error('Failed to send message')
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id && m.id !== streamingMessageId))
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
      toast.success(`Document uploaded`)
      await loadConversation(conversationId)
    } catch (error) {
      toast.error('Failed to upload document')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const formatMessage = (content: string) => {
    return content.split('\n').map((line, i) => {
      if (line.match(/^\d+\.\s\*\*(.*?)\*\*:/)) {
        const match = line.match(/^(\d+)\.\s\*\*(.*?)\*\*:\s*(.*)/)
        if (match) return (
          <div key={i} className="mb-3">
            <div className="font-semibold text-blue-500">{match[1]}. {match[2]}:</div>
            {match[3] && <div className="ml-4 mt-1">{match[3]}</div>}
          </div>
        )
      }
      const formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      return <div key={i} className="mb-2" dangerouslySetInnerHTML={{ __html: formatted }} />
    })
  }

  return (
    <div className={cn("flex h-screen", darkMode ? "dark bg-[#212121] text-white" : "bg-white text-gray-900")}>
      <div className={cn("flex flex-col transition-all duration-300 border-r", darkMode ? "bg-[#171717] border-gray-800" : "bg-gray-50 border-gray-200", sidebarOpen ? "w-64" : "w-0 border-r-0")}>
        {sidebarOpen && (<>
          <div className={cn("p-3 border-b", darkMode ? "border-gray-800" : "border-gray-200")}>
            <button onClick={createNewConversation} className={cn("w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium", darkMode ? "bg-gray-800 hover:bg-gray-700" : "bg-white hover:bg-gray-100 border")}>
              <Plus className="w-4 h-4" />New chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map(conv => (
              <div key={conv.id} className={cn("group flex items-center gap-2 px-3 py-2 rounded-lg mb-1 cursor-pointer", conversationId === conv.id ? (darkMode ? "bg-gray-800" : "bg-gray-200") : (darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100"))} onClick={() => navigate(`/chat/${conv.id}`)}>
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/10 rounded">
                  <Trash2 className="w-3 h-3 text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </>)}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className={cn("flex items-center justify-between px-4 py-3 border-b", darkMode ? "border-gray-800" : "border-gray-200")}>
          <div className="flex items-center gap-2">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className={cn("p-2 rounded-lg", darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100")}>
              {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="text-lg font-semibold">PharmGPT</h1>
          </div>
          <button onClick={() => setDarkMode(!darkMode)} className={cn("p-2 rounded-lg", darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100")}>
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {!conversationId ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h2 className="text-2xl font-semibold mb-2">Welcome to PharmGPT</h2>
                <p className={cn("text-sm", darkMode ? "text-gray-400" : "text-gray-600")}>Start a new conversation</p>
              </div>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-8">
              {messages.map((message) => (
                <div key={message.id} className="mb-8">
                  <div className="flex gap-4">
                    <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm font-semibold", message.role === 'user' ? "bg-blue-600 text-white" : "bg-green-600 text-white")}>
                      {message.role === 'user' ? 'U' : 'AI'}
                    </div>
                    <div className="flex-1 min-w-0">
                      {message.role === 'assistant' && !message.content && isSending ? (
                        <div className="flex items-center gap-3">
                          <div className="ai-loader"></div>
                          <span className={cn("text-sm", darkMode ? "text-gray-400" : "text-gray-600")}>
                            Thinking...
                          </span>
                        </div>
                      ) : (
                        <div className="text-sm leading-relaxed">{formatMessage(message.content)}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {conversationId && (
          <div className={cn("border-t p-4", darkMode ? "border-gray-800" : "border-gray-200")}>
            <div className="max-w-3xl mx-auto">
              <div className={cn("flex items-end gap-2 rounded-xl border p-2", darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-300")}>
                <input ref={fileInputRef} type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt" className="hidden" />
                <button onClick={() => fileInputRef.current?.click()} disabled={isUploading} className={cn("p-2 rounded-lg shrink-0", darkMode ? "hover:bg-gray-700" : "hover:bg-gray-100")}>
                  {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Paperclip className="w-5 h-5" />}
                </button>
                <textarea value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} onKeyPress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }} placeholder="Message PharmGPT..." className={cn("flex-1 resize-none bg-transparent border-none outline-none px-2 py-2 max-h-32", darkMode ? "text-white placeholder-gray-500" : "text-gray-900 placeholder-gray-400")} rows={1} disabled={isSending} />
                <button onClick={sendMessage} disabled={!inputMessage.trim() || isSending} className={cn("p-2 rounded-lg shrink-0", inputMessage.trim() && !isSending ? "bg-blue-600 hover:bg-blue-700 text-white" : (darkMode ? "bg-gray-700 text-gray-500" : "bg-gray-200 text-gray-400"))}>
                  {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </div>
              {currentConversation && currentConversation.document_count > 0 && (
                <p className={cn("text-xs mt-2", darkMode ? "text-gray-500" : "text-gray-600")}>
                  📎 {currentConversation.document_count} document(s) uploaded
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
