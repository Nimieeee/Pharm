'use client';

import { motion } from 'framer-motion';
import { User, Sparkles } from 'lucide-react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 py-6 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center ${
        isUser 
          ? 'bg-[var(--surface-highlight)]' 
          : 'bg-gradient-to-br from-indigo-500 to-purple-600'
      }`}>
        {isUser ? (
          <User size={16} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
        ) : (
          <Sparkles size={16} strokeWidth={1.5} className="text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block p-4 rounded-2xl ${
          isUser 
            ? 'bg-[var(--text-primary)] text-[var(--background)] rounded-tr-md' 
            : 'bg-[var(--surface)] border border-[var(--border)] rounded-tl-md'
        }`}>
          <p className={`text-sm leading-relaxed whitespace-pre-wrap ${
            isUser ? '' : 'text-[var(--text-primary)]'
          }`}>
            {message.content}
          </p>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-2 px-1">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}
