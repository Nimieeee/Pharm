'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Message } from '@/components/chat/ChatMessage';
import { moveConversationToTop, addConversationToList } from './useSWRChat';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? '' // Use relative path for production (proxied by Vercel)
  : 'http://localhost:8000';

// Direct backend URL for large file uploads (bypasses Vercel's 4.5MB limit)
const UPLOAD_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt.164.68.122.165.sslip.io' // Direct HTTPS to backend for large uploads
  : 'http://localhost:8000';

type Mode = 'fast' | 'detailed' | 'deep_research';

// Helper function to generate intelligent conversation title
function generateConversationTitle(message: string): string {
  // Remove extra whitespace and newlines
  const cleaned = message.trim().replace(/\s+/g, ' ');

  // If message is short enough, use it as-is
  if (cleaned.length <= 50) {
    return cleaned;
  }

  // Try to cut at a sentence boundary
  const firstSentence = cleaned.match(/^[^.!?]+[.!?]/);
  if (firstSentence && firstSentence[0].length <= 60) {
    return firstSentence[0].replace(/[.!?]$/, '');
  }

  // Otherwise, cut at word boundary around 50 chars
  const truncated = cleaned.substring(0, 50);
  const lastSpace = truncated.lastIndexOf(' ');
  return lastSpace > 30 ? truncated.substring(0, lastSpace) + '...' : truncated + '...';
}

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
    source_type?: string;
    authors?: string;
    year?: string;
    journal?: string;
    doi?: string;
    snippet?: string;
  }>;
}

import { activeStreams, registerStream, unregisterStream, isConversationStreaming } from './useStreamingState';

// Global store for messages per conversation (allows switching without losing streamed content)
const conversationMessages = new Map<string, Message[]>();

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [deepResearchProgress, setDeepResearchProgress] = useState<DeepResearchProgress | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ name: string; size: string; type: string }>>([]);
  const currentConvIdRef = useRef<string | null>(null);
  const uploadAbortRef = useRef<AbortController | null>(null); // Separate abort for uploads

  // Keep-alive ping to prevent HF Space cold starts (runs every 30 seconds)
  useEffect(() => {
    const pingBackend = async () => {
      try {
        await fetch(`${API_BASE_URL}/`, { method: 'HEAD' }).catch(() => { });
      } catch { }
    };

    // Initial ping
    pingBackend();

    // Ping every 30 seconds while the app is open
    const interval = setInterval(pingBackend, 30 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync messages to global cache whenever they change
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      conversationMessages.set(conversationId, messages);
    }
  }, [messages, conversationId]);

  // Update loading state when current conversation's stream status changes
  useEffect(() => {
    if (conversationId) {
      setIsLoading(isConversationStreaming(conversationId));
    } else {
      setIsLoading(false);
    }
  }, [conversationId]);

  // Load conversation messages - with stream-aware switching
  const loadConversation = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    console.log(`📖 Loading conversation: ${convId}`);

    // Save current conversation's messages to cache before switching
    if (currentConvIdRef.current && messages.length > 0) {
      conversationMessages.set(currentConvIdRef.current, messages);
    }

    // Update refs and state
    currentConvIdRef.current = convId;
    setConversationId(convId);
    setDeepResearchProgress(null);

    // Check if this conversation has an active stream
    const activeStream = isConversationStreaming(convId);
    if (activeStream) {
      setIsLoading(true);
    }

    // Check if we have cached messages for this conversation
    const cachedMessages = conversationMessages.get(convId);
    if (cachedMessages && cachedMessages.length > 0) {
      setMessages(cachedMessages);
      console.log(`✅ Restored ${cachedMessages.length} cached messages`);
      return; // Use cache, don't fetch
    }

    setMessages([]);
    setIsLoadingConversation(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${convId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        const loadedMessages: Message[] = data.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          attachments: msg.metadata?.attachments || undefined,
        }));
        setMessages(loadedMessages);
        console.log(`✅ Loaded ${loadedMessages.length} messages`);
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        console.log('❌ Token expired');
      } else {
        console.log(`❌ Failed to load: HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('❌ Load conversation error:', error);
    } finally {
      setIsLoadingConversation(false);
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
    // Check if THIS conversation is currently loading (allow sending in other conversations)
    const currentConvLoading = isConversationStreaming(conversationId);
    if (!content.trim() || currentConvLoading) return;

    const token = localStorage.getItem('token');

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
    };

    setMessages(prev => [...prev, userMessage]);
    setUploadedFiles([]); // Clear attachments after sending
    setIsLoading(true);

    // Track the conversation ID for this request (will be set if new conversation is created)
    let streamConversationId = conversationId;

    // Only abort if there's an active stream in THIS conversation
    if (streamConversationId) {
      const existingStream = activeStreams.get(streamConversationId);
      if (existingStream) {
        existingStream.abortController.abort();
        unregisterStream(streamConversationId);
      }
    }

    // Create new abort controller for this stream
    const abortController = new AbortController();
    const signal = abortController.signal;

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

      if (!streamConversationId) {
        const convResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ title: generateConversationTitle(content) }),
        });

        if (convResponse.ok) {
          const convData = await convResponse.json();
          streamConversationId = convData.id;
          setConversationId(convData.id);
          currentConvIdRef.current = convData.id;
          // Optimistically add new conversation to sidebar
          addConversationToList({
            id: convData.id,
            title: convData.title || generateConversationTitle(content),
          });
        } else {
          throw new Error('Failed to create conversation');
        }
      } else {
        // Existing conversation - move it to top of list
        moveConversationToTop(streamConversationId);
      }

      // Register this stream in the global store
      if (streamConversationId) {
        registerStream(streamConversationId, abortController);
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

        const response = await fetch(`${UPLOAD_BASE_URL}/api/v1/ai/deep-research/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            question: content.trim(),
            conversation_id: streamConversationId,
            metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
          }),
          signal,
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
          let isDone = false;
          let buffer = '';
          while (!isDone) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();
                if (data === '[DONE]') {
                  isDone = true;
                  break;
                }

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
                  console.debug('Deep Research: Partial chunk or parse error', data);
                }
              }
            }
          }
        }

        setDeepResearchProgress(null);

        // Re-fetch conversation to ensure we have the latest saved report
        let savedReport = finalReport;
        if (streamConversationId) {
          try {
            const messagesResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${streamConversationId}/messages`, {
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
            conversation_id: streamConversationId,
            mode: mode,
            use_rag: true,
            metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
          }),
          signal,
        });

        if (streamResponse.ok && streamResponse.body) {
          // Add empty assistant message that we'll update
          const assistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          };

          // Helper to update messages (only if still on same conversation)
          const updateMessage = (content: string) => {
            const newMsg = { ...assistantMessage, content };
            // Always update the cache
            const cached = conversationMessages.get(streamConversationId!) || [];
            const existingIdx = cached.findIndex(m => m.id === assistantMessageId);
            if (existingIdx >= 0) {
              cached[existingIdx] = newMsg;
            } else {
              cached.push(newMsg);
            }
            conversationMessages.set(streamConversationId!, cached);

            // Only update UI if still on this conversation
            if (currentConvIdRef.current === streamConversationId) {
              setMessages(prev => prev.map(msg =>
                msg.id === assistantMessageId ? newMsg : msg
              ));
            }
          };

          // Only add to UI if still on same conversation
          if (currentConvIdRef.current === streamConversationId) {
            setMessages(prev => [...prev, assistantMessage]);
          }
          // Always add to cache
          const cached = conversationMessages.get(streamConversationId!) || [];
          cached.push(assistantMessage);
          conversationMessages.set(streamConversationId!, cached);

          // Process SSE stream
          const reader = streamResponse.body.getReader();
          const decoder = new TextDecoder();
          let fullContent = '';
          let buffer = '';
          let isDone = false;
          while (!isDone) {
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
                if (data.trim() === '[DONE]') {
                  isDone = true;
                  break;
                }

                // Skip any JSON log messages that might have leaked into the stream
                if (data.trim().startsWith('{') && data.includes('"timestamp"')) continue;
                if (data.trim().startsWith('{') && data.includes('"level"')) continue;

                // Try to parse as JSON (new format with proper newline handling)
                let textContent = '';
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.text !== undefined) {
                    textContent = parsed.text;
                  } else {
                    // Fallback: treat as raw text
                    textContent = data.replace(/\\n/g, '\n');
                  }
                } catch {
                  // Not JSON - might be legacy format, decode escaped newlines
                  textContent = data.replace(/\\n/g, '\n');
                }

                // Add to content
                fullContent += textContent;
                // Update the message content in real-time (respects current conversation)
                updateMessage(fullContent);
              }
            }
          }

          // Process any remaining buffer
          if (buffer.startsWith('data: ')) {
            const data = buffer.slice(6);
            if (data.trim() !== '[DONE]') {
              // Try to parse as JSON
              let textContent = '';
              try {
                const parsed = JSON.parse(data);
                if (parsed.text !== undefined) {
                  textContent = parsed.text;
                } else {
                  textContent = data.replace(/\\n/g, '\n');
                }
              } catch {
                textContent = data.replace(/\\n/g, '\n');
              }
              fullContent += textContent;
              updateMessage(fullContent);
            }
          }

          // After streaming completes, re-fetch the message to ensure we have the final formatted version
          if (streamConversationId) {
            try {
              const messagesResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${streamConversationId}/messages`, {
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
            conversation_id: streamConversationId,
            mode: mode,
            use_rag: true,
            metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
          }),
          signal,
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
      // Clean up the stream from activeStreams using the tracked ID
      if (streamConversationId) {
        unregisterStream(streamConversationId);
      }
      setIsLoading(false);
    }
  }, [conversationId, uploadedFiles]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setDeepResearchProgress(null); // Reset deep research UI
    // Clear from localStorage as well
    if (typeof window !== 'undefined') {
      localStorage.removeItem('streamConversationId');
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
    let streamConversationId = conversationId;
    if (!streamConversationId) {
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
          streamConversationId = convData.id;
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

    // Create new AbortController for this upload session
    if (uploadAbortRef.current) {
      uploadAbortRef.current.abort();
    }
    uploadAbortRef.current = new AbortController();
    const signal = uploadAbortRef.current.signal;

    try {
      for (let i = 0; i < files.length; i++) {
        if (signal.aborted) break;

        const file = files[i];

        try {
          console.log(`📤 Uploading file: ${file.name} to conversation: ${streamConversationId}`);

          const formData = new FormData();
          formData.append('file', file);

          const uploadUrl = `${UPLOAD_BASE_URL}/api/v1/chat/conversations/${streamConversationId}/documents`;

          const response = await fetch(uploadUrl, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            body: formData,
            signal,
          });

          if (response.ok) {
            console.log(`✅ Upload success: ${file.name}`);

            // Add to uploaded files state for display
            const fileSizeKB = (file.size / 1024).toFixed(1);
            setUploadedFiles(prev => [...prev, {
              name: file.name,
              size: `${fileSizeKB} KB`,
              type: file.type
            }]);

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
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Upload cancelled');
        return [{ fileName: 'Upload', status: 'error', error: 'Upload cancelled by user' }];
      }
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
      uploadAbortRef.current = null;
    }

    return results;
  }, [conversationId]);

  const cancelUpload = useCallback(() => {
    if (uploadAbortRef.current) {
      uploadAbortRef.current.abort();
      uploadAbortRef.current = null;
      setIsUploading(false);
    }
  }, []);

  const stopGeneration = useCallback(() => {
    // Stop the stream for the current conversation
    if (conversationId) {
      const stream = activeStreams.get(conversationId);
      if (stream) {
        stream.abortController.abort();
        unregisterStream(conversationId);
      }
    }
    setIsLoading(false);
    setDeepResearchProgress(null);
  }, [conversationId]);

  const editMessage = useCallback((messageId: string, newContent: string) => {
    setMessages(prev => prev.map(msg =>
      msg.id === messageId
        ? { ...msg, content: newContent }
        : msg
    ));
  }, []);

  const deleteMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  return {
    messages,
    isLoading,
    isLoadingConversation,
    isUploading,
    isDeleting,
    sendMessage,
    stopGeneration,
    clearMessages,
    deleteConversation,
    uploadFiles,
    cancelUpload,
    editMessage,
    deleteMessage,
    conversationId,
    deepResearchProgress,
    selectConversation,
  };
}
