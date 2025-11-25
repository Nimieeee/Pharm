'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, CheckCircle2, Loader2 } from 'lucide-react';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import { useChat } from '@/hooks/useChat';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, sendMessage } = useChat();
  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    if (initialQuery && !hasInitialized) {
      sendMessage(initialQuery);
      setHasInitialized(true);
    }
  }, [initialQuery, hasInitialized, sendMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Header */}
      <header className="h-16 px-6 flex items-center justify-between border-b border-[var(--border)] glass-strong">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={16} strokeWidth={1.5} className="text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-[var(--text-primary)]">PharmGPT</h1>
            <p className="text-xs text-[var(--text-secondary)]">AI Research Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isLoading ? (
            <Loader2 size={14} strokeWidth={1.5} className="text-amber-500 animate-spin" />
          ) : (
            <CheckCircle2 size={14} strokeWidth={1.5} className="text-emerald-500" />
          )}
          <span className="text-xs text-[var(--text-secondary)]">
            {isLoading ? 'Thinking...' : 'Ready'}
          </span>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 pb-32 md:pb-8">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState onSuggestionClick={sendMessage} />
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
                >
                  <ChatMessage message={msg} />
                </motion.div>
              ))}
            </AnimatePresence>
          )}
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-3 py-4"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Sparkles size={16} strokeWidth={1.5} className="text-white" />
              </div>
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-[var(--text-secondary)] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--text-secondary)] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--text-secondary)] animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}

function EmptyState({ onSuggestionClick }: { onSuggestionClick: (msg: string) => void }) {
  const suggestions = [
    'What are the common drug interactions with Warfarin?',
    'Explain the mechanism of action of SSRIs',
    'Summarize recent clinical trials for mRNA vaccines',
    'What are the pharmacokinetics of Metformin?',
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="text-center py-16"
    >
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
        <Sparkles size={28} strokeWidth={1.5} className="text-white" />
      </div>
      <h2 className="text-section-header text-[var(--text-primary)] mb-3">
        How can I help you today?
      </h2>
      <p className="text-body mb-8 max-w-md mx-auto">
        Ask me about drug interactions, clinical research, molecular structures, or upload documents for analysis.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto">
        {suggestions.map((suggestion, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i, duration: 0.4 }}
            onClick={() => onSuggestionClick(suggestion)}
            className="p-4 rounded-2xl bg-[var(--surface)] border border-[var(--border)] text-left text-sm text-[var(--text-primary)] hover:border-indigo-500/50 hover:shadow-lg transition-all btn-press"
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center">
        <Loader2 size={32} strokeWidth={1.5} className="text-indigo-500 animate-spin" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
