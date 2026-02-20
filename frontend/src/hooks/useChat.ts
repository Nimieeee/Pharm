'use client';

import { useCallback, useEffect } from 'react';
import { API_BASE_URL, UPLOAD_BASE_URL } from '@/config/api';
import { useChatState, clearMessageCache } from './useChatState';
import { useChatStreaming } from './useChatStreaming';
import { isConversationStreaming } from './useStreamingState';
import { Message } from '@/components/chat/ChatMessage';

export { clearMessageCache };

export function useChat() {
  const state = useChatState();
  const streaming = useChatStreaming(state);

  const {
    messages, setMessages,
    isLoading, setIsLoading,
    isLoadingConversation, setIsLoadingConversation,
    isUploading, setIsUploading,
    conversationId, setConversationId,
    deepResearchProgress, setDeepResearchProgress,
    isDeleting, setIsDeleting,
    uploadedFiles, setUploadedFiles,
    branchMap,
    currentConvIdRef, uploadAbortRef,
    clearMessages
  } = state;

  const { sendMessage, stopGeneration, editMessage, fetchBranchInfo } = streaming;

  // Keep-alive ping
  useEffect(() => {
    let failCount = 0;
    const pingBackend = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/`, { method: 'HEAD' });
        if (!res.ok) { failCount++; if (failCount >= 3) console.warn(`[Health] Backend ping failed ${failCount} times`); }
        else { failCount = 0; }
      } catch {
        failCount++; if (failCount >= 3) console.warn(`[Health] Backend unreachable (${failCount} failures)`);
      }
    };
    pingBackend();
    const interval = setInterval(pingBackend, 30 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Sync isLoading
  useEffect(() => {
    const update = () => { if (conversationId) { setIsLoading(isConversationStreaming(conversationId)); } else { setIsLoading(false); } };
    update();
    const subscribers = (globalThis as any).__streamSubscribers;
    if (subscribers) { subscribers.add(update); return () => { subscribers.delete(update); }; }
  }, [conversationId, setIsLoading]);

  const loadConversation = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    currentConvIdRef.current = convId;
    setConversationId(convId);
    setDeepResearchProgress(null);

    if (isConversationStreaming(convId)) setIsLoading(true);

    import('./useChatState').then(({ cacheGet }) => {
      const cachedMessages = cacheGet(convId);
      if (cachedMessages && cachedMessages.length > 0) {
        setMessages(cachedMessages);
      } else {
        setMessages([]);
        setIsLoadingConversation(true);
      }
    });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${convId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        const loadedMessages: Message[] = data.map((msg: any) => ({
          id: msg.id, role: msg.role, content: msg.content,
          parentId: msg.parent_id || undefined, translations: msg.translations || undefined,
          timestamp: new Date(msg.created_at), attachments: msg.metadata?.attachments || undefined,
          mode: msg.metadata?.mode || undefined,
        }));
        setMessages(loadedMessages);
        fetchBranchInfo(convId);
      } else if (response.status === 401) {
        localStorage.removeItem('token');
      } else if (response.status === 404) {
        setConversationId(null); currentConvIdRef.current = null;
        if (typeof window !== 'undefined') localStorage.removeItem('currentConversationId');
        setMessages([]);
      }
    } catch (error) {
      console.error('Load conversation error:', error);
    } finally {
      setIsLoadingConversation(false);
    }
  }, [currentConvIdRef, setConversationId, setDeepResearchProgress, setIsLoading, setMessages, setIsLoadingConversation, fetchBranchInfo]);

  const selectConversation = useCallback((convId: string) => { loadConversation(convId); }, [loadConversation]);

  const deleteConversation = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token || !conversationId) return false;
    setIsDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${conversationId}`, {
        method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) { setMessages([]); setConversationId(null); return true; }
      return false;
    } catch (error) { return false; } finally { setIsDeleting(false); }
  }, [conversationId, setMessages, setConversationId, setIsDeleting]);

  const cancelledUploadsRef = { current: new Set<string>() };

  const removeFile = useCallback((fileName: string) => {
    cancelledUploadsRef.current.add(fileName);
    setUploadedFiles((prev: any) => prev.filter((f: any) => f.name !== fileName));
  }, [setUploadedFiles]);

  const uploadFiles = useCallback(async (files: FileList) => {
    const token = localStorage.getItem('token');
    if (!token) return [{ fileName: 'General', status: 'error', error: 'Please sign in to upload files.' }];

    let streamConversationId = conversationId;
    if (!streamConversationId) {
      try {
        const convResponse = await fetch(`${API_BASE_URL}/api/v1/chat/conversations`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ title: 'Document Analysis' }),
        });
        if (convResponse.ok) { streamConversationId = (await convResponse.json()).id; setConversationId(streamConversationId); }
      } catch (e) { return [{ fileName: 'General', status: 'error', error: 'Failed to create conversation' }]; }
    }

    setIsUploading(true);
    const results: any[] = [];
    if (!uploadAbortRef.current) uploadAbortRef.current = new AbortController();
    const signal = uploadAbortRef.current.signal;

    try {
      await Promise.all(Array.from(files).map(async (file) => {
        if (cancelledUploadsRef.current.has(file.name)) return;
        try {
          const formData = new FormData(); formData.append('file', file);
          const response = await fetch(`${UPLOAD_BASE_URL}/api/v1/chat/conversations/${streamConversationId}/documents`, {
            method: 'POST', headers: { 'Authorization': `Bearer ${token}` }, body: formData, signal,
          });
          if (cancelledUploadsRef.current.has(file.name)) return;
          if (response.ok) {
            setUploadedFiles((prev: any) => { if (prev.some((f: any) => f.name === file.name)) return prev; return [...prev, { name: file.name, size: `${(file.size / 1024).toFixed(1)} KB`, type: file.type }]; });
            results.push({ fileName: file.name, status: 'success' });
          } else results.push({ fileName: file.name, status: 'error', error: 'Upload failed' });
        } catch (e: any) {
          if (e.name !== 'AbortError' && !cancelledUploadsRef.current.has(file.name)) results.push({ fileName: file.name, status: 'error', error: e.message });
        }
      }));
    } finally { setIsUploading(false); }
    return results;
  }, [conversationId, setConversationId, setIsUploading, uploadAbortRef, setUploadedFiles]);

  const cancelUpload = useCallback(() => {
    if (uploadAbortRef.current) { uploadAbortRef.current.abort(); uploadAbortRef.current = null; }
    setIsUploading(false); cancelledUploadsRef.current.clear();
  }, [uploadAbortRef, setIsUploading]);

  const regenerateMessage = useCallback(async (assistantMessageId: string) => {
    const msgIndex = messages.findIndex((m: Message) => m.id === assistantMessageId);
    if (msgIndex <= 0) return;
    const precedingUserMsg = messages[msgIndex - 1];
    if (precedingUserMsg.role !== 'user') return;
    await editMessage(precedingUserMsg.id, precedingUserMsg.content);
  }, [messages, editMessage]);

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
      const res = await fetch(
        `${API_BASE_URL}/api/v1/ai/chat/conversations/${conversationId}/messages/${siblingId}/thread`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (res.ok) {
        const threadData = await res.json();
        // Backend returns { messages: [...] }, not a raw array
        const rawMessages = Array.isArray(threadData) ? threadData : (threadData.messages || []);
        const threadMessages: Message[] = rawMessages.map((msg: any) => ({
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
  }, [branchMap, conversationId, setMessages]);

  const deleteMessage = useCallback((messageId: string) => {
    setMessages((prev: Message[]) => prev.filter((msg: Message) => msg.id !== messageId));
  }, [setMessages]);

  return {
    messages, isLoading, isLoadingConversation, isUploading, conversationId, deepResearchProgress,
    isDeleting, uploadedFiles, branchMap,
    sendMessage, stopGeneration, editMessage, clearMessages, loadConversation, selectConversation,
    deleteConversation, uploadFiles, cancelUpload, removeFile,
    regenerateMessage, deleteMessage, navigateBranch,
    isConversationLoading: (id: string) => isConversationStreaming(id) || (id === conversationId && isLoading),
  };
}
