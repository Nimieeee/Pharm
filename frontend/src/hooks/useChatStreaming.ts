import { useCallback } from 'react';
import { Message } from '@/components/chat/ChatMessage';
import { API_BASE_URL, UPLOAD_BASE_URL } from '@/config/api';
import { processSSEStream } from '@/utils/streamReader';
import { activeStreams, registerStream, unregisterStream, isConversationStreaming } from './useStreamingState';
import { moveConversationToTop, addConversationToList } from './useSWRChat';
import { Mode, cacheSet, DeepResearchProgress } from './useChatState';

function generateConversationTitle(message: string): string {
    const cleaned = message.trim().replace(/\s+/g, ' ');
    if (cleaned.length <= 50) return cleaned;
    const firstSentence = cleaned.match(/^[^.!?]+[.!?]/);
    if (firstSentence && firstSentence[0].length <= 60) return firstSentence[0].replace(/[.!?]$/, '');
    const truncated = cleaned.substring(0, 50);
    const lastSpace = truncated.lastIndexOf(' ');
    return lastSpace > 30 ? truncated.substring(0, lastSpace) + '...' : truncated + '...';
}

export function useChatStreaming(state: any) {
    const {
        messages, setMessages,
        setIsLoading,
        conversationId, setConversationId,
        deepResearchProgress, setDeepResearchProgress,
        uploadedFiles, setUploadedFiles,
        branchMap, setBranchMap,
        currentConvIdRef,
        lastUpdateRef,
        isSendingRef, // Now a Set<string>
        modeRef
    } = state;

    const fetchBranchInfo = useCallback(async (convId: string) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;
            const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat/conversations/${convId}/branch-info`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setBranchMap(data);
            }
        } catch (e) {
            console.error('Failed to fetch branch info', e);
        }
    }, [setBranchMap]);

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

        try {
            const token = localStorage.getItem('token');

            const userMessage: Message = {
                id: Date.now().toString(),
                role: 'user',
                content: content.trim(),
                timestamp: new Date(),
                attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
            };

            setMessages((prev: Message[]) => [...prev, userMessage]);
            setUploadedFiles([]);
            setIsLoading(true);

            let streamConversationId = conversationId;

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
                    const authMessage: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: 'Please sign in to use PharmGPT. Go to /login to authenticate.', timestamp: new Date() };
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
                        addConversationToList({ id: convData.id, title: convData.title || generateConversationTitle(content) });
                    } else {
                        throw new Error('Failed to create conversation');
                    }
                } else {
                    moveConversationToTop(streamConversationId);
                }

                if (streamConversationId) {
                    registerStream(streamConversationId, abortController);
                }

                if (content.trim().startsWith('/image')) {
                    const prompt = content.replace('/image', '').trim();
                    if (!prompt) { setIsLoading(false); return; }
                    try {
                        const assistantMessage: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: '_Generating image..._', timestamp: new Date() };
                        if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => [...prev, assistantMessage]);
                        const result = await generateImage(prompt, streamConversationId);
                        const finalMessage: Message = { ...assistantMessage, content: result.markdown || result.image_url || 'Image generated.' };
                        if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => prev.map(m => m.id === assistantMessage.id ? finalMessage : m));
                        setIsLoading(false);
                        return;
                    } catch (error) {
                        const errorMessage: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: 'Failed to generate image. Please try again.', timestamp: new Date() };
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
                    await processSSEStream(response, {
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

                                const now = Date.now();
                                if (now - lastUpdateRef.current >= 50) {
                                    setDeepResearchProgress({ ...accumulatedState });
                                    lastUpdateRef.current = now;
                                }

                                if (progress.type === 'complete' && progress.report) {
                                    finalReport = progress.report;
                                }
                            } catch (e) { }
                        }
                    });

                    setDeepResearchProgress(null);
                    const assistantMessage: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: finalReport || 'Deep research completed.', timestamp: new Date() };
                    setMessages((prev: Message[]) => [...prev, assistantMessage]);
                    return;
                }

                // Standard Stream
                const assistantMessageId = (Date.now() + 1).toString();
                const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                    body: JSON.stringify({
                        message: content.trim(),
                        conversation_id: streamConversationId,
                        mode, use_rag: true,
                        metadata: uploadedFiles.length > 0 ? { attachments: uploadedFiles } : undefined,
                        language,
                        parent_id: messages.length > 0 && messages[messages.length - 1].id.includes('-') ? messages[messages.length - 1].id : undefined,
                    }),
                    signal,
                });

                if (streamResponse.ok && streamResponse.body) {
                    const assistantMessage: Message = { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date() };
                    const isCurrentConv = () => currentConvIdRef.current === streamConversationId;

                    const updateMessage = (fullContent: string) => {
                        const newMsg = { ...assistantMessage, content: fullContent };
                        if (isCurrentConv()) {
                            setMessages((prev: Message[]) => {
                                const exists = prev.some(m => m.id === assistantMessageId);
                                return exists ? prev.map(m => m.id === assistantMessageId ? newMsg : m) : [...prev, newMsg];
                            });
                        }
                    };

                    if (isCurrentConv()) setMessages((prev: Message[]) => [...prev, assistantMessage]);

                    let lastContent = '';
                    await processSSEStream(streamResponse, {
                        onMeta: (meta) => {
                            if (meta.user_message_id) {
                                setMessages((prev: Message[]) => prev.map(msg => msg.id === userMessage.id ? { ...msg, id: meta.user_message_id } : msg));
                            }
                        },
                        onContent: (fullContent) => {
                            lastContent = fullContent;
                            const now = Date.now();
                            if (now - lastUpdateRef.current >= 100) {
                                updateMessage(fullContent);
                                lastUpdateRef.current = now;
                            }
                        },
                        onDone: () => updateMessage(lastContent)
                    });
                    updateMessage(lastContent);
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
                const errorMessage: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: error.message || 'Connection error', timestamp: new Date() };
                setMessages((prev: Message[]) => [...prev, errorMessage]);
            } finally {
                if (streamConversationId) unregisterStream(streamConversationId);
                setIsLoading(false);
            }
        } finally {
            isSendingRef.current.delete(conversationId || 'new');
            if (conversationId) isSendingRef.current.delete(conversationId);
        }
    }, [conversationId, uploadedFiles, messages]);

    const editMessage = useCallback(async (messageId: string, newContent: string) => {
        const messageToEdit = messages.find((m: Message) => m.id === messageId);
        const targetMode = messageToEdit?.mode || modeRef.current;
        const token = localStorage.getItem('token');

        if (!token || !conversationId) {
            setMessages((prev: Message[]) => prev.map(msg => msg.id === messageId ? { ...msg, content: newContent } : msg));
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat/conversations/${conversationId}/messages/${messageId}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                body: JSON.stringify({ new_content: newContent, mode: targetMode }),
            });

            if (!response.ok) {
                setMessages((prev: Message[]) => prev.map(msg => msg.id === messageId ? { ...msg, content: newContent } : msg));
                return;
            }

            const branchData = await response.json();
            setMessages((prev: Message[]) => {
                const editIdx = prev.findIndex(m => m.id === messageId);
                if (editIdx < 0) return prev;
                const before = prev.slice(0, editIdx);
                const newUserMsg: Message = {
                    id: branchData.id, role: 'user', content: newContent,
                    parentId: branchData.parent_id || undefined,
                    timestamp: new Date(branchData.created_at || Date.now()),
                    mode: targetMode,
                };
                return [...before, newUserMsg];
            });

            setIsLoading(true);
            const streamConversationId = conversationId;
            const abortController = new AbortController();
            registerStream(streamConversationId, abortController);

            try {
                const streamResponse = await fetch(`${API_BASE_URL}/api/v1/ai/chat/stream`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                    body: JSON.stringify({
                        message: newContent, conversation_id: streamConversationId,
                        mode: targetMode, use_rag: true, language: 'en',
                        parent_id: branchData.id,
                    }),
                    signal: abortController.signal,
                });

                if (streamResponse.ok && streamResponse.body) {
                    const assistantMessageId = (Date.now() + 1).toString();
                    const assistantMessage: Message = { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date() };

                    if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => [...prev, assistantMessage]);

                    let lastContent = '';
                    await processSSEStream(streamResponse, {
                        onContent: (fullContent) => {
                            lastContent = fullContent;
                            const now = Date.now();
                            if (now - lastUpdateRef.current >= 100) {
                                if (currentConvIdRef.current === streamConversationId) {
                                    setMessages((prev: Message[]) => prev.map(m => m.id === assistantMessageId ? { ...assistantMessage, content: fullContent } : m));
                                }
                                lastUpdateRef.current = now;
                            }
                        },
                        onDone: () => {
                            if (currentConvIdRef.current === streamConversationId) {
                                setMessages((prev: Message[]) => prev.map(m => m.id === assistantMessageId ? { ...assistantMessage, content: lastContent } : m));
                            }
                        }
                    });

                    fetchBranchInfo(streamConversationId);
                    moveConversationToTop(streamConversationId);
                }
            } catch (streamError: any) {
                if (streamError.name !== 'AbortError') {
                    setMessages((prev: Message[]) => [...prev, { id: 'err', role: 'assistant', content: 'Connection lost.', timestamp: new Date() }]);
                }
            } finally {
                unregisterStream(streamConversationId);
                setIsLoading(false);
            }
        } catch (error) {
            console.error('Edit error:', error);
            setIsLoading(false);
        }
    }, [conversationId, messages]);

    return { sendMessage, stopGeneration, editMessage, fetchBranchInfo };
}
