/**
 * Regression Test: Message Edit Re-render
 * 
 * Following CLAUDE.md: Test-Driven Development
 * Write test FIRST, then implement fix
 * 
 * Issue: After editing a message, UI doesn't update until page refresh
 * Expected: Edited message content should display immediately
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock dependencies
vi.mock('@/config/api', () => ({
  API_BASE_URL: 'http://test-api.com',
  UPLOAD_BASE_URL: 'http://test-upload.com',
}));

vi.mock('@/lib/auth-context', () => ({
  useAuth: () => ({
    user: { id: 'test-user', email: 'test@test.com', is_admin: false },
    token: 'test-token',
    logout: vi.fn(),
  }),
}));

vi.mock('@/hooks/useSWRChat', () => ({
  useConversations: () => ({
    conversations: [],
    isLoading: false,
    isError: false,
    mutate: vi.fn(),
  }),
}));

describe('Message Edit Re-render', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should re-render message immediately after edit', async () => {
    // Arrange: Create a hook with initial messages
    const { result } = renderHook(() => {
      // Import here to avoid hoisting issues
      const { useChat } = require('@/hooks/useChat');
      return useChat();
    });

    const initialMessage = {
      id: 'test-message-id',
      role: 'user' as const,
      content: 'Original content',
      timestamp: new Date('2026-03-09T10:00:00Z'),
    };

    // Set initial messages
    act(() => {
      result.current.setMessages([initialMessage]);
    });

    // Assert: Initial state
    expect(result.current.messages[0].content).toBe('Original content');

    // Act: Edit the message
    await act(async () => {
      await result.current.editMessage('test-message-id', 'Edited content');
    });

    // Assert: Message content updated immediately (without refresh)
    expect(result.current.messages[0].content).toBe('Edited content');
  });

  it('should update message timestamp when edited', async () => {
    const { result } = renderHook(() => {
      const { useChat } = require('@/hooks/useChat');
      return useChat();
    });

    const beforeEdit = Date.now();

    const initialMessage = {
      id: 'test-message-id',
      role: 'user' as const,
      content: 'Original content',
      timestamp: new Date('2026-03-09T10:00:00Z'),
    };

    act(() => {
      result.current.setMessages([initialMessage]);
    });

    await act(async () => {
      await result.current.editMessage('test-message-id', 'Edited content');
    });

    const afterEdit = Date.now();
    const updatedMessage = result.current.messages[0];

    // Timestamp should be updated to reflect edit time
    expect(updatedMessage.timestamp.getTime()).toBeGreaterThanOrEqual(beforeEdit);
    expect(updatedMessage.timestamp.getTime()).toBeLessThanOrEqual(afterEdit);
  });

  it('should not affect other messages when editing one', async () => {
    const { result } = renderHook(() => {
      const { useChat } = require('@/hooks/useChat');
      return useChat();
    });

    const messages = [
      { id: 'msg1', role: 'user' as const, content: 'Message 1', timestamp: new Date() },
      { id: 'msg2', role: 'user' as const, content: 'Message 2', timestamp: new Date() },
      { id: 'msg3', role: 'user' as const, content: 'Message 3', timestamp: new Date() },
    ];

    act(() => {
      result.current.setMessages(messages);
    });

    await act(async () => {
      await result.current.editMessage('msg2', 'Edited Message 2');
    });

    // Only msg2 should be edited
    expect(result.current.messages[0].content).toBe('Message 1');
    expect(result.current.messages[1].content).toBe('Edited Message 2');
    expect(result.current.messages[2].content).toBe('Message 3');
  });
});
