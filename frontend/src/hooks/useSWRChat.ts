'use client';

import useSWR, { mutate as globalMutate } from 'swr';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? 'https://toluwanimi465-pharmgpt-backend.hf.space'
    : 'http://localhost:8000';

/**
 * Simple fetcher with auth and timeout
 */
async function fetcher<T>(url: string): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000); // 20s timeout

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            headers: { 'Authorization': `Bearer ${token}` },
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('token');
                throw new Error('Session expired');
            }
            throw new Error(`Request failed: ${response.status}`);
        }

        return response.json();
    } catch (error: any) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout');
        }
        throw error;
    }
}

/**
 * Clear all SWR cache - call on logout
 */
export function clearSWRCache() {
    globalMutate(() => true, undefined, { revalidate: false });
}

/**
 * Hook for conversation list
 */
export function useConversations(authToken?: string | null) {
    // Use token to create unique cache key per user
    const token = authToken !== undefined ? authToken : (typeof window !== 'undefined' ? localStorage.getItem('token') : null);
    const cacheKey = token ? `conversations-${token.substring(0, 8)}` : null;

    const { data, error, mutate, isLoading } = useSWR(
        cacheKey,
        () => fetcher('/api/v1/chat/conversations'),
        {
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            revalidateIfStale: false,
            dedupingInterval: 60000,
            errorRetryCount: 2,
            errorRetryInterval: 3000,
        }
    );

    return {
        conversations: data || [],
        isLoading: !cacheKey || isLoading,
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
            revalidateOnReconnect: false,
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
