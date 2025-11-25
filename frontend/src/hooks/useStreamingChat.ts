import { useState, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'

export interface StreamingMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at?: string
  metadata?: any
}

interface UseStreamingChatProps {
  conversationId?: string
  mode: 'fast' | 'detailed'
  onNewMessage?: (message: StreamingMessage) => void
}

export function useStreamingChat({ conversationId, mode, onNewMessage }: UseStreamingChatProps) {
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
  }, [])

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setIsLoading(false)
    }
  }, [])

  const sendMessage = useCallback(async (content: string, documentIds?: string[]) => {
    if (!content.trim() || !conversationId || isLoading) return

    const userMessage: StreamingMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Create abort controller for this request
    abortControllerRef.current = new AbortController()

    try {
      // Try streaming endpoint first
      let response: Response
      let useStreaming = true
      
      try {
        response = await fetch('/api/v1/ai/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('pharmgpt_token')}`
          },
          body: JSON.stringify({
            message: content.trim(),
            conversation_id: conversationId,
            mode,
            use_rag: true,
            metadata: documentIds && documentIds.length > 0 ? { document_ids: documentIds } : {}
          }),
          signal: abortControllerRef.current.signal
        })
        
        // Check if streaming endpoint returned an error (405, 404, etc.)
        if (!response.ok && (response.status === 405 || response.status === 404)) {
          console.log(`Streaming endpoint returned ${response.status}, using regular endpoint`)
          useStreaming = false
          response = await fetch('/api/v1/ai/chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('pharmgpt_token')}`
            },
            body: JSON.stringify({
              message: content.trim(),
              conversation_id: conversationId,
              mode,
              use_rag: true,
              metadata: documentIds && documentIds.length > 0 ? { document_ids: documentIds } : {}
            }),
            signal: abortControllerRef.current.signal
          })
        }
      } catch (streamError) {
        // Fallback to regular endpoint if streaming fails
        console.log('Streaming endpoint failed, using regular endpoint')
        useStreaming = false
        response = await fetch('/api/v1/ai/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('pharmgpt_token')}`
          },
          body: JSON.stringify({
            message: content.trim(),
            conversation_id: conversationId,
            mode,
            use_rag: true,
            metadata: documentIds && documentIds.length > 0 ? { document_ids: documentIds } : {}
          }),
          signal: abortControllerRef.current.signal
        })
      }

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`API error ${response.status}:`, errorText)
        throw new Error(`Failed to get response: ${response.status}`)
      }
      
      // Handle non-streaming response
      if (!useStreaming) {
        const data = await response.json()
        assistantMessage.content = data.response
        setMessages(prev => [...prev, assistantMessage])
        onNewMessage?.(assistantMessage)
        return
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let assistantMessage: StreamingMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              break
            }
            
            assistantMessage.content += data
            setMessages(prev => {
              const newMessages = [...prev]
              newMessages[newMessages.length - 1] = { ...assistantMessage }
              return newMessages
            })
          }
        }
      }

      onNewMessage?.(assistantMessage)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request aborted')
      } else {
        console.error('Streaming error:', error)
        toast.error('Failed to send message')
        // Remove the user message on error
        setMessages(prev => prev.filter(m => m.id !== userMessage.id))
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }, [conversationId, mode, isLoading, onNewMessage])

  const uploadFile = useCallback(async (file: File): Promise<string | null> => {
    if (!conversationId) {
      toast.error('No conversation selected')
      return null
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`/api/v1/ai/documents/upload?conversation_id=${conversationId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('pharmgpt_token')}`
        },
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Upload error:', errorText)
        throw new Error('Upload failed')
      }

      const result = await response.json()
      toast.success(`${file.name} uploaded successfully`)
      return result.id
    } catch (error) {
      console.error('Upload error:', error)
      toast.error(`Failed to upload ${file.name}`)
      return null
    }
  }, [conversationId])

  return {
    messages,
    input,
    handleInputChange,
    isLoading,
    sendMessage,
    uploadFile,
    stop,
    setMessages
  }
}
