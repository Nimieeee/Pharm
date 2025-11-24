import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, Plus, MessageSquare, Trash2, Loader2, Paperclip, ChevronLeft, ChevronRight, Zap, Brain, Sun, Moon, X, Check } from 'lucide-react'

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
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 1024)
  const [mode, setMode] = useState<'fast' | 'detailed'>('fast')
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])

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
    if (!inputMessage.trim() || !conversationId) return
    const userMessage = inputMessage.trim()
    const attachedFiles = uploadingFiles.filter(f => f.status === 'complete').map(f => ({ name: f.name, id: f.id }))
    setInputMessage('')
    setUploadingFiles([]) // Clear files after sending
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
        message: userMessage,
        conversation_id: conversationId,
        mode,
        use_rag: true,
        metadata: attachedFiles.length > 0 ? { attachedFiles } : undefined
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
    } catch (error: any) {
      // Handle 429 rate limit error gracefully
      if (error?.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait a moment and try again.')
      } else {
        toast.error('Failed to send message')
      }
      setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id && m.id !== streamingMessageId))
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

    const fileId = 'file-' + Date.now()
    const uploadingFile: UploadingFile = {
      name: file.name,
      id: fileId,
      progress: 0,
      status: 'uploading'
    }

    setUploadingFiles(prev => [...prev, uploadingFile])

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadingFiles(prev => prev.map(f =>
          f.id === fileId && f.progress < 90
            ? { ...f, progress: Math.min(f.progress + 10, 90) }
            : f
        ))
      }, 500)

      const result = await chatAPI.uploadDocument(conversationId, file)
      clearInterval(progressInterval)

      if (result.success && result.chunk_count > 0) {
        setUploadingFiles(prev => prev.map(f =>
          f.id === fileId
            ? { ...f, progress: 100, status: 'complete' }
            : f
        ))
        toast.success(`Document uploaded: ${result.chunk_count} chunks`)
        await loadConversation(conversationId)
      } else if (result.chunk_count === 0) {
        setUploadingFiles(prev => prev.map(f =>
          f.id === fileId
            ? { ...f, status: 'error' }
            : f
        ))
        if (result.message && result.message.includes('rate limit')) {
          toast.error('Rate limit exceeded. Please wait and try again.')
        } else {
          toast.error('No content extracted from document')
        }
      }
    } catch (error: any) {
      setUploadingFiles(prev => prev.map(f =>
        f.id === fileId
          ? { ...f, status: 'error' }
          : f
      ))

      if (error?.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait and try again.')
      } else if (error?.response?.status === 520) {
        toast.error('Backend is waking up. Please try again in a moment.')
      } else {
        toast.error(error?.response?.data?.detail || 'Failed to upload document')
      }
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const removeUploadingFile = (fileId: string) => {
    setUploadingFiles(prev => prev.filter(f => f.id !== fileId))
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className={cn(
      "flex h-screen overflow-hidden",
      darkMode ? "dark bg-[#1a1a1a] text-white" : "bg-white text-neutral-900"
    )}>
      {sidebarOpen && window.innerWidth < 1024 && (
        <div className="fixed inset-0 bg-black/80 z-40" onClick={() => setSidebarOpen(false)} />
      )}

      <div className={cn(
        "flex flex-col transition-all duration-200 border-r-4 z-50",
        darkMode ? "bg-neutral-900 border-white" : "bg-neutral-50 border-neutral-900",
        sidebarOpen ? "w-72 fixed lg:relative h-full" : "w-0 border-r-0"
      )}>
        {sidebarOpen && (<>
          <div className={cn("p-4 border-b-4 flex items-center justify-between", darkMode ? "border-white" : "border-neutral-900")}>
            <button 
              onClick={createNewConversation} 
              className="flex-1 btn-primary btn-sm mr-2"
            >
              <Plus className="w-4 h-4 mr-2" />New
            </button>
            <button 
              onClick={() => setSidebarOpen(false)} 
              className={cn(
                "lg:hidden p-2 border-3 transition-colors",
                darkMode ? "border-white hover:bg-white hover:text-neutral-900" : "border-neutral-900 hover:bg-neutral-900 hover:text-white"
              )}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3">
            {conversations.map(conv => (
              <div 
                key={conv.id} 
                className={cn(
                  "group flex items-center gap-3 px-3 py-3 mb-2 cursor-pointer transition-all duration-200 border-3",
                  conversationId === conv.id 
                    ? (darkMode 
                        ? "bg-white text-neutral-900 border-white" 
                        : "bg-neutral-900 text-white border-neutral-900"
                      )
                    : (darkMode 
                        ? "border-neutral-700 hover:border-white" 
                        : "border-neutral-300 hover:border-neutral-900"
                      )
                )} 
                onClick={() => { navigate(`/chat/${conv.id}`); if (window.innerWidth < 1024) setSidebarOpen(false) }}
              >
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="flex-1 text-xs truncate font-bold uppercase tracking-wide">{conv.title}</span>
                <button 
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }} 
                  className="p-1 hover:scale-110 transition-transform"
                >
                  <Trash2 className="w-3.5 h-3.5 text-accent-600" />
                </button>
              </div>
            ))}
          </div>
        </>)}
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className={cn(
          "flex items-center justify-between px-4 lg:px-6 py-3 border-b-4",
          darkMode ? "border-white bg-neutral-900" : "border-neutral-900 bg-white"
        )}>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)} 
              className={cn(
                "p-2 border-3 transition-colors",
                darkMode ? "border-white hover:bg-white hover:text-neutral-900" : "border-neutral-900 hover:bg-neutral-900 hover:text-white"
              )}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
            <img src="/PharmGPT.png" alt="PharmGPT" className="w-8 h-8" />
            <span className="font-display font-black text-lg hidden sm:block">PharmGPT</span>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setMode('fast')} 
              className={cn(
                "p-2 border-3 transition-all duration-200",
                mode === 'fast' 
                  ? (darkMode ? "bg-white text-neutral-900 border-white" : "bg-neutral-900 text-white border-neutral-900")
                  : (darkMode ? "border-neutral-700 hover:border-white" : "border-neutral-300 hover:border-neutral-900")
              )} 
              title="Fast mode"
            >
              <Zap className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setMode('detailed')} 
              className={cn(
                "p-2 border-3 transition-all duration-200",
                mode === 'detailed' 
                  ? (darkMode ? "bg-white text-neutral-900 border-white" : "bg-neutral-900 text-white border-neutral-900")
                  : (darkMode ? "border-neutral-700 hover:border-white" : "border-neutral-300 hover:border-neutral-900")
              )} 
              title="Detailed mode"
            >
              <Brain className="w-4 h-4" />
            </button>
            <div className={cn("w-px h-6 mx-1 border-l-2", darkMode ? "border-neutral-700" : "border-neutral-300")} />
            <button 
              onClick={toggleDarkMode} 
              className={cn(
                "p-2 border-3 transition-colors",
                darkMode ? "border-neutral-700 hover:border-white" : "border-neutral-300 hover:border-neutral-900"
              )} 
              title="Toggle theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto pb-32">
          {!conversationId ? (
            <div className="flex items-center justify-center h-full p-4">
              <div className="text-center">
                <img src="/PharmGPT.png" alt="PharmGPT" className="w-16 h-16 mx-auto mb-4" />
                <h2 className="text-2xl lg:text-3xl font-display font-black mb-2">
                  PharmGPT System
                </h2>
                <p className="text-sm font-sans uppercase tracking-wider">
                  Initialize conversation
                </p>
              </div>
            </div>
          ) : isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="ai-loader"></div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto px-4 lg:px-6 py-6">
              {messages.map((message, idx) => (
                <div 
                  key={message.id} 
                  className={cn(
                    "mb-6 flex",
                    message.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === 'user' ? (
                    <div className={cn(
                      "max-w-[85%] lg:max-w-[70%] px-4 py-3 border-4",
                      darkMode 
                        ? "bg-white text-neutral-900 border-white" 
                        : "bg-neutral-900 text-white border-neutral-900"
                    )}>
                      {message.metadata?.attachedFiles && message.metadata.attachedFiles.length > 0 && (
                        <div className="mb-3 space-y-2">
                          {message.metadata.attachedFiles.map((file: any) => (
                            <div key={file.id} className={cn(
                              "flex items-center gap-2 px-2 py-1 border-2",
                              darkMode ? "border-neutral-900 bg-neutral-100" : "border-white bg-neutral-800"
                            )}>
                              <Paperclip className="w-3 h-3 shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-bold uppercase truncate">{file.name}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="text-sm font-sans leading-relaxed break-words">{message.content}</div>
                    </div>
                  ) : (
                    <div className="flex gap-3 max-w-full">
                      <img src="/PharmGPT.png" alt="AI" className="w-8 h-8 shrink-0" />
                      <div className={cn(
                        "flex-1 min-w-0 px-4 py-3 border-4",
                        darkMode 
                          ? "bg-neutral-900 border-neutral-700" 
                          : "bg-white border-neutral-300"
                      )}>
                        {!message.content ? (
                          <div className="flex items-center gap-3">
                            <div className="ai-loader scale-75"></div>
                            <span className="text-xs font-bold uppercase tracking-wider">
                              Processing...
                            </span>
                          </div>
                        ) : (
                          <div className="text-sm font-sans leading-relaxed break-words">{formatMessage(message.content)}</div>
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
          <div className={cn(
            "fixed bottom-0 left-0 right-0 p-4 border-t-4 z-20",
            darkMode ? "bg-neutral-900 border-white" : "bg-white border-neutral-900",
            sidebarOpen && window.innerWidth >= 1024 ? "lg:left-72" : ""
          )}>
            <div className="max-w-4xl mx-auto">
              {uploadingFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {uploadingFiles.map(file => (
                    <div 
                      key={file.id} 
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 text-xs border-3",
                        darkMode 
                          ? "bg-neutral-800 border-neutral-700" 
                          : "bg-neutral-50 border-neutral-300"
                      )}
                    >
                      <div className={cn(
                        "w-6 h-6 flex items-center justify-center shrink-0 border-2",
                        file.status === 'complete' ? 'bg-primary-600 border-primary-600' :
                          file.status === 'error' ? 'bg-accent-600 border-accent-600' :
                            'bg-neutral-900 border-neutral-900'
                      )}>
                        {file.status === 'complete' ? (
                          <Check className="w-3 h-3 text-white" />
                        ) : file.status === 'error' ? (
                          <X className="w-3 h-3 text-white" />
                        ) : (
                          <Loader2 className="w-3 h-3 text-white animate-spin" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-bold uppercase truncate">{file.name}</div>
                        <div className="text-xs">
                          {file.status === 'complete' ? 'READY' :
                            file.status === 'error' ? 'FAILED' :
                              `${file.progress}%`}
                        </div>
                      </div>
                      <button 
                        onClick={() => removeUploadingFile(file.id)} 
                        className="p-1 hover:scale-110 transition-transform"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <div className={cn(
                "flex items-end gap-2 p-2 border-4",
                darkMode 
                  ? "bg-neutral-900 border-white" 
                  : "bg-white border-neutral-900"
              )}>
                <input ref={fileInputRef} type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt,.pptx,.ppt,.xlsx,.csv,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp,.md" className="hidden" />
                <button 
                  onClick={() => fileInputRef.current?.click()} 
                  disabled={uploadingFiles.some(f => f.status === 'uploading')} 
                  className={cn(
                    "p-2 border-3 shrink-0 transition-colors",
                    darkMode ? "border-neutral-700 hover:border-white" : "border-neutral-300 hover:border-neutral-900"
                  )} 
                  title="Upload document"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <textarea 
                  ref={textareaRef} 
                  value={inputMessage} 
                  onChange={handleTextareaChange} 
                  onKeyDown={handleKeyDown} 
                  placeholder="Enter query..." 
                  className="flex-1 resize-none bg-transparent border-none outline-none px-2 py-2 max-h-[200px] font-sans text-sm"
                  rows={1} 
                  style={{ minHeight: '24px' }} 
                />
                <button 
                  onClick={sendMessage} 
                  disabled={!inputMessage.trim()} 
                  className={cn(
                    "p-2 border-3 shrink-0 transition-all duration-200",
                    inputMessage.trim() 
                      ? (darkMode ? "bg-white text-neutral-900 border-white hover:translate-y-0.5" : "bg-neutral-900 text-white border-neutral-900 hover:translate-y-0.5")
                      : (darkMode ? "border-neutral-800 text-neutral-800" : "border-neutral-200 text-neutral-300")
                  )}
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-center mt-2 font-sans uppercase tracking-wider">
                {mode === 'fast' ? '[FAST MODE]' : '[DETAILED MODE]'}
                {currentConversation && currentConversation.document_count > 0 && ` • ${currentConversation.document_count} DOCS`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
