'use client';

import { useEffect, useState } from 'react';

// Shared store for active streams - allows sidebar to show spinners
export const activeStreams = new Map<string, {
    abortController: AbortController;
    isLoading: boolean;
}>();

// Subscribers for reactive updates
const subscribers = new Set<() => void>();

export function notifyStreamChange() {
    subscribers.forEach(fn => fn());
}

/**
 * Hook to subscribe to streaming state changes
 * Returns a Set of conversation IDs that are currently streaming
 */
export function useStreamingConversations(): Set<string> {
    const [streamingIds, setStreamingIds] = useState<Set<string>>(new Set());

    useEffect(() => {
        const update = () => {
            const ids = new Set<string>();
            activeStreams.forEach((stream, id) => {
                if (stream.isLoading) {
                    ids.add(id);
                }
            });
            setStreamingIds(ids);
        };

        // Initial update
        update();

        // Subscribe to changes
        subscribers.add(update);

        // Also poll every 500ms as backup (for when notifications are missed)
        const interval = setInterval(update, 500);

        return () => {
            subscribers.delete(update);
            clearInterval(interval);
        };
    }, []);

    return streamingIds;
}

/**
 * Register a stream - call when starting a stream
 */
export function registerStream(conversationId: string, abortController: AbortController) {
    activeStreams.set(conversationId, {
        abortController,
        isLoading: true,
    });
    notifyStreamChange();
}

/**
 * Unregister a stream - call when stream completes
 */
export function unregisterStream(conversationId: string) {
    activeStreams.delete(conversationId);
    notifyStreamChange();
}

/**
 * Check if a specific conversation is streaming
 */
export function isConversationStreaming(conversationId: string | null): boolean {
    if (!conversationId) return false;
    return activeStreams.get(conversationId)?.isLoading || false;
}

/**
 * Abort a specific conversation's stream
 */
export function abortStream(conversationId: string) {
    const stream = activeStreams.get(conversationId);
    if (stream) {
        stream.abortController.abort();
        activeStreams.delete(conversationId);
        notifyStreamChange();
    }
}
