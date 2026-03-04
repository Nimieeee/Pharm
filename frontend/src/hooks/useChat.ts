'use client';

import { useCallback, useEffect } from 'react';
import { API_BASE_URL, UPLOAD_BASE_URL } from '@/config/api';
import { useChatState, clearMessageCache } from './useChatState';
import { useChatStreaming } from './useChatStreaming';
import { isConversationStreaming, activeStreams } from './useStreamingState';
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
    branchData, setBranchData,
    activeBranches, setActiveBranches,
    currentConvIdRef, uploadAbortRef,
    clearMessages
  } = state;

  const { sendMessage, stopGeneration, regenerateResponse } = streaming;

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
    const update = () => {
      // Use the ref to check the current conversation's actual streaming state
      if (currentConvIdRef.current) {
        setIsLoading(isConversationStreaming(currentConvIdRef.current));
      } else {
        setIsLoading(false);
      }
    };
    update();
    const subscribers = (globalThis as any).__streamSubscribers;
    if (subscribers) {
      subscribers.add(update);
      return () => { subscribers.delete(update); };
    }
  }, [setIsLoading, currentConvIdRef]);

  const loadConversation = useCallback(async (convId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    currentConvIdRef.current = convId;
    setConversationId(convId);

    // Check if this conversation has an active stream with preserved state
    const streamState = activeStreams.get(convId);
    if (streamState && isConversationStreaming(convId)) {
      // Restore deep research progress from global store
      if (streamState.deepResearchProgress) {
        setDeepResearchProgress(streamState.deepResearchProgress);
      } else {
        setDeepResearchProgress(null);
      }
      setIsLoading(true);
    } else {
      // No active stream — reset progress
      setDeepResearchProgress(null);
      setIsLoading(false);
    }

    // Check for pending messages (e.g., deep research completed while user was away)
    if (streamState?.pendingMessages && streamState.pendingMessages.length > 0) {
      const pending = [...streamState.pendingMessages];
      streamState.pendingMessages = []; // Clear after consuming
      // Will be merged after loading messages from API below
      setTimeout(() => {
        setMessages((prev: Message[]) => {
          const existingIds = new Set(prev.map(m => m.id));
          const newMsgs = pending.filter(m => !existingIds.has(m.id));
          return newMsgs.length > 0 ? [...prev, ...newMsgs] : prev;
        });
      }, 500); // Small delay to let API messages load first
    }

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
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/conversations/${convId}/branched-messages`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();

        // 1. Process base messages (only user messages belong in the layout loop now)
        const loadedMessages: Message[] = (data.messages || [])
          .filter((msg: any) => msg.role === 'user')
          .map((msg: any) => ({
            id: msg.id, role: msg.role, content: msg.content,
            parentId: msg.parent_id || undefined, translations: msg.translations || undefined,
            timestamp: new Date(msg.created_at), attachments: msg.metadata?.attachments || undefined,
            mode: msg.metadata?.mode || undefined,
          }));
        setMessages(loadedMessages);

        // 2. Process branchData mapping
        const newBranchData = new Map<string, any[]>();
        if (data.responses) {
          data.responses.forEach((resp: any) => {
            const arr = newBranchData.get(resp.user_message_id) || [];
            arr.push(resp);
            newBranchData.set(resp.user_message_id, arr);
          });
        }
        setBranchData(newBranchData);

        // 3. Process activeBranches mapping
        const newActiveBranches = new Map<string, string>();
        if (data.selections) {
          data.selections.forEach((sel: any) => {
            if (sel.active_response_id) {
              newActiveBranches.set(sel.user_message_id, sel.active_response_id);
            }
          });
        }
        setActiveBranches(newActiveBranches);
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
  }, [currentConvIdRef, setConversationId, setDeepResearchProgress, setIsLoading, setMessages, setIsLoadingConversation, setBranchData, setActiveBranches]);

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

  const regenerateMessage = useCallback(async (userMessageId: string) => {
    // With independent branching, `messages` array only contains user messages.
    // So the UI will pass the userMessageId directly.
    await regenerateResponse(userMessageId);
  }, [regenerateResponse]);

  const switchBranch = useCallback(async (userMessageId: string, responseId: string) => {
    setActiveBranches((prev) => {
      const newMap = new Map(prev);
      newMap.set(userMessageId, responseId);
      return newMap;
    });

    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const formData = new FormData();
      formData.append('response_id', responseId);
      formData.append('conversation_id', conversationId || '');

      await fetch(`${API_BASE_URL}/api/v1/chat/messages/${userMessageId}/branch`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
    } catch (e) {
      console.error("Failed to switch branch", e);
    }
  }, [setActiveBranches, conversationId]);

  const deleteBranch = useCallback(async (responseId: string) => {
    let ownerMsgId: string | null = null;
    let newBranches: any[] = [];

    for (const [uid, branches] of Array.from(branchData.entries())) {
      if (branches.some((b: any) => b.id === responseId)) {
        ownerMsgId = uid;
        newBranches = branches.filter((b: any) => b.id !== responseId);
        break;
      }
    }

    if (!ownerMsgId) return;

    const fallbackId = newBranches.length > 0 ? newBranches[newBranches.length - 1].id : undefined;

    setBranchData((prev) => {
      const newMap = new Map(prev);
      newMap.set(ownerMsgId as string, newBranches);
      return newMap;
    });

    if (activeBranches.get(ownerMsgId) === responseId) {
      setActiveBranches((prev) => {
        const newMap = new Map(prev);
        if (fallbackId) newMap.set(ownerMsgId as string, fallbackId);
        else newMap.delete(ownerMsgId as string);
        return newMap;
      });
    }

    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      await fetch(`${API_BASE_URL}/api/v1/chat/responses/${responseId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Failed to delete branch", e);
    }
  }, [branchData, activeBranches, setBranchData, setActiveBranches]);

  const deleteMessage = useCallback((messageId: string) => {
    setMessages((prev: Message[]) => prev.filter((msg: Message) => msg.id !== messageId));
  }, [setMessages]);

  return {
    messages, isLoading, isLoadingConversation, isUploading, conversationId, deepResearchProgress,
    isDeleting, uploadedFiles, branchData, activeBranches,
    sendMessage, stopGeneration, clearMessages, loadConversation, selectConversation,
    deleteConversation, uploadFiles, cancelUpload, removeFile,
    regenerateMessage, regenerateResponse, deleteMessage, switchBranch, deleteBranch,
    isConversationLoading: (id: string) => isConversationStreaming(id) || (id === conversationId && isLoading),
  };
}
