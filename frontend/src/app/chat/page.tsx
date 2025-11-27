'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Trash2, Menu, Edit3, ChevronDown, Sparkles } from 'lucide-react';
import { openMobileNav } from '@/components/chat/MobileNav';
import ChatMessage from '@/components/chat/ChatMessage';
import ChatInput, { Mode } from '@/components/chat/ChatInput';
import DeepResearchUI from '@/components/chat/DeepResearchUI';
import { useChatContext } from '@/contexts/ChatContext';
import { useSidebar } from '@/contexts/SidebarContext';

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get('q');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, isUploading, isDeleting, sendMessage, uploadFiles, deepResearchProgress, deleteConversation, clearMessages, conversationId, selectConversation } = useChatContext();
  const { sidebarOpen } = useSidebar();
  const [hasInitialized, setHasInitialized] = useState(false);
  const [mode, setMode] = useState<Mode>('fast'); // Lifted mode state

  // Restore conversation from localStorage on mount
  useEffect(() => {
    const savedConversationId = localStorage.getItem('currentConversationId');
    if (savedConversationId && !conversationId && !initialQuery) {
      selectConversation(savedConversationId);
    }
  }, []);

  // Save current conversation ID to localStorage
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem('currentConversationId', conversationId);
    }
  }, [conversationId]);

  useEffect(() => {
    if (initialQuery && !hasInitialized) {
      sendMessage(initialQuery, 'fast'); // Default to fast mode
      setHasInitialized(true);
    }
  }, [initialQuery, hasInitialized, sendMessage]);

  const handleNewChat = () => {
    localStorage.removeItem('currentConversationId');
    clearMessages();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (message: string, selectedMode: Mode) => {
    sendMessage(message, selectedMode);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-[var(--background)]">
      {/* Mobile Header - ChatGPT Style with Glassmorphism */}
      <header className="md:hidden sticky top-0 z-30 h-16 px-4 flex items-center justify-between bg-[var(--background)]/80 backdrop-blur-md border-b border-[var(--border)]/10">
        {/* Left: Hamburger Menu */}
        <button
          onClick={() => openMobileNav()}
          className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors"
        >
          <Menu size={20} strokeWidth={1.5} className="text-[var(--text-primary)]" />
        </button>

        {/* Center: Model Selector (Simplified) */}
        <div className="flex items-center gap-1.5">
          <span className="text-base font-medium text-[var(--text-primary)]">PharmGPT</span>
        </div>

        {/* Right: New Chat */}
        <button
          onClick={handleNewChat}
          className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-[var(--surface-highlight)] transition-colors"
          title="New chat"
        >
          <Edit3 size={20} strokeWidth={1.5} className="text-[var(--text-primary)]" />
        </button>
      </header>

      {/* Desktop Header with Glassmorphism */}
      <header className={`hidden md:flex h-[72px] px-6 items-center justify-between border-b border-[var(--border)]/10 bg-[var(--background)]/80 backdrop-blur-md transition-all duration-300 ${!sidebarOpen ? 'pl-16' : ''}`}>
        <div className="flex items-center gap-3 h-full">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={16} strokeWidth={1.5} className="text-white" />
          </div>
          <div>
            <h1 className="font-serif font-medium text-[var(--text-primary)]">PharmGPT</h1>
            <p className="text-xs text-[var(--text-secondary)]">AI Research Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-3 h-full">
          {/* Delete Conversation Button */}
          {conversationId && messages.length > 0 && (
            <button
              onClick={deleteConversation}
              disabled={isDeleting}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20 transition-colors disabled:opacity-50"
              title="Delete conversation"
            >
              {isDeleting ? (
                <Loader2 size={12} strokeWidth={1.5} className="animate-spin" />
              ) : (
                <Trash2 size={12} strokeWidth={1.5} />
              )}
              Delete
            </button>
          )}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${isLoading
              ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
              : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
            }`}>
            {isLoading ? (
              <>
                <Loader2 size={12} strokeWidth={1.5} className="animate-spin" />
                Thinking...
              </>
            ) : (
              <>
                <CheckCircle2 size={12} strokeWidth={1.5} />
                Ready
              </>
            )}
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-4 md:px-6 py-3 sm:py-4 pb-32 sm:pb-36 md:pb-44">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState
              onSuggestionClick={(msg) => handleSend(msg, mode)}
              currentMode={mode}
            />
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((msg, index) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChatMessage
                    message={msg}
                    isStreaming={isLoading && index === messages.length - 1 && msg.role === 'assistant'}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {/* Deep Research Progress */}
          {deepResearchProgress && (
            <div className="mb-4">
              <DeepResearchUI
                state={{
                  status: deepResearchProgress.message || deepResearchProgress.status || 'Processing...',
                  progress: deepResearchProgress.progress || 0,
                  logs: deepResearchProgress.plan_overview
                    ? [`Strategy: ${deepResearchProgress.plan_overview}`]
                    : [],
                  sources: deepResearchProgress.citations?.map(c => ({
                    title: c.title,
                    url: c.url,
                    source: c.source,
                    authors: c.authors,
                    year: c.year,
                    journal: c.journal,
                    doi: c.doi
                  })) || [],
                  isComplete: deepResearchProgress.type === 'complete',
                  planOverview: deepResearchProgress.plan_overview,
                  steps: deepResearchProgress.steps,
                  report: deepResearchProgress.report
                }}
              />
            </div>
          )}

          {/* Loading indicator - minimal, no avatar */}
          {isLoading && !deepResearchProgress && (messages.length === 0 || messages[messages.length - 1]?.role !== 'assistant') && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="py-4"
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-bounce" style={{ animationDelay: '300ms' }} />
                <span className="text-xs text-[var(--text-secondary)] ml-2">Thinking...</span>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onFileUpload={uploadFiles}
        isLoading={isLoading}
        isUploading={isUploading}
        mode={mode}
        setMode={setMode}
      />
    </div>
  );
}

function EmptyState({ onSuggestionClick, currentMode }: { onSuggestionClick: (msg: string) => void, currentMode: Mode }) {
  const suggestions = [
    'What are the common drug interactions with Warfarin?',
    'Explain the mechanism of action of SSRIs',
    'Help me write a research manuscript introduction',
    'Deep research: Current evidence for pembrolizumab in NSCLC',
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center py-12 md:py-16"
    >
      <div className="w-14 h-14 md:w-16 md:h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
        <Sparkles size={24} strokeWidth={1.5} className="text-white" />
      </div>
      <h2 className="text-xl md:text-2xl font-serif font-medium text-[var(--text-primary)] mb-3">
        How can I help you today?
      </h2>
      <p className="text-[var(--text-secondary)] mb-8 max-w-md mx-auto text-sm md:text-base">
        Ask about drug interactions, research writing, or upload documents for analysis.
        <br />
        <span className="text-xs opacity-70 mt-2 block">Current Mode: {currentMode === 'deep_research' ? 'Deep Research' : currentMode === 'detailed' ? 'Detailed' : 'Fast'}</span>
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 max-w-xl mx-auto px-2 sm:px-4">
        {suggestions.map((suggestion, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i, duration: 0.3 }}
            onClick={() => onSuggestionClick(suggestion)}
            className="p-3 sm:p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-left text-xs sm:text-sm text-[var(--text-primary)] hover:border-[var(--accent)] hover:bg-[var(--surface-highlight)] transition-all"
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
        <Loader2 size={32} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
