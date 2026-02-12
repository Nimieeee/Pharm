'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * A hook to batch streaming updates to prevent UI thrashing.
 * Instead of updating state on every single token (which can be 50+ times/sec),
 * this updates at most once every `updateIntervalMs` (default 30ms/30fps).
 */
export function useBatchedStream(
    isLoading: boolean,
    updateIntervalMs: number = 30
) {
    const [streamedContent, setStreamedContent] = useState('');
    const bufferRef = useRef('');
    const lastUpdateRef = useRef(0);
    const rafRef = useRef<number | null>(null);

    // Function to add new content to the buffer
    const updateStream = useCallback((newContent: string) => {
        bufferRef.current = newContent;

        // If we haven't updated in a while, do strictly minimal updates
        const now = Date.now();
        if (now - lastUpdateRef.current >= updateIntervalMs) {
            setStreamedContent(bufferRef.current);
            lastUpdateRef.current = now;
        } else {
            // Otherwise schedule a FLUSH on the next animation frame
            if (!rafRef.current) {
                rafRef.current = requestAnimationFrame(() => {
                    setStreamedContent(bufferRef.current);
                    lastUpdateRef.current = Date.now();
                    rafRef.current = null;
                });
            }
        }
    }, [updateIntervalMs]);

    // Reset when loading starts/stops
    useEffect(() => {
        if (!isLoading) {
            // Flush any remaining buffer when stream ends
            if (bufferRef.current && bufferRef.current !== streamedContent) {
                setStreamedContent(bufferRef.current);
            }
            // Cleanup
            if (rafRef.current) {
                cancelAnimationFrame(rafRef.current);
                rafRef.current = null;
            }
        } else {
            // New stream starting
            setStreamedContent('');
            bufferRef.current = '';
        }
    }, [isLoading]);

    return {
        streamedContent,
        updateStream,
        setStreamedContent, // Allow manual override if needed
    };
}
