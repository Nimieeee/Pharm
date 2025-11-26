'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, CheckCircle2, Loader2, PanelLeft, Plus, X } from 'lucide-react';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput from '@/components/chat/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useTheme } from '@/lib/theme-context';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, sendMessage, clearMessages } = useChat();
  const { theme, toggleTheme } = useTheme();
  const [hasInitialized, setHasInitialized] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  useEffect(() => {
    if (initialQuery && !hasInitialized) {
      sendMessage(initialQuery, 'detailed');
      setHasInitialized(true);
    }
  }, [initialQuery, hasInitialized, sendMessage]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (message: string, mode: 'fast' | 'detailed' | 'research') => {
    sendMessage(message, mode);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {/* Mobile Header */}
      <header className="md:hidden sticky top-0 z-40 h-14 px-4 flex items-center justify-between bg-[rgba(var(--surface-rgb),0.8)] backdrop-blur-md border-b border-[var(--border)]">
        <button
          onClick={() => setShowMobileSidebar(true)}
          className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors btn-press"
        >
          <PanelLeft size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
        </button>
        
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={14} strokeWidth={1.5} className="text-white" />
          </div>
          <span className="font-semibold text-sm text-[var(--text-primary)]">PharmGPT</span>
        </div>

        <button
          onClick={clearMessages}
          className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors btn-press"
        >
          <Plus size={20} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
        </button>
      </header>

      {/* Mobile Sidebar Sheet */}
      <AnimatePresence>
        {showMobileSidebar && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowMobileSidebar(false)}
              className="md:hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            />
            
            {/* Sheet */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="md:hidden fixed left-0 top-0 bottom-0 z-50 w-[280px] bg-[var(--surface)] border-r border-[var(--border)] p-4 flex flex-col"
            >
              {/* Sheet Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                    <Sparkles size={16} strokeWidth={1.5} className="text-white" />
                  </div>
                  <span className="font-semibold text-[var(--text-primary)]">PharmGPT</span>
                </div>
                <button
                  onClick={() => setShowMobileSidebar(false)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors"
                >
                  <X size={18} strokeWidth={1.5} className="text-[var(--text-secondary)]" />
                </button>
              </div>

              {/* New Chat */}
              <button
                onClick={() => { clearMessages(); setShowMobileSidebar(false); }}
                className="w-full py-3 px-4 rounded-xl bg-[var(--text-primary)] text-[var(--background)] font-medium text-sm flex items-center justify-center gap-2 btn-press mb-6"
              >
                <Plus size={16} strokeWidth={1.5} />
                New Chat
              </button>

              {/* Chat History Placeholder */}
              <div className="flex-1 overflow-y-auto">
                <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider mb-3 px-2">
                  Recent Chats
                </p>
                <p className="text-sm text-[var(--text-secondary)] px-2">
                  Chat history will appear here
                </p>
              </div>

              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="w-full p-3 rounded-xl hover:bg-[var(--surface-highlight)] transition-colors flex items-center gap-3 mt-4 border-t border-[var(--border)] pt-4"
              >
                <span className="text-[var(--text-secondary)]">
                  {theme === 'light' ? 'Dark' : 'Light'} Mode
                </span>
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop Header */}
      <header className="hidden md:flex h-16 px-6 items-center justify-between border-b border-[var(--border)] bg-[var(--surface)]">
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
      <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6 pb-40 md:pb-48">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState onSuggestionClick={(msg) => handleSend(msg, 'detailed')} />
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

      {/* Input */}
      <ChatInput onSend={handleSend} isLoading={isLoading} />
    </div>
  );
}

function EmptyState({ onSuggestionClick }: { onSuggestionClick: (msg: string) => void }) {
  const suggestions = [
    'What are the common drug interactions with Warfarin?',
    'Explain the mechanism of action of SSRIs',
    'Help me write a research manuscript introduction',
    'Generate a lab protocol for drug extraction',
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="text-center py-12 md:py-16"
    >
      <div className="w-14 h-14 md:w-16 md:h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
        <Sparkles size={24} strokeWidth={1.5} className="text-white" />
      </div>
      <h2 className="text-xl md:text-2xl font-semibold text-[var(--text-primary)] mb-3">
        How can I help you today?
      </h2>
      <p className="text-[var(--text-secondary)] mb-8 max-w-md mx-auto text-sm md:text-base">
        Ask about drug interactions, research writing, or upload documents for analysis.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto px-4">
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
