'use client';

import { useState, useCallback, useEffect } from 'react';
import { Message } from '@/components/chat/ChatMessage';

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
  ? 'https://pharmgpt-backend.onrender.com'
  : 'http://localhost:8000';

type Mode = 'fast' | 'detailed' | 'research';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && !conversationId) {
      createConversation(token);
    }
  }, [conversationId]);

  const createConversation = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ title: 'New Chat' }),
      });

      if (response.ok) {
        const data = await response.json();
        setConversationId(data.id);
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const sendMessage = useCallback(async (content: string, mode: Mode = 'detailed') => {
    if (!content.trim() || isLoading) return;

    const token = localStorage.getItem('token');
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (!token) {
        const authMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Please sign in to use PharmGPT. Go to /login to authenticate.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, authMessage]);
        setIsLoading(false);
        return;
      }

      let currentConversationId = conversationId;
      if (!currentConversationId) {
        const convResponse = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ title: content.slice(0, 50) }),
        });

        if (convResponse.ok) {
          const convData = await convResponse.json();
          currentConversationId = convData.id;
          setConversationId(convData.id);
        } else {
          throw new Error('Failed to create conversation');
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: content.trim(),
          conversation_id: currentConversationId,
          mode: mode,
          use_rag: true,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          localStorage.removeItem('token');
          throw new Error('Session expired. Please sign in again.');
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get response');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || data.message || 'I apologize, but I encountered an issue processing your request.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: error.message || 'I apologize, but I\'m having trouble connecting to the server. Please check your connection and try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    conversationId,
  };
}
