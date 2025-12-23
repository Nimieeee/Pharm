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
    // Use first 8 chars of token as user identifier (unique per user)
    return token.substring(0, 8);
}

// Generic fetcher with auth
const fetcher = async (url: string) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) throw new Error('No token');

    const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
        },
    });

    if (!response.ok) throw new Error('Fetch failed');
    return response.json();
};

// Clear all SWR cache (call on logout)
export function clearSWRCache() {
    globalMutate(() => true, undefined, { revalidate: false });
}

// Hook for conversation list (sidebar)
export function useConversations() {
    const tokenHash = getTokenHash();

    const { data, error, mutate, isLoading } = useSWR(
        // Include tokenHash in key for user isolation
        tokenHash ? `/api/v1/chat/conversations?user=${tokenHash}` : null,
        // Actual fetch URL (without the user param - it's just for cache key)
        () => fetcher('/api/v1/chat/conversations'),
        {
            revalidateOnFocus: false,       // Don't reload on window focus
            dedupingInterval: 30000,        // Cache for 30 seconds
            revalidateOnReconnect: true,    // Reload when connection restored
            // No fallbackData - prevents showing stale data from other users
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
