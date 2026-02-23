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
            const parentId = messages.length > 0 && messages[messages.length - 1].id.includes('-') ? messages[messages.length - 1].id : undefined;

            const userMessage: Message = {
                id: Date.now().toString(),
                role: 'user',
                content: content.trim(),
                timestamp: new Date(),
                attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
                parentId: parentId,
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
                    let assistantMessage: Message = { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date(), parentId: userMessage.id };
                    const isCurrentConv = () => currentConvIdRef.current === streamConversationId;

                    // Track the message by position instead of ID to avoid race conditions
                    let messagePosition = -1;
                    let updateCallCount = 0;
                    let lastStateSnapshot: Message[] | null = null;

                    const updateMessage = (fullContent: string) => {
                        updateCallCount++;
                        console.log(`🔄 [${updateCallCount}] updateMessage called: ${fullContent.length} chars, ID: ${assistantMessage.id}, convMatch: ${isCurrentConv()}`);
                        
                        if (!isCurrentConv()) {
                            console.log(`  ⚠️ [${updateCallCount}] Not current conversation (current: ${currentConvIdRef.current}, target: ${streamConversationId}), skipping update`);
                            return;
                        }
                        
                        setMessages((prev: Message[]) => {
                            console.log(`  📊 [${updateCallCount}] setMessages callback executing, prev.length: ${prev.length}`);
                            
                            // Check if state actually changed since last update
                            if (lastStateSnapshot && prev === lastStateSnapshot) {
                                console.warn(`  ⚠️ [${updateCallCount}] State reference unchanged - React may not be re-rendering!`);
                            }
                            
                            // Log all message IDs in current state
                            console.log(`  📋 [${updateCallCount}] Current message IDs:`, prev.map(m => `${m.role}:${m.id.substring(0, 8)}`));
                            
                            // If we know the position, use it directly
                            if (messagePosition >= 0 && messagePosition < prev.length) {
                                const msg = prev[messagePosition];
                                console.log(`  🎯 [${updateCallCount}] Checking position ${messagePosition}: role=${msg.role}, id=${msg.id.substring(0, 8)}, contentLen=${msg.content.length}`);
                                if (msg.role === 'assistant') {
                                    console.log(`  ✅ [${updateCallCount}] Updating by position ${messagePosition}, old content: ${msg.content.length} chars, new: ${fullContent.length} chars`);
                                    const updated = [...prev];
                                    updated[messagePosition] = { ...msg, content: fullContent };
                                    lastStateSnapshot = updated;
                                    return updated;
                                } else {
                                    console.warn(`  ⚠️ [${updateCallCount}] Position ${messagePosition} is not assistant (role: ${msg.role}), falling back to ID search`);
                                }
                            }
                            
                            // Fallback: find by ID
                            const targetId = assistantMessage.id;
                            console.log(`  🔍 [${updateCallCount}] Searching for ID: ${targetId.substring(0, 8)}`);
                            const index = prev.findIndex(m => m.id === targetId);
                            if (index >= 0) {
                                console.log(`  ✅ [${updateCallCount}] Found by ID at position ${index}`);
                                messagePosition = index; // Cache the position
                                const updated = [...prev];
                                updated[index] = { ...prev[index], content: fullContent };
                                lastStateSnapshot = updated;
                                return updated;
                            }
                            
                            // Last resort: find last assistant message
                            const lastAssistantIndex = prev.length - 1;
                            if (lastAssistantIndex >= 0 && prev[lastAssistantIndex].role === 'assistant') {
                                console.log(`  ⚠️ [${updateCallCount}] Using last assistant message at position ${lastAssistantIndex}, id: ${prev[lastAssistantIndex].id.substring(0, 8)}`);
                                messagePosition = lastAssistantIndex;
                                const updated = [...prev];
                                updated[lastAssistantIndex] = { ...prev[lastAssistantIndex], content: fullContent };
                                lastStateSnapshot = updated;
                                return updated;
                            }
                            
                            console.error(`  ❌ [${updateCallCount}] Could not find message to update! Looking for ID: ${targetId.substring(0, 8)}`);
                            console.error(`  ❌ [${updateCallCount}] Available IDs:`, prev.map(m => m.id.substring(0, 8)));
                            lastStateSnapshot = prev;
                            return prev;
                        });
                    };

                    if (isCurrentConv()) {
                        setMessages((prev: Message[]) => {
                            const newMessages = [...prev, assistantMessage];
                            messagePosition = newMessages.length - 1; // Cache the position
                            console.log(`📍 Added assistant message at position ${messagePosition}, ID: ${assistantMessage.id.substring(0, 8)}, total messages: ${newMessages.length}`);
                            console.log(`📍 Message IDs after add:`, newMessages.map(m => `${m.role}:${m.id.substring(0, 8)}`));
                            return newMessages;
                        });
                    } else {
                        console.warn(`⚠️ Not current conversation when adding assistant message`);
                    }

                    let lastContent = '';
                    let chunkCount = 0;
                    console.log('📡 Starting SSE stream processing...');
                    
                    await processSSEStream(streamResponse, {
                        onMeta: (meta) => {
                            console.log('📋 Received meta:', meta);
                            if (meta.user_message_id) {
                                console.log(`🔄 Updating user message ID: ${userMessage.id.substring(0, 8)} -> ${meta.user_message_id.substring(0, 8)}`);
                                setMessages((prev: Message[]) => {
                                    const updated = prev.map(msg => msg.id === userMessage.id ? { ...msg, id: meta.user_message_id } : msg);
                                    console.log(`  User message updated in state, new IDs:`, updated.map(m => `${m.role}:${m.id.substring(0, 8)}`));
                                    return updated;
                                });
                                userMessage.id = meta.user_message_id;
                                assistantMessage.parentId = meta.user_message_id;
                            }
                            if (meta.assistant_message_id) {
                                const oldId = assistantMessage.id;
                                assistantMessage.id = meta.assistant_message_id;
                                console.log(`🔄 Updated assistant message ID: ${oldId.substring(0, 8)} -> ${meta.assistant_message_id.substring(0, 8)}`);
                                console.log(`🔄 Message position cached: ${messagePosition}`);
                                // Update the ID in state using position
                                setMessages((prev: Message[]) => {
                                    console.log(`  Updating assistant ID in state, position: ${messagePosition}, prev.length: ${prev.length}`);
                                    if (messagePosition >= 0 && messagePosition < prev.length) {
                                        const updated = [...prev];
                                        updated[messagePosition] = { ...prev[messagePosition], id: meta.assistant_message_id, parentId: meta.user_message_id };
                                        console.log(`  ✅ Updated by position, new IDs:`, updated.map(m => `${m.role}:${m.id.substring(0, 8)}`));
                                        return updated;
                                    }
                                    // Fallback to ID-based update
                                    console.log(`  ⚠️ Position invalid, using ID-based update`);
                                    const updated = prev.map(msg => msg.id === oldId ? { ...msg, id: meta.assistant_message_id, parentId: meta.user_message_id } : msg);
                                    console.log(`  Updated by ID, new IDs:`, updated.map(m => `${m.role}:${m.id.substring(0, 8)}`));
                                    return updated;
                                });
                            }
                        },
                        onContent: (fullContent) => {
                            chunkCount++;
                            if (chunkCount === 1) {
                                console.log('🎉 First content chunk received!');
                            }
                            lastContent = fullContent;
                            const now = Date.now();
                            if (now - lastUpdateRef.current >= 150) {
                                updateMessage(fullContent);
                                lastUpdateRef.current = now;
                            }
                        },
                        onDone: () => {
                            console.log(`✅ Stream complete! Total chunks: ${chunkCount}`);
                            updateMessage(lastContent);
                        },
                        onError: (error) => {
                            console.error('❌ Stream error:', error);
                            throw error;
                        }
                    });
                    updateMessage(lastContent);
                    console.log(`📊 Final update: ${lastContent.length} chars`);
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
            // Replace the local user message immediately with a temporary ID
            const tempBranchId = 'branch_' + Date.now().toString();
            setMessages((prev: Message[]) => {
                const editIdx = prev.findIndex(m => m.id === messageId);
                if (editIdx < 0) return prev;
                const before = prev.slice(0, editIdx);
                const newUserMsg: Message = {
                    id: tempBranchId, role: 'user', content: newContent,
                    parentId: messageToEdit?.parentId || undefined,
                    timestamp: new Date(),
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
                        parent_id: messageToEdit?.parentId || undefined,
                    }),
                    signal: abortController.signal,
                });

                if (streamResponse.ok && streamResponse.body) {
                    const assistantMessageId = (Date.now() + 1).toString();
                    const assistantMessage: Message = { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date(), parentId: tempBranchId };

                    const updateMessage = (fullContent: string) => {
                        const newMsg = { ...assistantMessage, content: fullContent };
                        if (currentConvIdRef.current === streamConversationId) {
                            setMessages((prev: Message[]) => {
                                const targetId = assistantMessage.id;
                                const exists = prev.some(m => m.id === targetId);
                                return exists ? prev.map(m => m.id === targetId ? newMsg : m) : [...prev, newMsg];
                            });
                        }
                    };

                    if (currentConvIdRef.current === streamConversationId) setMessages((prev: Message[]) => [...prev, assistantMessage]);

                    let currentUserMsgId = tempBranchId;
                    let lastContent = '';
                    await processSSEStream(streamResponse, {
                        onMeta: (meta) => {
                            if (meta.user_message_id) {
                                setMessages((prev: Message[]) => prev.map(msg => msg.id === currentUserMsgId ? { ...msg, id: meta.user_message_id } : msg));
                                currentUserMsgId = meta.user_message_id;
                                assistantMessage.parentId = meta.user_message_id;
                                setMessages((prev: Message[]) => prev.map(msg => msg.id === assistantMessage.id ? { ...msg, parentId: meta.user_message_id } : msg));
                            }
                            if (meta.assistant_message_id) {
                                setMessages((prev: Message[]) => prev.map(msg => msg.id === assistantMessage.id ? { ...msg, id: meta.assistant_message_id } : msg));
                                assistantMessage.id = meta.assistant_message_id;
                            }
                        },
                        onContent: (fullContent) => {
                            lastContent = fullContent;
                            const now = Date.now();
                            if (now - lastUpdateRef.current >= 150) {
                                updateMessage(fullContent);
                                lastUpdateRef.current = now;
                            }
                        },
                        onDone: () => updateMessage(lastContent)
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
