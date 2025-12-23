'use client';

import useSWR, { mutate as globalMutate } from 'swr';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? 'https://toluwanimi465-pharmgpt-backend.hf.space'
    : 'http://localhost:8000';

/**
 * Get token from localStorage (stable, doesn't cause re-renders)
 */
function getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
}

/**
 * Simple fetcher - no complex abort logic
 */
async function fetcher<T>(url: string): Promise<T> {
    const token = getToken();
    if (!token) {
        throw new Error('Not authenticated');
    }

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

    return response.json();
}

/**
 * Clear all SWR cache - call on logout
 */
export function clearSWRCache() {
    globalMutate(() => true, undefined, { revalidate: false });
}

/**
 * Hook for conversation list - SIMPLIFIED
 * Uses a stable cache key that doesn't change on re-render
 */
export function useConversations() {
    // Get token once for the cache key - use stable reference
    const token = getToken();

    // Simple, stable cache key
    const cacheKey = token ? 'conversations' : null;

    const { data, error, mutate, isLoading } = useSWR<any[]>(
        cacheKey,
        () => fetcher<any[]>('/api/v1/chat/conversations'),
        {
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            dedupingInterval: 30000,
            errorRetryCount: 2,
        }
    );

    return {
        conversations: data || [],
        isLoading: isLoading,
        isError: error,
        mutate,
    };
}

/**
 * Hook for conversation messages
 */
export function useConversationMessages(conversationId: string | null) {
    const { data, error, mutate, isLoading } = useSWR(
        conversationId ? `messages-${conversationId}` : null,
        () => fetcher(`/api/v1/chat/conversations/${conversationId}/messages`),
        {
            revalidateOnFocus: false,
            dedupingInterval: 30000,
        }
    );

    return {
        messages: data || [],
        isLoading,
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
