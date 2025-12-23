'use client';

import useSWR from 'swr';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? 'https://toluwanimi465-pharmgpt-backend.hf.space'
    : 'http://localhost:8000';

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

// Hook for conversation list (sidebar)
export function useConversations() {
    const { data, error, mutate, isLoading } = useSWR(
        '/api/v1/chat/conversations',
        fetcher,
        {
            revalidateOnFocus: false,       // Don't reload on window focus
            dedupingInterval: 30000,        // Cache for 30 seconds
            revalidateOnReconnect: true,    // Reload when connection restored
            fallbackData: [],               // Start with empty array (no loading flash)
        }
    );

    return {
        conversations: data || [],
        isLoading,
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
