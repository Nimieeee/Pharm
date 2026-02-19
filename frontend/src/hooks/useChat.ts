'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Message } from '@/components/chat/ChatMessage';
import { moveConversationToTop, addConversationToList } from './useSWRChat';

import { API_BASE_URL, UPLOAD_BASE_URL } from '@/config/api';

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

import { activeStreams, registerStream, unregisterStream, isConversationStreaming, notifyStreamChange } from './useStreamingState';

// Global store for messages per conversation (LRU-capped to avoid memory leaks)
const MAX_CACHED_CONVERSATIONS = 20;
const conversationMessages = new Map<string, Message[]>();

/** Enforce LRU eviction on the global message cache */
function cacheSet(key: string, value: Message[]) {
  // Delete-then-set moves the key to "most recent" in Map insertion order
  conversationMessages.delete(key);
  conversationMessages.set(key, value);
  // Evict oldest entries beyond the cap
  while (conversationMessages.size > MAX_CACHED_CONVERSATIONS) {
    const oldest = conversationMessages.keys().next().value;
    if (oldest) conversationMessages.delete(oldest);
  }
}

/** Clear the global message cache (call on logout) */
export function clearMessageCache() {
  conversationMessages.clear();
}

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
  const lastUpdateRef = useRef<number>(0); // For throttling updates
  const isSendingRef = useRef(false); // Debounce sendMessage
  // Branch navigation: maps messageId → { branchIndex, branchCount, siblingIds }
  const [branchMap, setBranchMap] = useState<Record<string, { branchIndex: number; branchCount: number; siblingIds: string[] }>>({});
  const modeRef = useRef<Mode>('detailed'); // Track current mode for edit-regenerate

  // Keep-alive ping to prevent HF Space cold starts (runs every 30 seconds)
  useEffect(() => {
    let failCount = 0;
    const pingBackend = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/`, { method: 'HEAD' });
        if (!res.ok) {
          failCount++;
          if (failCount >= 3) console.warn(`[Health] Backend ping failed ${failCount} times`);
        } else {
          failCount = 0;
        }
      } catch {
        failCount++;
        if (failCount >= 3) console.warn(`[Health] Backend unreachable (${failCount} failures)`);
      }
    };

    pingBackend();
    const interval = setInterval(pingBackend, 30 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync messages to global cache whenever they change (uses LRU cache)
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      cacheSet(conversationId, messages);
    }
  }, [messages, conversationId]);

  // Update loading state reactively when streaming state changes
  useEffect(() => {
    const update = () => {
      if (conversationId) {
        setIsLoading(isConversationStreaming(conversationId));
      } else {
        setIsLoading(false);
      }
    };
    update();
    // Subscribe to streaming state changes for reactive updates
    const subscribers = (globalThis as any).__streamSubscribers;
    if (subscribers) {
      subscribers.add(update);
      return () => { subscribers.delete(update); };
    }
  }, [conversationId]);

  // Image Generation Service Call
  const generateImage = async (prompt: string, convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) throw new Error('Authentication required');

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/image-generation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt,
          conversation_id: convId
        })
      });

      if (!response.ok) {
        throw new Error('Image generation failed');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Image generation error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Load conversation messages - with stream-aware switching
  const loadConversation = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    console.log(`📖 Loading conversation: ${convId}`);

    // Save current conversation's messages to cache before switching
    // (reads from ref to avoid stale closure — the sync effect above keeps the cache hot)
    const prevId = currentConvIdRef.current;

    // Concurrency fix: DO NOT abort the previous stream. Let it run in the background.
    // The streaming loop is guarded by (currentConvIdRef.current === streamConversationId)
    // so it won't bleed into the UI, but it WILL update the cache.


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
      // return; // REMOVED: Always fetch latest to support language switching
    }

    if (!cachedMessages || cachedMessages.length === 0) {
      setMessages([]);
      setIsLoadingConversation(true);
    }

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
          parentId: msg.parent_id || undefined,
          translations: msg.translations || undefined,
          timestamp: new Date(msg.created_at),
          attachments: msg.metadata?.attachments || undefined,
        }));
        setMessages(loadedMessages);
        console.log(`✅ Loaded ${loadedMessages.length} messages`);

        // Fetch branch info after loading messages
        fetchBranchInfo(convId);
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        console.log('❌ Token expired');
      } else if (response.status === 404) {
        console.log('❌ Conversation not found, resetting state');
        setConversationId(null);
        currentConvIdRef.current = null;
        if (typeof window !== 'undefined') {
          localStorage.removeItem('currentConversationId');
        }
        setMessages([]);
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

  const sendMessage = useCallback(async (content: string, mode: Mode = 'detailed', language: string = 'en') => {
    // Check if THIS conversation is currently loading (allow sending in other conversations)
    const currentConvLoading = isConversationStreaming(conversationId);

    // Prevent double sending
    if (isSendingRef.current || !content.trim() || currentConvLoading) return;

    isSendingRef.current = true;
    modeRef.current = mode; // Sync for edit-regenerate

    try {
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

        // Handle Image Generation Command
        if (content.trim().startsWith('/image')) {
          const prompt = content.replace('/image', '').trim();

          // Ensure we don't fall through even if prompt is empty
          if (!prompt) {
            setIsLoading(false);
            return;
          }

          if (prompt && streamConversationId) {
            try {
              // Add assistant placeholder
              const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '_Generating image..._',
                timestamp: new Date(),
              };

              // Optimistically add to UI if current
              if (currentConvIdRef.current === streamConversationId) {
                setMessages(prev => [...prev, assistantMessage]);
              }

              const result = await generateImage(prompt, streamConversationId);

              // Update with actual result
              const finalMessage: Message = {
                ...assistantMessage,
                content: result.markdown || result.image_url || 'Image generated.'
              };

              // Update UI
              if (currentConvIdRef.current === streamConversationId) {
                setMessages(prev => prev.map(m => m.id === assistantMessage.id ? finalMessage : m));
              }

              setIsLoading(false);
              return; // Success
            } catch (error) {
              console.error('Image generation error:', error);
              const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Failed to generate image. Please try again.',
                timestamp: new Date(),
              };
              if (currentConvIdRef.current === streamConversationId) {
                setMessages(prev => prev.filter(m => m.content !== '_Generating image..._').concat(errorMessage));
              }
              setIsLoading(false);
              return;
            }
          }
          return; // Catch-all return for /image command
        }

        // ... continue ...


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
              language: language,
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
                    let currentCitations = accumulatedState.citations || [];
                    if (progress.citations && progress.citations.length > 0) {
                      // Merge new citations avoiding duplicates by URL
                      const newCitations = progress.citations.filter(
                        nc => !currentCitations.some(ec => ec.url === nc.url)
                      );
                      currentCitations = [...currentCitations, ...newCitations];
                    }

                    accumulatedState = {
                      ...accumulatedState,
                      ...progress,
                      // Preserve and update accumulated data
                      steps: progress.steps || accumulatedState.steps,
                      citations: currentCitations,
                      plan_overview: progress.plan_overview || accumulatedState.plan_overview,
                    };

                    // Throttled UI Update (every 50ms)
                    const now = Date.now();
                    if (now - lastUpdateRef.current >= 50) {
                      setDeepResearchProgress({ ...accumulatedState });
                      lastUpdateRef.current = now;
                    }

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
              language: language,
              // Only send parent_id if it's a real DB UUID (contains hyphens), not a temporary frontend ID
              parent_id: messages.length > 0 && messages[messages.length - 1].id.includes('-')
                ? messages[messages.length - 1].id
                : undefined,
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
              cacheSet(streamConversationId!, cached);

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
            cacheSet(streamConversationId!, cached);

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

                  // Handle Meta events (e.g. user_message_id)
                  if (data.trim().startsWith('{"type": "meta"')) {
                    try {
                      const meta = JSON.parse(data);
                      if (meta.user_message_id) {
                        // Update the temporary user message ID with the real DB UUID
                        const realId = meta.user_message_id;
                        setMessages(prev => prev.map(msg =>
                          msg.id === userMessage.id ? { ...msg, id: realId } : msg
                        ));
                        // Also update cache if needed
                        const cached = conversationMessages.get(streamConversationId!) || [];
                        const userMsgIdx = cached.findIndex(m => m.id === userMessage.id);
                        if (userMsgIdx >= 0) {
                          cached[userMsgIdx] = { ...cached[userMsgIdx], id: realId };
                          cacheSet(streamConversationId!, cached);
                        }
                      }
                    } catch (e) {
                      console.error('Failed to parse meta event:', e);
                    }
                    continue;
                  }

                  // Skip any JSON log messages that might have leaked into the stream
                  if (data.trim().startsWith('{') && (data.includes('"timestamp"') || data.includes('"level"'))) continue;

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

                  // Throttled UI Update (every 100ms - 10fps for better performance)
                  const now = Date.now();
                  if (now - lastUpdateRef.current >= 100) {
                    updateMessage(fullContent);
                    lastUpdateRef.current = now;
                  }
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
              }
            }

            // Final update to ensure we have everything
            updateMessage(fullContent);

            // After streaming completes, we already have the full content in the state
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
              language: language,
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

        // Handle "Conversation not found" by resetting state so user can start fresh
        if (error.message && (error.message.includes('Conversation not found') || error.message.includes('404'))) {
          console.warn('Conversation lost during send, resetting state');
          setConversationId(null);
          currentConvIdRef.current = null;
          if (typeof window !== 'undefined') {
            localStorage.removeItem('currentConversationId');
          }
        }

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
    } finally {
      isSendingRef.current = false;
    }
  }, [conversationId, uploadedFiles]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    currentConvIdRef.current = null;
    setDeepResearchProgress(null); // Reset deep research UI
    // Clear from localStorage as well
    if (typeof window !== 'undefined') {
      localStorage.removeItem('streamConversationId');
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

  const cancelledUploadsRef = useRef<Set<string>>(new Set());

  const removeFile = useCallback((fileName: string) => {
    cancelledUploadsRef.current.add(fileName);
    setUploadedFiles(prev => prev.filter(f => f.name !== fileName));
  }, []);

  const uploadFiles = useCallback(async (files: FileList) => {
    const token = localStorage.getItem('token');
    if (!token) {
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

    // Create new AbortController for this upload session if one doesn't exist
    if (!uploadAbortRef.current) {
      uploadAbortRef.current = new AbortController();
    }
    const signal = uploadAbortRef.current.signal;

    try {
      const uploadPromises = Array.from(files).map(async (file) => {
        if (cancelledUploadsRef.current.has(file.name)) {
          console.log(`🚫 Upload cancelled before start: ${file.name}`);
          return;
        }

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

          if (cancelledUploadsRef.current.has(file.name)) {
            console.log(`🚫 Upload cancelled after finish: ${file.name}`);
            return;
          }

          if (response.ok) {
            console.log(`✅ Upload success: ${file.name}`);

            // Add to uploaded files state for display
            const fileSizeKB = (file.size / 1024).toFixed(1);
            setUploadedFiles(prev => {
              if (prev.some(f => f.name === file.name)) return prev;

              return [...prev, {
                name: file.name,
                size: `${fileSizeKB} KB`,
                type: file.type
              }];
            });

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
          if (error.name === 'AbortError' || cancelledUploadsRef.current.has(file.name)) {
            console.log(`Upload cancelled: ${file.name}`);
            return;
          }
          console.error(`❌ Upload exception:`, error);
          results.push({ fileName: file.name, status: 'error', error: error.message || 'Network error' });
        }
      });

      await Promise.all(uploadPromises);

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Upload cancelled');
        return [{ fileName: 'Upload', status: 'error', error: 'Upload cancelled by user' }];
      }
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }

    return results;
  }, [conversationId]);

  const cancelUpload = useCallback(() => {
    if (uploadAbortRef.current) {
      uploadAbortRef.current.abort();
      uploadAbortRef.current = null;
    }
    setIsUploading(false);
    cancelledUploadsRef.current.clear();
  }, []);
  const stopGeneration = useCallback(() => {
    // Stop the stream for the current conversation
    if (conversationId) {
      const stream = activeStreams.get(conversationId);
      if (stream) {
        stream.abortController.abort();
        unregisterStream(conversationId);
      }

      // Remove the partial assistant message from UI
      setMessages(prev => {
        if (prev.length > 0) {
          const lastMsg = prev[prev.length - 1];
          // Only remove if it's an assistant message (the one being streamed)
          if (lastMsg.role === 'assistant') {
            return prev.slice(0, -1);
          }
        }
        return prev;
      });
    }
    setIsLoading(false);
    setDeepResearchProgress(null);
  }, [conversationId]);

  const editMessage = useCallback(async (messageId: string, newContent: string) => {
    const token = localStorage.getItem('token');
    if (!token || !conversationId) {
      // Fallback to local edit if no auth/conversation
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, content: newContent } : msg
      ));
      return;
    }

    try {
      // 1. POST to /edit endpoint to create a new branch
      const response = await fetch(
        `${API_BASE_URL}/api/v1/ai/chat/conversations/${conversationId}/messages/${messageId}/edit`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ new_content: newContent }),
        }
      );

      if (!response.ok) {
        console.error('Failed to create branch:', response.status);
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, content: newContent } : msg
        ));
        return;
      }

      const branchData = await response.json();
      console.log(`✏️ Branch created: ${branchData.id}, parent: ${branchData.parent_id}`);

      // 2. Truncate messages: keep everything BEFORE the edited message,
      //    then append the new branch message
      setMessages(prev => {
        const editIdx = prev.findIndex(m => m.id === messageId);
        if (editIdx < 0) return prev;
        const before = prev.slice(0, editIdx);
        const newUserMsg: Message = {
          id: branchData.id,
          role: 'user',
          content: newContent,
          parentId: branchData.parent_id || undefined,
          timestamp: new Date(branchData.created_at || Date.now()),
        };
        return [...before, newUserMsg];
      });

      // 3. Immediately trigger AI regeneration via streaming
      setIsLoading(true);
      const streamConversationId = conversationId;
      const abortController = new AbortController();

      // Register this stream
      registerStream(streamConversationId, abortController);

      try {
        const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: newContent,
            conversation_id: streamConversationId,
            mode: modeRef.current,
            use_rag: true,
            language: 'en',
            parent_id: branchData.id,  // Chain AI response to the new branch
          }),
          signal: abortController.signal,
        });

        if (streamResponse.ok && streamResponse.body) {
          const assistantMessageId = (Date.now() + 1).toString();
          const assistantMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          };

          // Add empty assistant message
          if (currentConvIdRef.current === streamConversationId) {
            setMessages(prev => [...prev, assistantMessage]);
          }

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
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data.trim() === '[DONE]') { isDone = true; break; }
                if (data.trim().startsWith('{') && (data.includes('"timestamp"') || data.includes('"level"'))) continue;

                let textContent = '';
                try {
                  const parsed = JSON.parse(data);
                  textContent = parsed.text !== undefined ? parsed.text : data.replace(/\\n/g, '\n');
                } catch {
                  textContent = data.replace(/\\n/g, '\n');
                }

                fullContent += textContent;
                const now = Date.now();
                if (now - lastUpdateRef.current >= 100) {
                  const newMsg = { ...assistantMessage, content: fullContent };
                  if (currentConvIdRef.current === streamConversationId) {
                    setMessages(prev => prev.map(m => m.id === assistantMessageId ? newMsg : m));
                  }
                  lastUpdateRef.current = now;
                }
              }
            }
          }

          // Final update
          const finalMsg = { ...assistantMessage, content: fullContent };
          if (currentConvIdRef.current === streamConversationId) {
            setMessages(prev => prev.map(m => m.id === assistantMessageId ? finalMsg : m));
          }

          // Refresh branch info after edit
          fetchBranchInfo(streamConversationId);

          // Invalidate SWR conversation cache
          moveConversationToTop(streamConversationId);
        }
      } catch (streamError: any) {
        if (streamError.name !== 'AbortError') {
          console.error('Edit streaming error:', streamError);
          const errorMsg: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: 'Failed to regenerate response after edit. Please try again.',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMsg]);
        }
      } finally {
        unregisterStream(streamConversationId);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Edit/branch error:', error);
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, content: newContent } : msg
      ));
    }
  }, [conversationId]);

  // Fetch branch info for a conversation
  const fetchBranchInfo = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/ai/chat/conversations/${convId}/branch-info`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setBranchMap(data || {});
      }
    } catch (e) {
      console.warn('Failed to fetch branch info:', e);
    }
  }, []);

  // Navigate to a sibling branch
  const navigateBranch = useCallback(async (messageId: string, direction: 'prev' | 'next') => {
    const info = branchMap[messageId];
    if (!info) return;

    const currentIdx = info.siblingIds.indexOf(messageId);
    const newIdx = direction === 'prev' ? currentIdx - 1 : currentIdx + 1;
    if (newIdx < 0 || newIdx >= info.siblingIds.length) return;

    const siblingId = info.siblingIds[newIdx];
    const token = localStorage.getItem('token');
    if (!token || !conversationId) return;

    try {
      // Fetch the thread from the sibling message downward
      const res = await fetch(
        `${API_BASE_URL}/api/v1/ai/chat/conversations/${conversationId}/messages/${siblingId}/thread`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const threadData = await res.json();
        const threadMessages: Message[] = threadData.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          parentId: msg.parent_id || undefined,
          translations: msg.translations || msg.metadata?.translations || undefined,
          timestamp: new Date(msg.created_at),
          attachments: msg.metadata?.attachments || undefined,
        }));
        setMessages(threadMessages);
      }
    } catch (e) {
      console.error('Branch navigation failed:', e);
    }
  }, [branchMap, conversationId]);

  const deleteMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  }, []);

  return {
    messages,
    isLoading,
    isConversationLoading: (id: string) => activeStreams.has(id) || (id === conversationId && isLoading),
    isLoadingConversation,
    isUploading,
    isDeleting,
    sendMessage,
    stopGeneration,
    clearMessages,
    deleteConversation,
    uploadFiles,
    cancelUpload,
    removeFile,
    editMessage,
    deleteMessage,
    conversationId,
    deepResearchProgress,
    selectConversation,
    branchMap,
    navigateBranch,
  };
}
