import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, Upload, Plus, MessageSquare, Trash2, Menu, Loader2, Paperclip, ChevronLeft, Zap, Brain, Sun, Moon } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { chatAPI, Conversation, Message, ConversationWithMessages } from '@/lib/api'
import { cn } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { darkMode, toggleDarkMode } = useTheme()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversation, setCurrentConversation] = useState<ConversationWithMessages | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 1024)
  const [mode, setMode] = useState<'fast' | 'detailed'>('fast')
  const [uploadedFiles, setUploadedFiles] = useState<Array<{name: string, id: string}>>([])

  useEffect(() => { loadConversations() }, [])
  useEffect(() => { if (conversationId) loadConversation(conversationId) }, [conversationId])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) setSidebarOpen(false)
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
      if (window.innerWidth < 1024) setSidebarOpen(false)
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
    const attachedFiles = [...uploadedFiles]
    setInputMessage('')
    setUploadedFiles([])
    setIsSending(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const tempUserMessage: Message = {
      id: 'temp-' + Date.now(), conversation_id: conversationId, role: 'user',
      content: userMessage, created_at: new Date().toISOString(),
      metadata: { attachedFiles }
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
        message: userMessage, conversation_id: conversationId, mode, use_rag: true
      })
      
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
        await new Promise(resolve => setTimeout(resolve, 20))
      }
      
      // Remove streaming message and reload to get actual messages
      setMessages(prev => prev.filter(m => m.id !== streamingMessageId && m.id !== tempUserMessage.id))
      await loadConversation(conversationId)
      
      // Generate title if this is the first message
      if (currentConversation && currentConversation.message_count === 0) {
        await generateConversationTitle(conversationId, userMessage, response.response)
      }
    } catch (error) {
      toast.error('Failed to send message')
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id && m.id !== streamingMessageId))
    } finally {
      setIsSending(false)
    }
  }

  const generateConversationTitle = async (convId: string, userMsg: string, aiResponse: string) => {
    try {
      // Generate a summary title (7+ words) from the conversation
      const prompt = `${userMsg.substring(0, 100)}... ${aiResponse.substring(0, 100)}...`
      const words = prompt.split(' ').filter(w => w.length > 0)
      
      // Create a title with at least 7 words
      let title = words.slice(0, Math.max(7, Math.min(12, words.length))).join(' ')
      
      // Clean up and truncate if needed
      title = title.replace(/[^\w\s-]/g, '').trim()
      if (title.length > 60) {
        title = title.substring(0, 57) + '...'
      }
      
      // Ensure minimum 7 words
      const titleWords = title.split(' ')
      if (titleWords.length < 7) {
        title = `Conversation about ${title}`
      }
      
      await chatAPI.updateConversation(convId, title)
      await loadConversations()
    } catch (error) {
      console.error('Failed to generate title:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !conversationId) return
    setIsUploading(true)
    const fileId = 'file-' + Date.now()
    setUploadedFiles(prev => [...prev, { name: file.name, id: fileId }])
    try {
      const result = await chatAPI.uploadDocument(conversationId, file)
      
      // Check if upload was successful
      if (result.success && result.chunk_count > 0) {
        toast.success(`Document uploaded: ${result.chunk_count} chunks processed`)
      } else if (result.chunk_count === 0) {
        // Check if it's a rate limit issue
        if (result.message && result.message.includes('rate limit')) {
          toast.error('Upload failed: Mistral API rate limit exceeded. Please wait a few minutes and try again.')
        } else {
          toast.error('No content could be extracted from document')
        }
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
      } else {
        toast.warning(result.message || 'Document partially uploaded')
      }
      
      await loadConversation(conversationId)
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || 'Failed to upload document'
      toast.error(errorMsg)
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const removeUploadedFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatMessage = (content: string) => {
    const lines = content.split('\n')
    const elements: JSX.Element[] = []
    let inTable = false
    let tableRows: string[] = []
    
    const renderTable = (rows: string[]) => {
      if (rows.length === 0) return null
      
      // Parse table rows and clean up markdown formatting
      const parsedRows = rows.map(row => 
        row.split('|')
          .map(cell => cell.trim().replace(/\*\*/g, '').replace(/\*/g, ''))
          .filter(cell => cell)
      )
      
      if (parsedRows.length < 2) return null
      
      const headers = parsedRows[0]
      const dataRows = parsedRows.slice(2) // Skip separator row
      
      return (
        <div className="overflow-x-auto my-4">
          <table className={cn("min-w-full border-collapse text-sm", darkMode ? "border-gray-700" : "border-gray-300")}>
            <thead className={cn(darkMode ? "bg-gray-800" : "bg-gray-100")}>
              <tr>
                {headers.map((header, idx) => (
                  <th key={idx} className={cn("border px-4 py-2 text-left font-semibold", darkMode ? "border-gray-700" : "border-gray-300")}>
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataRows.map((row, rowIdx) => (
                <tr key={rowIdx} className={cn(darkMode ? "hover:bg-gray-800/50" : "hover:bg-gray-50")}>
                  {row.map((cell, cellIdx) => (
                    <td key={cellIdx} className={cn("border px-4 py-2", darkMode ? "border-gray-700" : "border-gray-300")}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }
    
    lines.forEach((line, i) => {
      // Detect table rows (lines with |)
      if (line.includes('|') && line.trim().startsWith('|')) {
        if (!inTable) {
          inTable = true
          tableRows = []
        }
        tableRows.push(line)
      } else {
        // If we were in a table, render it
        if (inTable) {
          const table = renderTable(tableRows)
          if (table) elements.push(<div key={`table-${i}`}>{table}</div>)
          inTable = false
          tableRows = []
        }
        
        // Format regular lines
        let processedLine = line.replace(/^#+\s/, '').replace(/\*\*/g, '')
        
        // Numbered lists
        if (processedLine.match(/^\d+\.\s/)) {
          const match = processedLine.match(/^(\d+)\.\s(.*)/)
          if (match) {
            elements.push(
              <div key={i} className="mb-2">
                <span className="font-semibold text-blue-500">{match[1]}.</span> {match[2]}
              </div>
            )
            return
          }
        }
        
        // Regular lines
        if (processedLine.trim()) {
          elements.push(<div key={i} className="mb-2">{processedLine}</div>)
        } else {
          elements.push(<div key={i} className="mb-1"></div>)
        }
      }
    })
    
    // Handle table at end of content
    if (inTable && tableRows.length > 0) {
      const table = renderTable(tableRows)
      if (table) elements.push(<div key="table-end">{table}</div>)
    }
    
    return elements
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px'
  }

  return (
    <div className={cn("flex h-screen overflow-hidden", darkMode ? "dark bg-[#212121] text-white" : "bg-white text-gray-900")}>
      {sidebarOpen && window.innerWidth < 1024 && (
        <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setSidebarOpen(false)} />
      )}
      
      <div className={cn("flex flex-col transition-all duration-300 border-r z-50", darkMode ? "bg-[#171717] border-gray-800" : "bg-gray-50 border-gray-200", sidebarOpen ? "w-64 fixed lg:relative h-full" : "w-0 border-r-0")}>
        {sidebarOpen && (<>
          <div className={cn("p-3 border-b flex items-center justify-between", darkMode ? "border-gray-800" : "border-gray-200")}>
            <button onClick={createNewConversation} className={cn("flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium mr-2", darkMode ? "bg-gray-800 hover:bg-gray-700" : "bg-white hover:bg-gray-100 border")}>
              <Plus className="w-4 h-4" />New chat
            </button>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden p-2 hover:bg-gray-800 rounded">
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map(conv => (
              <div key={conv.id} className={cn("group flex items-center gap-2 px-3 py-2 rounded-lg mb-1 cursor-pointer", conversationId === conv.id ? (darkMode ? "bg-gray-800" : "bg-gray-200") : (darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100"))} onClick={() => { navigate(`/chat/${conv.id}`); if (window.innerWidth < 1024) setSidebarOpen(false) }}>
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="flex-1 text-sm truncate">{conv.title}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }} className="p-1 hover:bg-red-500/10 rounded">
                  <Trash2 className="w-3 h-3 text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </>)}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className={cn("flex items-center justify-between px-3 lg:px-4 py-3 border-b", darkMode ? "border-gray-800" : "border-gray-200")}>
          <div className="flex items-center gap-2">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className={cn("p-2 rounded-lg", darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100")}>
              <Menu className="w-5 h-5" />
            </button>
            <img src="/PharmGPT.png" alt="PharmGPT" className="w-6 h-6" />
            <h1 className="text-base lg:text-lg font-semibold">PharmGPT</h1>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setMode('fast')} className={cn("p-2 rounded-lg", mode === 'fast' ? "bg-blue-600 text-white" : (darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100"))} title="Fast mode">
              <Zap className="w-4 h-4" />
            </button>
            <button onClick={() => setMode('detailed')} className={cn("p-2 rounded-lg", mode === 'detailed' ? "bg-blue-600 text-white" : (darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100"))} title="Detailed mode">
              <Brain className="w-4 h-4" />
            </button>
            <div className={cn("w-px h-6 mx-1", darkMode ? "bg-gray-700" : "bg-gray-300")} />
            <button onClick={toggleDarkMode} className={cn("p-2 rounded-lg", darkMode ? "hover:bg-gray-800" : "hover:bg-gray-100")} title="Toggle theme">
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto pb-32">
          {!conversationId ? (
            <div className="flex items-center justify-center h-full p-4">
              <div className="text-center">
                <img src="/PharmGPT.png" alt="PharmGPT" className="w-16 h-16 mx-auto mb-4" />
                <h2 className="text-xl lg:text-2xl font-semibold mb-2">Welcome to PharmGPT</h2>
                <p className={cn("text-sm", darkMode ? "text-gray-400" : "text-gray-600")}>Start a new conversation</p>
              </div>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="ai-loader scale-75"></div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto px-3 lg:px-4 py-4 lg:py-8">
              {messages.map((message) => (
                <div key={message.id} className={cn("mb-6 lg:mb-8 flex", message.role === 'user' ? "justify-end" : "justify-start")}>
                  {message.role === 'user' ? (
                    <div className={cn("max-w-[85%] lg:max-w-[70%] rounded-2xl px-4 py-3", darkMode ? "bg-blue-600 text-white" : "bg-blue-500 text-white")}>
                      {message.metadata?.attachedFiles && message.metadata.attachedFiles.length > 0 && (
                        <div className="mb-3 space-y-2">
                          {message.metadata.attachedFiles.map((file: any) => (
                            <div key={file.id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 backdrop-blur">
                              <div className="w-8 h-8 rounded bg-red-500 flex items-center justify-center shrink-0">
                                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                                </svg>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-sm truncate">{file.name}</div>
                                <div className="text-xs opacity-75">PDF</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="text-sm leading-relaxed break-words">{message.content}</div>
                    </div>
                  ) : (
                    <div className="flex gap-3 max-w-full">
                      <img src="/PharmGPT.png" alt="AI" className="w-8 h-8 rounded-full shrink-0" />
                      <div className="flex-1 min-w-0">
                        {!message.content ? (
                          <div className="flex items-center gap-3">
                            <div className="ai-loader scale-50"></div>
                            <span className={cn("text-sm", darkMode ? "text-gray-400" : "text-gray-600")}>Thinking...</span>
                          </div>
                        ) : (
                          <div className="text-sm leading-relaxed break-words">{formatMessage(message.content)}</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {conversationId && (
          <div className={cn("fixed bottom-0 left-0 right-0 p-3 lg:p-4", darkMode ? "bg-[#212121]" : "bg-white", sidebarOpen && window.innerWidth >= 1024 ? "lg:left-64" : "")}>
            <div className="max-w-4xl mx-auto">
              {uploadedFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {uploadedFiles.map(file => (
                    <div key={file.id} className={cn("flex items-center gap-2 px-3 py-2 rounded-full text-sm", darkMode ? "bg-gray-800 border border-gray-700" : "bg-gray-100 border border-gray-300")}>
                      <div className="w-8 h-8 rounded bg-red-500 flex items-center justify-center shrink-0">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{file.name}</div>
                        <div className={cn("text-xs", darkMode ? "text-gray-400" : "text-gray-600")}>PDF</div>
                      </div>
                      <button onClick={() => removeUploadedFile(file.id)} className={cn("p-1 rounded-full hover:bg-gray-700 shrink-0")}>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <div className={cn("flex items-end gap-2 rounded-3xl p-2 shadow-lg", darkMode ? "bg-[#2f2f2f]" : "bg-[#f4f4f4]")}>
                <input ref={fileInputRef} type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt" className="hidden" />
                <button onClick={() => fileInputRef.current?.click()} disabled={isUploading} className={cn("p-2 rounded-lg shrink-0", darkMode ? "hover:bg-gray-700" : "hover:bg-gray-200")} title="Upload document">
                  {isUploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Paperclip className="w-5 h-5" />}
                </button>
                <textarea ref={textareaRef} value={inputMessage} onChange={handleTextareaChange} onKeyPress={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }} placeholder="Message PharmGPT..." className={cn("flex-1 resize-none bg-transparent border-none outline-none px-2 py-2 max-h-[200px]", darkMode ? "text-white placeholder-gray-500" : "text-gray-900 placeholder-gray-400")} rows={1} disabled={isSending} style={{ minHeight: '24px' }} />
                <button onClick={sendMessage} disabled={!inputMessage.trim() || isSending} className={cn("p-2 rounded-lg shrink-0", inputMessage.trim() && !isSending ? "bg-blue-600 hover:bg-blue-700 text-white" : (darkMode ? "bg-gray-700 text-gray-500" : "bg-gray-200 text-gray-400"))}>
                  {isSending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </div>
              <p className={cn("text-xs text-center mt-2", darkMode ? "text-gray-500" : "text-gray-600")}>
                {mode === 'fast' ? 'Fast ⚡' : 'Detailed 🧠'}
                {currentConversation && currentConversation.document_count > 0 && ` • ${currentConversation.document_count} doc(s)`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
