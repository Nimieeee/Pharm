import { renderHook, act } from '@testing-library/react';
import { useChatState, cacheGet, clearMessageCache } from '../hooks/useChatState';
import { describe, it, expect, beforeEach } from 'vitest';

describe('useChatState', () => {
    beforeEach(() => {
        clearMessageCache();
    });

    it('initializes with default values', () => {
        const { result } = renderHook(() => useChatState());
        expect(result.current.messages).toEqual([]);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.conversationId).toBeNull();
    });

    it('updates messages correctly', () => {
        const { result } = renderHook(() => useChatState());

        act(() => {
            result.current.setMessages([
                { id: '1', role: 'user', content: 'test', timestamp: new Date() }
            ]);
        });

        expect(result.current.messages.length).toBe(1);
        expect(result.current.messages[0].content).toBe('test');
    });

    it('caches messages against conversationId', () => {
        const { result, rerender } = renderHook(() => useChatState());

        act(() => {
            result.current.setConversationId('conv-123');
        });

        act(() => {
            result.current.setMessages([
                { id: '1', role: 'user', content: 'cached-message', timestamp: new Date() }
            ]);
        });

        // Force a re-render to trigger useEffect which caches the messages
        rerender();

        const cached = cacheGet('conv-123');
        expect(cached).toBeDefined();
        expect(cached![0].content).toBe('cached-message');
    });

    it('clears messages and cache gracefully', () => {
        const { result } = renderHook(() => useChatState());

        act(() => {
            result.current.setConversationId('conv-123');
            result.current.setMessages([
                { id: '1', role: 'user', content: 'test', timestamp: new Date() }
            ]);
        });

        act(() => {
            result.current.clearMessages();
        });

        expect(result.current.messages).toEqual([]);
        expect(result.current.conversationId).toBeNull();
    });
});
