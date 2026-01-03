'use client';

import { useState, useEffect } from 'react';
import useSWR, { mutate as globalMutate } from 'swr';

import { API_BASE_URL } from '@/config/api';

/**
 * Get token from localStorage
 */
function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
}

/**
 * Simple fetcher with auth
 */
async function fetcher<T>(url: string): Promise<T> {
    const token = getToken();
    if (!token) {
        throw new Error('Not authenticated');
    }

    console.log(`🚀 fetching: ${url}`);
    // Use full backend URL to avoid Vercel 301 redirects changing POST to GET
    const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: { 'Authorization': `Bearer ${token}` },
    });

    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('token');
            throw new Error('Session expired');
        }
        throw new Error(`Request failed: ${response.status}`);
    }

    const data = await response.json();
    console.log(`✅ Fetcher Success (${url}):`, Array.isArray(data) ? `Array(${data.length})` : typeof data);
    return data;
}

/**
 * Clear all SWR cache - call on logout
 */
export function clearSWRCache() {
    globalMutate(() => true, undefined, { revalidate: false });
}

/**
 * Move a conversation to top of list (optimistic update)
 * Call this when a message is sent to immediately reflect the change
 */
export function moveConversationToTop(conversationId: string) {
    globalMutate(
        'conversations',
        (current: any[] | undefined) => {
            if (!current) return current;
            const conv = current.find(c => c.id === conversationId);
            if (!conv) return current;
            // Move to top by updating updated_at
            const updated = { ...conv, updated_at: new Date().toISOString() };
            return [updated, ...current.filter(c => c.id !== conversationId)];
        },
        { revalidate: false }
    );
}

/**
 * Add a new conversation to the list (optimistic update)
 * Call this when a new conversation is created
 */
export function addConversationToList(conversation: { id: string; title: string; created_at?: string; updated_at?: string }) {
    globalMutate(
        'conversations',
        (current: any[] | undefined) => {
            const now = new Date().toISOString();
            const newConv = {
                ...conversation,
                created_at: conversation.created_at || now,
                updated_at: conversation.updated_at || now,
            };
            return [newConv, ...(current || [])];
        },
        { revalidate: false }
    );
}

/**
 * Hook for conversation list
 * Uses stable cache key - only fetches after client-side hydration
 */
export function useConversations() {
    // Track if we're on the client and have a token
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        // Only set ready after hydration, when we can reliably check localStorage
        const hasToken = !!getToken();
        console.log('useConversations useEffect - hasToken:', hasToken);
        setIsReady(hasToken);
    }, []);

    // Use stable cache key - only enabled when ready
    const { data, error, mutate, isLoading } = useSWR<any[]>(
        isReady ? 'conversations' : null,  // null key = don't fetch
        () => fetcher<any[]>('/api/v1/chat/conversations'),
        {
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            dedupingInterval: 10000,
            onSuccess: (data) => console.log('✅ SWR onSuccess - conversations:', data?.length),
            onError: (err) => console.error('❌ SWR onError:', err)
        }
    );

    console.log('useConversations return:', { isReady, dataLength: data?.length, isLoading, error: error?.message });

    return {
        conversations: data || [],
        isLoading: !isReady || isLoading,  // Loading if not ready OR SWR is loading
        isError: error,
        mutate,
    };
}

/**
 * Hook for conversation messages
 */
export function useConversationMessages(conversationId: string | null) {
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        setIsReady(!!getToken());
    }, []);

    const { data, error, mutate, isLoading } = useSWR(
        isReady && conversationId ? `messages-${conversationId}` : null,
        () => fetcher(`/api/v1/chat/conversations/${conversationId}/messages`),
        {
            revalidateOnFocus: false,
            dedupingInterval: 30000,
        }
    );

    return {
        messages: data || [],
        isLoading: !isReady || isLoading,
        isError: error,
        mutate,
    };
}

/**
 * Optimistic update - add message to cache
 */
export function optimisticAddMessage(
    mutate: (data?: any, shouldRevalidate?: boolean) => Promise<any>,
    message: any
) {
    mutate((current: any[]) => [...(current || []), message], false);
}

/**
 * Optimistic update - update last message content
 */
export function optimisticUpdateLastMessage(
    mutate: (data?: any, shouldRevalidate?: boolean) => Promise<any>,
    content: string
) {
    mutate((current: any[]) => {
        if (!current?.length) return current;
        const updated = [...current];
        updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content,
        };
        return updated;
    }, false);
}
