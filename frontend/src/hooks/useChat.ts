'use client';

import { useState, useCallback, useEffect } from 'react';
import { Message } from '@/components/chat/ChatMessage';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt-backend.onrender.com'
  : 'http://localhost:8000';

type Mode = 'fast' | 'detailed' | 'deep_research';

interface DeepResearchProgress {
  type: string;
  status?: string;
  message?: string;
  progress?: number;
  plan_overview?: string;
  steps?: Array<{ id: number; topic: string; source: string }>;
  count?: number;
  report?: string;
  citations?: Array<{ id: number; title: string; url: string; source: string }>;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [deepResearchProgress, setDeepResearchProgress] = useState<DeepResearchProgress | null>(null);

  // Load conversation messages when conversationId changes
  const loadConversation = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${convId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const loadedMessages: Message[] = data.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
        }));
        setMessages(loadedMessages);
        setConversationId(convId);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  }, []);

  const selectConversation = useCallback((convId: string) => {
    loadConversation(convId);
  }, [loadConversation]);

  const createConversation = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ title: 'New Chat' }),
      });

      if (response.ok) {
        const data = await response.json();
        setConversationId(data.id);
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const sendMessage = useCallback(async (content: string, mode: Mode = 'detailed') => {
    if (!content.trim() || isLoading) return;

    const token = localStorage.getItem('token');
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (!token) {
        const authMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Please sign in to use PharmGPT. Go to /login to authenticate.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, authMessage]);
        setIsLoading(false);
        return;
      }

      let currentConversationId = conversationId;
      if (!currentConversationId) {
        const convResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ title: content.slice(0, 50) }),
        });

        if (convResponse.ok) {
          const convData = await convResponse.json();
          currentConversationId = convData.id;
          setConversationId(convData.id);
        } else {
          throw new Error('Failed to create conversation');
        }
      }

      // Handle Deep Research mode differently - use streaming endpoint
      if (mode === 'deep_research') {
        // Initialize accumulated state for the UI
        let accumulatedState: DeepResearchProgress = {
          type: 'status',
          status: 'initializing',
          message: 'Starting deep research...',
          progress: 0,
          steps: [],
          citations: [],
          plan_overview: ''
        };
        
        setDeepResearchProgress(accumulatedState);
        
        const response = await fetch(`${API_BASE_URL}/api/v1/ai/deep-research/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            question: content.trim(),
            conversation_id: currentConversationId,
          }),
        });

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.removeItem('token');
            throw new Error('Session expired. Please sign in again.');
          }
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to start deep research');
        }

        // Process SSE stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let finalReport = '';

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();
                if (data === '[DONE]') continue;
                
                try {
                  const progress = JSON.parse(data) as DeepResearchProgress;
                  
                  // Accumulate state for better UI experience
                  accumulatedState = {
                    ...accumulatedState,
                    ...progress,
                    // Preserve accumulated data
                    steps: progress.steps || accumulatedState.steps,
                    citations: progress.citations || accumulatedState.citations,
                    plan_overview: progress.plan_overview || accumulatedState.plan_overview,
                  };
                  
                  setDeepResearchProgress({ ...accumulatedState });
                  
                  if (progress.type === 'complete' && progress.report) {
                    finalReport = progress.report;
                  }
                } catch (e) {
                  // Ignore parse errors for partial chunks
                }
              }
            }
          }
        }

        setDeepResearchProgress(null);

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: finalReport || 'Deep research completed but no report was generated.',
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
        return;
      }

      // Regular chat mode - try streaming first, fallback to non-streaming
      const assistantMessageId = (Date.now() + 1).toString();
      let useStreaming = true;
      
      try {
        const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: content.trim(),
            conversation_id: currentConversationId,
            mode: mode,
            use_rag: true,
          }),
        });

        if (streamResponse.ok && streamResponse.body) {
          // Add empty assistant message that we'll update
          const assistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, assistantMessage]);

          // Process SSE stream
          const reader = streamResponse.body.getReader();
          const decoder = new TextDecoder();
          let fullContent = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();
                if (data === '[DONE]') continue;
                
                fullContent += data;
                // Update the message content in real-time
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: fullContent }
                    : msg
                ));
              }
            }
          }
          return; // Successfully streamed
        } else {
          useStreaming = false;
        }
      } catch (streamError) {
        console.log('Streaming not available, falling back to regular chat');
        useStreaming = false;
      }

      // Fallback to non-streaming
      if (!useStreaming) {
        const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: content.trim(),
            conversation_id: currentConversationId,
            mode: mode,
            use_rag: true,
          }),
        });

        if (!response.ok) {
          if (response.status === 401) {
            localStorage.removeItem('token');
            throw new Error('Session expired. Please sign in again.');
          }
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to get response');
        }

        const data = await response.json();
        
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: data.response || data.message || 'I apologize, but I encountered an issue processing your request.',
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error: any) {
      console.error('Chat error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error.message || 'I apologize, but I\'m having trouble connecting to the server. Please check your connection and try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  const uploadFiles = useCallback(async (files: FileList) => {
    const token = localStorage.getItem('token');
    if (!token) {
      const authMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Please sign in to upload files.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, authMessage]);
      return;
    }

    // Ensure we have a conversation
    let currentConversationId = conversationId;
    if (!currentConversationId) {
      try {
        const convResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ title: 'Document Analysis' }),
        });

        if (convResponse.ok) {
          const convData = await convResponse.json();
          currentConversationId = convData.id;
          setConversationId(convData.id);
        } else {
          throw new Error('Failed to create conversation');
        }
      } catch (error) {
        console.error('Failed to create conversation:', error);
        return;
      }
    }

    setIsUploading(true);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Add upload status message
      const uploadingMessage: Message = {
        id: `upload-${Date.now()}-${i}`,
        role: 'assistant',
        content: `📤 Uploading ${file.name}...`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, uploadingMessage]);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(
          `${API_BASE_URL}/api/v1/chat/conversations/${currentConversationId}/documents`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            body: formData,
          }
        );

        // Remove uploading message
        setMessages(prev => prev.filter(m => m.id !== uploadingMessage.id));

        if (response.ok) {
          const result = await response.json();
          const successMessage: Message = {
            id: `upload-success-${Date.now()}-${i}`,
            role: 'assistant',
            content: `✅ **${file.name}** uploaded successfully!\n\n${result.chunk_count} text chunks extracted and indexed. You can now ask questions about this document.`,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, successMessage]);
        } else {
          const errorData = await response.json();
          const errorMessage: Message = {
            id: `upload-error-${Date.now()}-${i}`,
            role: 'assistant',
            content: `❌ Failed to upload **${file.name}**: ${errorData.detail || 'Unknown error'}`,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMessage]);
        }
      } catch (error: any) {
        // Remove uploading message
        setMessages(prev => prev.filter(m => m.id !== uploadingMessage.id));
        
        const errorMessage: Message = {
          id: `upload-error-${Date.now()}-${i}`,
          role: 'assistant',
          content: `❌ Failed to upload **${file.name}**: ${error.message || 'Network error'}`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    }

    setIsUploading(false);
  }, [conversationId]);

  return {
    messages,
    isLoading,
    isUploading,
    sendMessage,
    clearMessages,
    uploadFiles,
    conversationId,
    deepResearchProgress,
    selectConversation,
  };
}
