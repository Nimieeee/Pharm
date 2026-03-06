import { useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { Message } from '@/components/chat/ChatMessage';
import { API_BASE_URL, UPLOAD_BASE_URL } from '@/config/api';
import { processSSEStream } from '@/utils/streamReader';
import { TokenStreamer } from '@/utils/TokenStreamer';
import { activeStreams, registerStream, unregisterStream, isConversationStreaming } from './useStreamingState';
import { moveConversationToTop, addConversationToList } from './useSWRChat';
import { Mode, cacheSet, DeepResearchProgress, generateStableClientId } from './useChatState';

function generateConversationTitle(message: string): string {
    const cleaned = message.trim().replace(/\s+/g, ' ');
    if (cleaned.length <= 50) return cleaned;
    const firstSentence = cleaned.match(/^[^.!?]+[.!?]/);
    if (firstSentence && firstSentence[0].length <= 60) return firstSentence[0].replace(/[.!?]$/, '');
    const truncated = cleaned.substring(0, 50);
    const lastSpace = truncated.lastIndexOf(' ');
    return lastSpace > 30 ? truncated.substring(0, lastSpace) + '...' : truncated + '...';
}

// Throttle scroll updates
const SCROLL_THROTTLE_MS = 50;
const CONTENT_UPDATE_THROTTLE_MS = 32; // ~30fps

export function useChatStreaming(state: any) {
    const {
        messages, setMessages,
        setIsLoading,
        conversationId, setConversationId,
        deepResearchProgress, setDeepResearchProgress,
        uploadedFiles, setUploadedFiles,
        branchData, setBranchData,
        activeBranches, setActiveBranches,
        currentConvIdRef,
        lastUpdateRef,
        isSendingRef,
        modeRef,
        mapMessageId,
        getStableKey,
    } = state;

    // Track scroll position to prevent jitter
    const lastScrollTimeRef = useRef<number>(0);

    // fetchBranchInfo was removed as it is obsolete

    const generateImage = async (prompt: string, convId: string) => {
        const token = localStorage.getItem('token');
        if (!token) throw new Error('Authentication required');
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/ai/image-generation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({ prompt, conversation_id: convId })
            });
            if (!response.ok) throw new Error('Image generation failed');
            return await response.json();
        } catch (error) {
            console.error('Image generation error:', error);
            throw error;
        }
    };

    const stopGeneration = useCallback(() => {
        if (conversationId) {
            const stream = activeStreams.get(conversationId);
            if (stream) {
                stream.abortController.abort();
                unregisterStream(conversationId);
            }
            setMessages((prev: Message[]) => {
                if (prev.length > 0) {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg.role === 'assistant') return prev.slice(0, -1);
                }
                return prev;
            });
        }
        setIsLoading(false);
        setDeepResearchProgress(null);
    }, [conversationId, setIsLoading, setMessages, setDeepResearchProgress]);

    const sendMessage = useCallback(async (content: string, mode: Mode = 'detailed', language: string = 'en') => {
        const targetConvId = conversationId || 'new';
        if (isSendingRef.current.has(targetConvId) || !content.trim()) return;

        isSendingRef.current.add(targetConvId);
        modeRef.current = mode;

        let streamConversationId = conversationId;

        try {
            const token = localStorage.getItem('token');
            const parentId = messages.length > 0 && messages[messages.length - 1].id.includes('-') ? messages[messages.length - 1].id : undefined;

            // FIX: Use stable client-side ID that won't change on server response
            const userMessageId = generateStableClientId();
            const userMessage: Message = {
                id: userMessageId,
                role: 'user',
                content: content.trim(),
                timestamp: new Date(),
                attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
            };

            setMessages((prev: Message[]) => [...prev, userMessage]);
            setUploadedFiles([]);
            setIsLoading(true);

            if (streamConversationId) {
                const existingStream = activeStreams.get(streamConversationId);
                if (existingStream) {
                    existingStream.abortController.abort();
                    unregisterStream(streamConversationId);
                }
            }

            const abortController = new AbortController();
            const signal = abortController.signal;

            try {
                if (!token) {
                    const authMessage: Message = { id: generateStableClientId(), role: 'assistant', content: 'Please sign in to use Benchside. Go to /login to authenticate.', timestamp: new Date() };
                    setMessages((prev: Message[]) => [...prev, authMessage]);
                    setIsLoading(false);
                    return;
                }

                if (!streamConversationId) {
                    const convResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                        body: JSON.stringify({ title: generateConversationTitle(content) }),
                    });

                    if (convResponse.ok) {
                        const convData = await convResponse.json();
                        streamConversationId = convData.id;
                        setConversationId(convData.id);
                        currentConvIdRef.current = convData.id;
                        // Swap isSendingRef key so 'new' is no longer locked
                        isSendingRef.current.delete('new');
                        isSendingRef.current.add(streamConversationId);
                        addConversationToList({ id: convData.id, title: convData.title || generateConversationTitle(content) });
                    } else {
                        throw new Error('Failed to create conversation');
                    }
                } else {
                    // CRITICAL FIX: Set currentConvIdRef for existing conversations too!
                    currentConvIdRef.current = streamConversationId;
                    moveConversationToTop(streamConversationId);
                }

                if (streamConversationId) {
                    registerStream(streamConversationId, abortController);
                }

                if (content.trim().startsWith('/image')) {
                    const prompt = content.replace('/image', '').trim();
                    if (!prompt) { setIsLoading(false); return; }
                    try {
                        const assistantMessageId = generateStableClientId();
                        const assistantMessage: Message = { id: assistantMessageId, role: 'assistant', content: '_Generating image..._', timestamp: new Date() };
                        if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => [...prev, assistantMessage]);
                        const result = await generateImage(prompt, streamConversationId);
                        const finalMessage: Message = { ...assistantMessage, content: result.markdown || result.image_url || 'Image generated.' };
                        if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => prev.map(m => m.id === assistantMessage.id ? finalMessage : m));
                        setIsLoading(false);
                        return;
                    } catch (error) {
                        const errorMessage: Message = { id: generateStableClientId(), role: 'assistant', content: 'Failed to generate image. Please try again.', timestamp: new Date() };
                        if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => prev.filter(m => m.content !== '_Generating image..._').concat(errorMessage));
                        setIsLoading(false);
                        return;
                    }
                }

                if (mode === 'deep_research') {
                    let accumulatedState: DeepResearchProgress = { type: 'status', status: 'initializing', message: 'Starting deep research...', progress: 0, steps: [], citations: [], plan_overview: '' };
                    setDeepResearchProgress(accumulatedState);

                    const response = await fetch(`${UPLOAD_BASE_URL}/api/v1/ai/deep-research/stream`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                        body: JSON.stringify({
                            question: content.trim(),
                            conversation_id: streamConversationId,
                            metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
                            language: language,
                        }),
                        signal,
                    });

                    if (!response.ok) {
                        if (response.status === 401) localStorage.removeItem('token');
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.detail || 'Failed to start deep research');
                    }

                    let finalReport = '';
                    const assistantMessageId = generateStableClientId();
                    await processSSEStream(response, {
                        onMeta: (meta) => {
                            // FIX: Don't change user message ID - keep stable client ID
                            // Just update the mapping if needed for backend references
                            if (meta.user_message_id) {
                                mapMessageId?.(userMessageId, meta.user_message_id);
                            }
                            if (meta.assistant_message_id) {
                                mapMessageId?.(assistantMessageId, meta.assistant_message_id);
                            }
                        },
                        onContent: () => { },
                        customParser: (data) => {
                            try {
                                const progress = JSON.parse(data) as DeepResearchProgress;
                                let currentCitations = accumulatedState.citations || [];
                                if (progress.citations && progress.citations.length > 0) {
                                    const newCitations = progress.citations.filter(nc => !currentCitations.some(ec => ec.url === nc.url));
                                    currentCitations = [...currentCitations, ...newCitations];
                                }
                                accumulatedState = {
                                    ...accumulatedState, ...progress,
                                    steps: progress.steps || accumulatedState.steps,
                                    citations: currentCitations,
                                    plan_overview: progress.plan_overview || accumulatedState.plan_overview,
                                };

                                // ALWAYS write to global store (survives conversation switches)
                                const streamEntry = activeStreams.get(streamConversationId);
                                if (streamEntry) {
                                    streamEntry.deepResearchProgress = { ...accumulatedState };
                                }

                                const now = Date.now();
                                if (now - lastUpdateRef.current >= 50) {
                                    // Only update React state if user is viewing this conversation
                                    if (currentConvIdRef.current === streamConversationId) {
                                        setDeepResearchProgress({ ...accumulatedState });
                                    }
                                    lastUpdateRef.current = now;
                                }

                                if (progress.type === 'complete' && progress.report) {
                                    finalReport = progress.report;
                                }
                            } catch (e) { }
                        }
                    });

                    // Research complete — clear progress and add final branch
                    const tempResponseId = assistantMessageId;
                    const finalReportStr = finalReport || 'Deep research completed.';

                    if (currentConvIdRef.current === streamConversationId) {
                        setDeepResearchProgress(null);
                        setBranchData((prev: Map<string, any[]>) => {
                            const newMap = new Map(prev);
                            const branches = newMap.get(userMessageId) || [];
                            const newBranch = {
                                id: tempResponseId,
                                user_message_id: userMessageId,
                                branch_label: String.fromCharCode(65 + Math.min(branches.length, 25)),
                                content: finalReportStr,
                                is_active: true,
                                created_at: new Date().toISOString(),
                                updated_at: new Date().toISOString()
                            };
                            newMap.set(userMessageId, [...branches, newBranch]);
                            return newMap;
                        });
                        setActiveBranches((prev: Map<string, string>) => {
                            const newMap = new Map(prev);
                            newMap.set(userMessageId, tempResponseId);
                            return newMap;
                        });
                    } else {
                        // User navigated away — store the final message for retrieval.
                        // Ideally we should refetch conversation on load, but we can stick it in messages as a fallback
                        const streamEntry = activeStreams.get(streamConversationId);
                        if (streamEntry) {
                            streamEntry.deepResearchProgress = null;
                            const fallbackMsg: Message = { id: assistantMessageId, role: 'assistant', content: finalReportStr, timestamp: new Date() };
                            streamEntry.pendingMessages = [fallbackMsg];
                        }
                    }
                    return;
                }

                // Standard Stream
                const assistantMessageId = generateStableClientId();
                const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                    body: JSON.stringify({
                        message: content.trim(),
                        conversation_id: streamConversationId,
                        mode, use_rag: true,
                        metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
                        language,
                        parent_id: messages.length > 0 ? messages[messages.length - 1].id : undefined,
                    }),
                    signal,
                });

                if (streamResponse.ok && streamResponse.body) {
                    const tempResponseId = assistantMessageId;
                    let currentUserMsgId = userMessageId; // Will map to server ID on meta
                    const isCurrentConv = () => currentConvIdRef.current === streamConversationId;

                    let messageInserted = false;

                    const insertOrUpdateMessage = (fullContent: string) => {
                        if (!isCurrentConv()) return;

                        setBranchData((prev: Map<string, any[]>) => {
                            const newMap = new Map(prev);
                            const branches = newMap.get(currentUserMsgId) || [];
                            const existingIndex = branches.findIndex(b => b.id === tempResponseId);

                            if (existingIndex >= 0) {
                                const newBranches = [...branches];
                                newBranches[existingIndex] = { ...newBranches[existingIndex], content: fullContent };
                                newMap.set(currentUserMsgId, newBranches);
                            } else {
                                const newBranch = {
                                    id: tempResponseId,
                                    user_message_id: currentUserMsgId,
                                    branch_label: String.fromCharCode(65 + Math.min(branches.length, 25)),
                                    content: fullContent,
                                    is_active: true,
                                    created_at: new Date().toISOString(),
                                    updated_at: new Date().toISOString(),
                                };
                                newMap.set(currentUserMsgId, [...branches, newBranch]);
                            }
                            return newMap;
                        });

                        if (!messageInserted) {
                            setActiveBranches((prev: Map<string, string>) => {
                                const newMap = new Map(prev);
                                newMap.set(currentUserMsgId, tempResponseId);
                                return newMap;
                            });
                            messageInserted = true;
                        }
                    };

                    let lastContent = '';

                    let resolveStreamer: () => void;
                    const streamerCompletePromise = new Promise<void>((resolve) => {
                        resolveStreamer = resolve;
                    });

                    const streamer = new TokenStreamer({
                        speed: mode === 'detailed' ? 15 : 25,
                        onUpdate: (streamedText) => {
                            const now = Date.now();
                            if (!messageInserted || now - lastUpdateRef.current >= CONTENT_UPDATE_THROTTLE_MS) {
                                insertOrUpdateMessage(streamedText);
                                lastUpdateRef.current = now;
                            }
                        },
                        onComplete: (finalText) => {
                            insertOrUpdateMessage(lastContent || 'No response generated.');
                            resolveStreamer();
                        }
                    });

                    await processSSEStream(streamResponse, {
                        onMeta: (meta) => {
                            // FIX: Don't change user message ID - just map it for backend references
                            if (meta.user_message_id) {
                                mapMessageId?.(userMessageId, meta.user_message_id);
                            }
                            if (meta.assistant_message_id) {
                                mapMessageId?.(assistantMessageId, meta.assistant_message_id);
                            }
                        },
                        onContent: (fullContent, token) => {
                            lastContent = fullContent;
                            // Add tokens to the buffer
                            if (token) {
                                streamer.addTokens([token]);
                            } else if (!messageInserted) {
                                // Fallback if no specific token provided on first chunk
                                streamer.addTokens([fullContent]);
                            }
                        },
                        onDone: () => {
                            streamer.markComplete();
                        },
                        onError: (error) => {
                            streamer.flush(); // On error, dump immediately
                            throw error;
                        }
                    });

                    await streamerCompletePromise;
                    return;
                } else {
                    throw new Error('Streaming not available or response failed');
                }
            } catch (error: any) {
                if (error.message && (error.message.includes('Conversation not found') || error.message.includes('404'))) {
                    setConversationId(null);
                    currentConvIdRef.current = null;
                    if (typeof window !== 'undefined') localStorage.removeItem('currentConversationId');
                }
                // Do not insert an assistant message into the main array for errors anymore.
                // We should alert via toast or let the branch show the error.
                console.error("Connection error during generation:", error.message);
            } finally {
                if (streamConversationId) unregisterStream(streamConversationId);
                setIsLoading(false);
            }
        } finally {
            isSendingRef.current.delete(targetConvId);
            if (streamConversationId) isSendingRef.current.delete(streamConversationId);
        }
    }, [conversationId, uploadedFiles, messages, mapMessageId]);

    // editMessage was repurposed to regenerateResponse, since users no longer edit their own messages
    // instead, they regenerate a new branch off an existing user message
    const regenerateResponse = useCallback(async (userMessageId: string, overrideContent?: string) => {
        const userMessage = messages.find((m: Message) => m.id === userMessageId);
        if (!userMessage) return;

        const targetMode = userMessage.mode || modeRef.current;
        const token = localStorage.getItem('token');

        // Use overrideContent if provided (for edits), otherwise use message from state
        const contentToSend = overrideContent || userMessage.content;

        if (!token || !conversationId) return;

        try {
            setIsLoading(true);
            const editStartTime = Date.now();
            const streamConversationId = conversationId;
            const abortController = new AbortController();
            registerStream(streamConversationId, abortController);

            try {
                const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                    body: JSON.stringify({
                        message: contentToSend, conversation_id: streamConversationId,
                        mode: targetMode, use_rag: true, language: userMessage.translations ? Object.keys(userMessage.translations)[0] || 'en' : 'en',
                        parent_id: userMessage.parentId || undefined,
                        user_message_id: userMessage.id,
                    }),
                    signal: abortController.signal,
                });

                if (streamResponse.ok && streamResponse.body) {
                    const tempResponseId = generateStableClientId();
                    let currentUserMsgId = userMessage.id;
                    let messageInserted = false;

                    const insertOrUpdateMessage = (fullContent: string) => {
                        if (currentConvIdRef.current !== streamConversationId) return;

                        setBranchData((prev: Map<string, any[]>) => {
                            const newMap = new Map(prev);
                            const branches = newMap.get(currentUserMsgId) || [];
                            const existingIndex = branches.findIndex(b => b.id === tempResponseId);

                            if (existingIndex >= 0) {
                                const newBranches = [...branches];
                                newBranches[existingIndex] = { ...newBranches[existingIndex], content: fullContent };
                                newMap.set(currentUserMsgId, newBranches);
                            } else {
                                const newBranch = {
                                    id: tempResponseId,
                                    user_message_id: currentUserMsgId,
                                    branch_label: String.fromCharCode(65 + Math.min(branches.length, 25)),
                                    content: fullContent,
                                    is_active: true,
                                    created_at: new Date().toISOString(),
                                    updated_at: new Date().toISOString(),
                                };
                                newMap.set(currentUserMsgId, [...branches, newBranch]);
                            }
                            return newMap;
                        });

                        if (!messageInserted) {
                            setActiveBranches((prev: Map<string, string>) => {
                                const newMap = new Map(prev);
                                newMap.set(currentUserMsgId, tempResponseId);
                                return newMap;
                            });
                            messageInserted = true;
                        }
                    };

                    let lastContent = '';

                    let resolveStreamer: () => void;
                    const streamerCompletePromise = new Promise<void>((resolve) => {
                        resolveStreamer = resolve;
                    });

                    const streamer = new TokenStreamer({
                        speed: targetMode === 'deep_research' || targetMode === 'detailed' ? 15 : 25,
                        onUpdate: (streamedText) => {
                            const now = Date.now();
                            if (!messageInserted) {
                                const elapsed = now - editStartTime;
                                if (elapsed < 400) {
                                    setTimeout(() => insertOrUpdateMessage(streamedText), 400 - elapsed);
                                    return;
                                }
                            }
                            if (!messageInserted || now - lastUpdateRef.current >= 150) {
                                insertOrUpdateMessage(streamedText);
                                lastUpdateRef.current = now;
                            }
                        },
                        onComplete: (finalText) => {
                            insertOrUpdateMessage(lastContent || 'No response generated.');
                            resolveStreamer();
                        }
                    });

                    await processSSEStream(streamResponse, {
                        onMeta: (meta) => {
                            // Map the returned IDs if present
                            if (meta.user_message_id) {
                                currentUserMsgId = meta.user_message_id;
                            }
                        },
                        onContent: (fullContent, token) => {
                            lastContent = fullContent;
                            if (token) {
                                streamer.addTokens([token]);
                            } else if (!messageInserted) {
                                streamer.addTokens([fullContent]);
                            }
                        },
                        onDone: () => {
                            streamer.markComplete();
                        },
                        onError: (error) => {
                            streamer.flush();
                            throw error;
                        }
                    });

                    moveConversationToTop(streamConversationId);
                    await streamerCompletePromise;
                }
            } catch (streamError: any) {
                // Ignore aborts
            } finally {
                unregisterStream(streamConversationId);
                setIsLoading(false);
            }
        } catch (error) {
            console.error('Regenerate error:', error);
            setIsLoading(false);
        }
    }, [conversationId, messages, setBranchData, setActiveBranches]);

    const editMessage = useCallback(async (messageId: string, newContent: string) => {
        const token = localStorage.getItem('token');
        if (!token || !conversationId) return;

        try {
            // 1. Update backend content
            const formData = new FormData();
            formData.append('content', newContent);

            const patchResponse = await fetch(`${API_BASE_URL}/api/v1/chat/messages/${messageId}`, {
                method: 'PATCH',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (!patchResponse.ok) throw new Error('Failed to update message content');

            // 2. Update local state
            setMessages((prev: Message[]) =>
                prev.map((m) => (m.id === messageId ? { ...m, content: newContent } : m))
            );

            // 3. Trigger regeneration with edited content (fixes race condition)
            await regenerateResponse(messageId, newContent);
        } catch (error) {
            console.error('Edit error:', error);
            toast.error('Failed to edit message');
        }
    }, [conversationId, setMessages, regenerateResponse]);

    return { sendMessage, stopGeneration, regenerateResponse, editMessage };
}
