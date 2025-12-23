'use client';

import useSWR, { mutate as globalMutate } from 'swr';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? 'https://toluwanimi465-pharmgpt-backend.hf.space'
    : 'http://localhost:8000';

// Get a short hash of the token for cache key isolation
function getTokenHash(): string {
    if (typeof window === 'undefined') return '';
    const token = localStorage.getItem('token');
    if (!token) return '';
    return token.substring(0, 8);
}

// Fetcher with timeout and retry
const fetcher = async (url: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) throw new Error('No token');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Fetch failed: ${response.status}`);
        }
        return response.json();
    } catch (error: any) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - backend may be starting up');
        }
        throw error;
    }
};

// Clear all SWR cache (call on logout)
export function clearSWRCache() {
    globalMutate(() => true, undefined, { revalidate: false });
}

// Hook for conversation list (sidebar)
export function useConversations(authToken?: string | null) {
    // Prefer passed token (reactive), fallback to localStorage
    const token = authToken !== undefined ? authToken : (typeof window !== 'undefined' ? localStorage.getItem('token') : null);

    // Generate hash from the effective token
    const tokenHash = token ? token.substring(0, 8) : '';

    const { data, error, mutate, isLoading } = useSWR(
        tokenHash ? `/api/v1/chat/conversations?user=${tokenHash}` : null,
        () => fetcher('/api/v1/chat/conversations'),
        {
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            revalidateIfStale: false,  // Don't auto-refetch stale data
            dedupingInterval: 60000,   // 60 second deduplication window
            errorRetryCount: 2,
            errorRetryInterval: 3000,
            refreshInterval: 0,        // No automatic refresh
        }
    );

    return {
        conversations: data || [],
        isLoading: isLoading || !tokenHash,
        isError: error,
        mutate,
    };
}

// Hook for conversation messages
export function useConversationMessages(conversationId: string | null) {
    const { data, error, mutate, isLoading } = useSWR(
        conversationId ? `/api/v1/chat/conversations/${conversationId}/messages` : null,
        fetcher,
        {
            revalidateOnFocus: false,
            dedupingInterval: 60000,        // Cache messages for 60 seconds
            revalidateOnReconnect: true,
        }
    );

    return {
        messages: data || [],
        isLoading,
        isError: error,
        mutate,
    };
}

// Optimistic update helper - add a message to cache immediately
export function optimisticAddMessage(
    mutate: (data?: any, shouldRevalidate?: boolean) => Promise<any>,
    message: any
) {
    mutate((current: any[]) => [...(current || []), message], false);
}

// Optimistic update helper - update last message (for streaming)
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
