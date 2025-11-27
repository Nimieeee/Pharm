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
  citations?: Array<{
    id: number;
    title: string;
    url: string;
    source: string;
    authors?: string;
    year?: string;
    journal?: string;
    doi?: string;
  }>;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [deepResearchProgress, setDeepResearchProgress] = useState<DeepResearchProgress | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

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

        // Re-fetch conversation to ensure we have the latest saved report
        let savedReport = finalReport;
        if (currentConversationId) {
          try {
            const messagesResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${currentConversationId}/messages`, {
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            });

            if (messagesResponse.ok) {
              const messagesData = await messagesResponse.json();
              // Find the most recent assistant message (should be the deep research report)
              const latestAssistantMsg = messagesData
                .filter((msg: any) => msg.role === 'assistant')
                .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

              if (latestAssistantMsg?.content) {
                savedReport = latestAssistantMsg.content;
              }
            }
          } catch (refetchError) {
            console.error('Failed to re-fetch conversation:', refetchError);
          }
        }

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: savedReport || 'Deep research completed but no report was generated. Please try again.',
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
          let buffer = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            // Process complete lines from buffer
            const lines = buffer.split('\n');
            // Keep the last potentially incomplete line in buffer
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data.trim() === '[DONE]') continue;

                // Skip any JSON log messages that might have leaked into the stream
                if (data.trim().startsWith('{') && data.includes('"timestamp"')) continue;
                if (data.trim().startsWith('{') && data.includes('"level"')) continue;

                // The data is the actual text content, not JSON
                // Add it directly to the content
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

          // Process any remaining buffer
          if (buffer.startsWith('data: ')) {
            const data = buffer.slice(6);
            if (data.trim() !== '[DONE]') {
              fullContent += data;
              setMessages(prev => prev.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullContent }
                  : msg
              ));
            }
          }

          // After streaming completes, re-fetch the message to ensure we have the final formatted version
          if (currentConversationId) {
            try {
              const messagesResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${currentConversationId}/messages`, {
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });

              if (messagesResponse.ok) {
                const messagesData = await messagesResponse.json();
                const latestAssistantMsg = messagesData
                  .filter((msg: any) => msg.role === 'assistant')
                  .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

                if (latestAssistantMsg?.content && latestAssistantMsg.content !== fullContent) {
                  // Update with the saved version if it's different (e.g., better formatted)
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: latestAssistantMsg.content }
                      : msg
                  ));
                }
              }
            } catch (refetchError) {
              console.error('Failed to re-fetch message:', refetchError);
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
    // Clear from localStorage as well
    if (typeof window !== 'undefined') {
      localStorage.removeItem('currentConversationId');
    }
  }, []);

  const deleteConversation = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token || !conversationId) return false;

    setIsDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setMessages([]);
        setConversationId(null);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      return false;
    } finally {
      setIsDeleting(false);
    }
  }, [conversationId]);

  const uploadFiles = useCallback(async (files: FileList) => {
    const token = localStorage.getItem('token');
    if (!token) {
      // If not logged in, we can't upload. 
      // In a real app, we might want to trigger a login modal or return an error.
      return [{ fileName: 'General', status: 'error', error: 'Please sign in to upload files.' }];
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
        return [{ fileName: 'General', status: 'error', error: 'Failed to create conversation' }];
      }
    }

    setIsUploading(true);
    const results: { fileName: string; status: 'success' | 'error'; error?: string }[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      try {
        console.log(`📤 Uploading file: ${file.name} to conversation: ${currentConversationId}`);

        const formData = new FormData();
        formData.append('file', file);

        const uploadUrl = `${API_BASE_URL}/api/v1/chat/conversations/${currentConversationId}/documents`;

        const response = await fetch(uploadUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          body: formData,
        });

        if (response.ok) {
          console.log(`✅ Upload success: ${file.name}`);
          results.push({ fileName: file.name, status: 'success' });
        } else {
          let errorDetail = 'Unknown error';
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || JSON.stringify(errorData);
          } catch {
            errorDetail = `HTTP ${response.status}: ${response.statusText}`;
          }
          console.error(`❌ Upload failed:`, errorDetail);
          results.push({ fileName: file.name, status: 'error', error: errorDetail });
        }
      } catch (error: any) {
        console.error(`❌ Upload exception:`, error);
        results.push({ fileName: file.name, status: 'error', error: error.message || 'Network error' });
      }
    }

    setIsUploading(false);
    return results;
  }, [conversationId]);

  return {
    messages,
    isLoading,
    isUploading,
    isDeleting,
    sendMessage,
    clearMessages,
    deleteConversation,
    uploadFiles,
    conversationId,
    deepResearchProgress,
    selectConversation,
  };
}
