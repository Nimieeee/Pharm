'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Trash2, Menu, Edit3, ChevronDown, Sparkles, MoreHorizontal } from 'lucide-react';
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
  const { sidebarOpen, setSidebarOpen } = useSidebar();
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

  // Reset mode when conversation changes
  useEffect(() => {
    setMode('fast');
  }, [conversationId]);

  const handleSend = (message: string, selectedMode: Mode = mode) => {
    if (selectedMode !== mode) {
      setMode(selectedMode);
    }
    sendMessage(message, selectedMode);
  };

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-[var(--background)]">
      {/* Floating Header Controls - 3-Column Grid for Mobile */}
      <div className="fixed top-0 left-0 right-0 h-16 z-40 pointer-events-none px-4">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center h-full gap-2">
          {/* Left Column: Sidebar Trigger */}
          <div className="flex items-center justify-start pointer-events-auto">
            <button
              onClick={() => setSidebarOpen(true)}
              className={`p-2.5 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--background)]/50 hover:text-[var(--text-primary)] transition-all backdrop-blur-sm ${sidebarOpen ? 'hidden md:hidden' : 'flex'}`}
            >
              <Menu size={24} strokeWidth={1.5} />
            </button>
          </div>

          {/* Center Column: PharmGPT Pill */}
          <div className="flex items-center justify-center pointer-events-none">
            <div
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/40 dark:bg-black/40 backdrop-blur-md border border-white/10 shadow-lg select-none whitespace-nowrap transition-all duration-300"
              style={{
                marginLeft: sidebarOpen ? '140px' : '0',
              }}
            >
              <span className="text-xs font-medium text-[var(--text-primary)] tracking-tight">PharmGPT</span>
              <span className="text-[10px] text-[var(--text-secondary)] opacity-70">v2.0</span>
            </div>
          </div>

          {/* Right Column: New Chat (Mobile Only) */}
          <div className="flex items-center justify-end pointer-events-auto md:hidden">
            <button
              onClick={handleNewChat}
              className="p-2.5 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--background)]/50 hover:text-[var(--text-primary)] transition-all backdrop-blur-sm"
            >
              <Edit3 size={24} strokeWidth={1.5} />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-2 sm:px-4 md:px-6 pt-24 pb-32 sm:pb-36 md:pb-44">
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

function EmptyState({ onSuggestionClick, currentMode }: { onSuggestionClick: (msg: string, mode?: Mode) => void, currentMode: Mode }) {
  const suggestions = [
    { text: 'What are the common drug interactions with Warfarin?', mode: 'detailed' as Mode },
    { text: 'Explain the mechanism of action of SSRIs', mode: 'detailed' as Mode },
    { text: 'Help me write a research manuscript introduction', mode: 'detailed' as Mode },
    { text: 'Deep research: Current evidence for pembrolizumab in NSCLC', mode: 'deep_research' as Mode },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="text-center py-12 md:py-16"
    >
      <div className="mb-8 relative flex justify-center">
        <img
          src="/PharmGPT.png"
          alt="PharmGPT"
          className="w-[120px] opacity-[0.05] dark:opacity-[0.08] pointer-events-none select-none grayscale"
        />
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
            onClick={() => onSuggestionClick(suggestion.text, suggestion.mode)}
            className="p-3 sm:p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] text-left text-xs sm:text-sm text-[var(--text-primary)] hover:border-[var(--accent)] hover:bg-[var(--surface-highlight)] transition-all"
          >
            {suggestion.text}
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
